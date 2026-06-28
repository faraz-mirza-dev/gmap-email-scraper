import asyncio
import aiodns
from typing import Optional

class MXValidator:
    def __init__(self):
        self.resolver = aiodns.DNSResolver(loop=asyncio.get_event_loop())
        # Simple cache to avoid querying the same domain repeatedly
        self.cache = {}
        
    async def is_valid_mx(self, domain: str) -> bool:
        """
        Checks if a domain has valid MX records.
        """
        domain = domain.lower().strip()
        if not domain:
            return False
            
        if domain in self.cache:
            return self.cache[domain]
            
        try:
            # Query MX records
            result = await self.resolver.query(domain, 'MX')
            is_valid = len(result) > 0
            self.cache[domain] = is_valid
            return is_valid
        except (aiodns.error.DNSError, Exception):
            # If MX fails, fallback to A record as per some SMTP RFCs
            try:
                result = await self.resolver.query(domain, 'A')
                is_valid = len(result) > 0
                self.cache[domain] = is_valid
                return is_valid
            except Exception:
                self.cache[domain] = False
                return False
