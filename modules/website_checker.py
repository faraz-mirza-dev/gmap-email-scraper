import asyncio
import aiohttp
from selectolax.parser import HTMLParser
import re
from .utils import get_random_user_agent

class WebsiteChecker:
    def __init__(self, config: dict):
        self.config = config
        self.timeout = aiohttp.ClientTimeout(total=config.get('timeout_seconds', 15))
        
    async def check_relevance(self, url: str, target_keyword: str, session: aiohttp.ClientSession) -> tuple[bool, float, str]:
        """
        Downloads homepage and checks for relevance against target keyword.
        Returns (is_relevant, score, html_content).
        """
        headers = {
            "User-Agent": get_random_user_agent(self.config),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        try:
            async with session.get(url, headers=headers, timeout=self.timeout, ssl=False, allow_redirects=True) as response:
                if response.status != 200:
                    return False, 0.0, ""
                    
                html = await response.text(errors='ignore')
                
                # Check relevance
                score = self._calculate_relevance(html, target_keyword)
                threshold = self.config.get('relevance_threshold', 1)
                
                return score >= threshold, score, html
                
        except Exception as e:
            return False, 0.0, ""

    def _calculate_relevance(self, html: str, keyword: str) -> float:
        """
        Simple text matching to calculate relevance score.
        Checks for exact keyword, partial words.
        """
        try:
            tree = HTMLParser(html)
            text = tree.body.text() if tree.body else html
            text_lower = text.lower()
            keyword_lower = keyword.lower()
            
            score = 0.0
            
            # 1. Exact match
            if keyword_lower in text_lower:
                score += 2.0
                
            # 2. Word matches
            words = keyword_lower.split()
            for word in words:
                # ignore very short words
                if len(word) > 2 and word in text_lower:
                    score += 0.5
                    
            return score
        except Exception:
            return 0.0
