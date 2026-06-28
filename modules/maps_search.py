import asyncio
import urllib.parse
from typing import List, Dict, Any
from playwright.async_api import async_playwright
import time
from .utils import normalize_url

_browser = None
_playwright = None
_browser_lock = asyncio.Lock()
# Limit concurrent Maps searches to prevent memory exhaustion and laptop heating
# User has i9 and 200mbps 5GHz WiFi 6, so 5 browsers is a good high-performance balance.
_maps_semaphore = asyncio.Semaphore(5)

async def get_browser():
    global _playwright, _browser
    async with _browser_lock:
        if _browser is None or not _browser.is_connected():
            try:
                if _playwright is None:
                    _playwright = await async_playwright().start()
                _browser = await _playwright.chromium.launch(headless=True)
            except Exception:
                # Fallback if playwright instance itself is broken
                _playwright = await async_playwright().start()
                _browser = await _playwright.chromium.launch(headless=True)
    return _browser

class MapsSearch:
    def __init__(self, config: dict):
        self.config = config
        self.timeout = config.get('timeout_seconds', 30)

    async def search(self, keyword: str, city: str, session: Any):
        """
        Searches Google Maps using Playwright with clicking & scrolling logic.
        Limited by a semaphore to prevent crashing the laptop.
        """
        async with _maps_semaphore:
            async for business in self._search_google_maps(keyword, city):
                yield business

    async def _search_google_maps(self, keyword: str, city: str):
        query = f"{keyword} in {city}"
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/maps/search/{encoded_query}?hl=en"
        
        browser = await get_browser()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        # CPU/Network Optimization: Abort loading images, media, and fonts to cool down the laptop
        await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf}", lambda route: route.abort())
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Check for consent screen
            try:
                consent_btn = await page.query_selector('button:has-text("Accept all")')
                if consent_btn:
                    await consent_btn.click()
            except Exception:
                pass

            # Wait for feed
            try:
                await page.wait_for_selector('a.hfpxzc', timeout=20000)
                print("Found feed selector 'a.hfpxzc'")
            except Exception as e:
                # No results or timeout
                print(f"Timeout waiting for 'a.hfpxzc': {e}")
                return
                
            # Scroll to load more results
            feed_selector = 'div[role="feed"]'
            feed = await page.query_selector(feed_selector)
            if feed:
                prev_height = 0
                no_change_count = 0
                while True:  # Endless scroll until the very bottom
                    await page.evaluate('(elem) => elem.scrollBy(0, 10000)', feed)
                    await page.wait_for_timeout(1500)
                    curr_height = await page.evaluate('(elem) => elem.scrollHeight', feed)
                    if curr_height == prev_height:
                        no_change_count += 1
                        if no_change_count >= 2:
                            break
                    else:
                        no_change_count = 0
                    prev_height = curr_height

            place_links = await page.query_selector_all('a.hfpxzc')
            
            for place_link in place_links:
                try:
                    place_name = await place_link.get_attribute('aria-label') or "Unknown"
                    if not place_name or place_name == "Unknown":
                        continue
                        
                    # Get the current H1 text so we can wait for it to change
                    old_h1 = await page.evaluate('''() => {
                        let h1 = document.querySelector('h1.DUwDvf');
                        return h1 ? h1.innerText : "";
                    }''')
                    
                    url_before = page.url
                    
                    # JS click is 100% reliable and doesn't care about floating headers
                    await place_link.evaluate('elem => elem.click()')
                    
                    # Wait for URL to change to the place details
                    try:
                        await page.wait_for_function('old_url => document.location.href !== old_url', arg=url_before, timeout=5000)
                    except Exception:
                        continue
                        
                    # BULLETPROOF FIX: Wait for the H1 text to CHANGE from the previous one.
                    # This ensures the React/Angular DOM has actually updated and we don't read the old panel.
                    try:
                        await page.wait_for_function(
                            '''([old_text]) => {
                                let h1 = document.querySelector('h1.DUwDvf');
                                return h1 && h1.innerText !== old_text;
                            }''',
                            arg=[old_h1],
                            timeout=5000
                        )
                    except Exception:
                        # If it didn't change (or it's an exact duplicate name), skip it
                        continue
                    
                    # Extract website using JS to ensure we get the visible one in the details pane
                    website_url = await page.evaluate('''() => {
                        let links = Array.from(document.querySelectorAll('a[data-item-id="authority"]'));
                        let link = links.find(l => l.offsetParent !== null);
                        if (link) return link.href;
                        
                        let altLinks = Array.from(document.querySelectorAll('a[aria-label^="Website:"], a[aria-label="Open website"]'));
                        let altLink = altLinks.reverse().find(l => l.offsetParent !== null);
                        if (altLink) return altLink.href;
                        
                        return null;
                    }''')
                        
                    if website_url and 'google.com' not in website_url:
                        yield {
                            "name": place_name,
                            "website": normalize_url(website_url),
                            "address": "",  # Can be extracted but not heavily needed right now
                            "phone": ""
                        }
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error searching Google Maps for {query}: {e}")
        finally:
            try:
                await context.close()
            except Exception:
                pass
