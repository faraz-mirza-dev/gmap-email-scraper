import tldextract
from urllib.parse import urlparse, urljoin
import random

def get_base_domain(url: str) -> str:
    """Extracts the base domain (e.g., example.com) from a URL."""
    try:
        extracted = tldextract.extract(url)
        if extracted.domain and extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}".lower()
    except Exception:
        pass
    
    # Fallback if tldextract fails
    try:
        parsed = urlparse(url)
        if parsed.netloc:
            parts = parsed.netloc.split('.')
            if len(parts) >= 2:
                return '.'.join(parts[-2:]).lower()
    except Exception:
        pass
    return ""

def normalize_url(url: str, base_url: str = None) -> str:
    """Normalizes a URL, joining it with a base URL if it's relative."""
    if not url:
        return ""
    
    try:
        if base_url:
            url = urljoin(base_url, url)
            
        parsed = urlparse(url)
        
        # Ensure it has a scheme
        if not parsed.scheme:
            url = f"https://{url}"
            parsed = urlparse(url)
            
        # Basic normalization: remove fragments
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
            
        return normalized
    except Exception:
        return url

def get_random_user_agent(config: dict) -> str:
    """Returns a random user agent from config."""
    agents = config.get('user_agents', [])
    if agents:
        return random.choice(agents)
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

def clean_text(text: str) -> str:
    """Cleans extracted text by removing extra whitespace."""
    if not text:
        return ""
    return " ".join(text.split())
