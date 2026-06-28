import re
from typing import List, Dict, Set, Tuple

FREE_EMAIL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
    'live.com', 'aol.com', 'icloud.com', 'proton.me', 'protonmail.com'
}

IGNORED_EMAILS = {
    'noreply', 'no-reply', 'do-not-reply', 'donotreply',
    'test', 'example', 'fake', 'demo', 'sentry', 'wix',
    'support@wix.com'
}

IGNORED_DOMAINS = {
    'sentry.io', 'wixpress.com', 'sentry-next.wixpress.com', 'sentry.wixpress.com', 'wix.com',
    'adobe.com', 'yahoogroups.com', 'email.com', 'wordpress.com', 'wordpress.org', 
    'squarespace.com', 'weebly.com', 'shopify.com', 'godaddy.com', 'automattic.com'
}

PLACEHOLDER_DOMAINS = {
    'domain.com', 'example.com', 'mysite.com', 'yoursite.com', 'email.com'
}

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

class EmailExtractor:
    @staticmethod
    def extract_emails(html_text: str, base_domain: str = None) -> Set[str]:
        """Extracts emails from HTML text."""
        if not html_text:
            return set()
            
        # Basic extraction
        emails = EMAIL_REGEX.findall(html_text)
        
        cleaned = set()
        for e in emails:
            e = e.lower().strip()
            # Filter ignored extensions
            if e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js', '.webp', '.avif')):
                continue
                
            parts = e.split('@')
            if len(parts) != 2: continue
            local_part, domain_part = parts
            
            # Replace placeholder domains with actual base domain
            if base_domain and domain_part in PLACEHOLDER_DOMAINS:
                e = f"{local_part}@{base_domain}"
                domain_part = base_domain
            
            # Filter ignored exact emails and prefixes
            if local_part in IGNORED_EMAILS or e in IGNORED_EMAILS:
                continue
                
            # Filter ignored domains
            if domain_part in IGNORED_DOMAINS or domain_part.endswith('.wixpress.com'):
                continue
                
            # Filter single character local parts (e.g. i@domain.com, x@domain.com) unless it's a known valid exception (very rare)
            if len(local_part) <= 1:
                continue
                
            # Filter long random hex strings (Sentry/Wix error logs)
            # A 32-character hex string is typically an MD5 hash
            if len(local_part) >= 20 and re.fullmatch(r'[0-9a-f]+', local_part):
                continue
                
            cleaned.add(e)
            
        # Deduplicate: if an email is just a prefixed version of another email in the set
        # (e.g. u003econtact@domain.com and contact@domain.com), keep the shorter one.
        final_cleaned = set()
        for e1 in cleaned:
            is_junk_version = False
            for e2 in cleaned:
                if e1 != e2 and e1.endswith(e2):
                    is_junk_version = True
                    break
            if not is_junk_version:
                final_cleaned.add(e1)
            
        return final_cleaned

    @staticmethod
    def rank_emails(emails: Set[str]) -> Tuple[Optional[str], List[str]]:
        """
        Ranks emails based on priority:
        1 = info@, 2 = contact@, 3 = hello@, 4 = sales@, 5 = admin@, 6 = support@
        """
        if not emails:
            return None, []
            
        email_list = list(emails)
        
        priority_map = {
            'info@': 1,
            'contact@': 2,
            'hello@': 3,
            'sales@': 4,
            'admin@': 5,
            'support@': 6
        }
        
        def get_rank(email: str) -> int:
            for prefix, rank in priority_map.items():
                if email.startswith(prefix):
                    return rank
            return 7 # Default for personal/owner emails
            
        ranked_emails = sorted(email_list, key=get_rank)
        return ranked_emails[0], ranked_emails

    @staticmethod
    def is_free_email(email: str) -> bool:
        """Checks if the email is from a free provider."""
        try:
            domain = email.split('@')[1]
            return domain in FREE_EMAIL_DOMAINS
        except IndexError:
            return False
