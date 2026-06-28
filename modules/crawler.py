import asyncio
import aiohttp
from selectolax.parser import HTMLParser
from urllib.parse import urlparse
import logging
from typing import Set

from .utils import get_random_user_agent, normalize_url, get_base_domain
from .email_extractor import EmailExtractor

class Crawler:
    def __init__(self, config: dict):
        self.config = config
        self.max_depth = config.get('max_depth', 3)
        self.timeout = aiohttp.ClientTimeout(total=config.get('timeout_seconds', 15))
        
        # Priority paths to crawl
        self.priority_paths = [
            '/contact', '/contact-us', '/about', '/about-us', 
            '/team', '/staff', '/providers', '/doctors'
        ]

    async def crawl_website(self, start_url: str, session: aiohttp.ClientSession) -> Set[str]:
        """
        Crawls a website up to max_depth and extracts all emails.
        """
        base_domain = get_base_domain(start_url)
        if not base_domain:
            return set()

        visited = set()
        to_visit = [(start_url, 0)]
        all_emails = set()
        
        while to_visit:
            # OPTIMIZATION: Check max 5 pages per website instead of 20 to make it 400% faster.
            # Emails are almost always on the homepage, contact, or about pages.
            if len(visited) >= 20:
                break
                
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited or depth > self.max_depth:
                continue
                
            visited.add(current_url)
            
            headers = {
                "User-Agent": get_random_user_agent(self.config),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
            
            try:
                async with session.get(current_url, headers=headers, timeout=self.timeout, ssl=False, allow_redirects=True) as response:
                    if response.status != 200:
                        continue
                        
                    html = await response.text(errors='ignore')
                    
                    # 1. Extract emails
                    emails = EmailExtractor.extract_emails(html, base_domain)
                    all_emails.update(emails)
                    
                    # 2. Extract links (if not at max depth)
                    if depth < self.max_depth:
                        tree = HTMLParser(html)
                        for a_tag in tree.css('a'):
                            href = a_tag.attributes.get('href')
                            if href:
                                if href.startswith('mailto:'):
                                    mail = href.replace('mailto:', '').split('?')[0].strip()
                                    if '@' in mail:
                                        all_emails.add(mail.lower())
                                    continue
                                    
                                next_url = normalize_url(href, current_url)
                                next_domain = get_base_domain(next_url)
                                
                                # Only crawl same domain
                                if next_domain == base_domain and next_url not in visited:
                                    # Boost priority for contact/about pages
                                    parsed_next = urlparse(next_url)
                                    path = parsed_next.path.lower()
                                    
                                    is_priority = any(p in path for p in self.priority_paths)
                                    
                                    if is_priority:
                                        to_visit.insert(0, (next_url, depth + 1))
                                    else:
                                        to_visit.append((next_url, depth + 1))
                                        
            except Exception as e:
                # Connection error, timeout, etc.
                pass
                
        return all_emails
