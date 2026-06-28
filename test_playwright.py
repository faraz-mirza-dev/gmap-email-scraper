import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://www.google.com/maps/search/Plastic+Surgeon+in+Atlanta?hl=en", wait_until="domcontentloaded")
        
        try:
            consent_btn = await page.query_selector('button:has-text("Accept all")')
            if consent_btn:
                await consent_btn.click()
        except:
            pass
            
        print("Waiting for places...")
        try:
            await page.wait_for_selector('a.hfpxzc', timeout=10000)
            links = await page.query_selector_all('a.hfpxzc')
            print(f"Found {len(links)} places")
            
            for link in links[:20]:
                name = await link.get_attribute('aria-label')
                url_before = page.url
                
                # JS click is 100% reliable and doesn't care about floating headers
                await link.evaluate('elem => elem.click()')
                
                # Wait for URL to change to the place details
                try:
                    await page.wait_for_function('old_url => document.location.href !== old_url', arg=url_before, timeout=5000)
                except Exception as e:
                    print(f"Name: {name} -> FAILED TO OPEN DETAILS (Timeout)")
                    continue
                
                # Wait a bit for the details panel to render
                await page.wait_for_timeout(1000)
                
                # Extract website
                website_url = await page.evaluate('''() => {
                    let links = Array.from(document.querySelectorAll('a[data-item-id="authority"]'));
                    let link = links.find(l => l.offsetParent !== null);
                    if (link) return link.href;
                    
                    let altLinks = Array.from(document.querySelectorAll('a[aria-label^="Website:"], a[aria-label="Open website"]'));
                    let altLink = altLinks.reverse().find(l => l.offsetParent !== null);
                    if (altLink) return altLink.href;
                    
                    return null;
                }''')
                
                print(f"Name: {name} -> Website: {website_url}")
                
        except Exception as e:
            print(f"Error: {e}")
            print(await page.content())
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
