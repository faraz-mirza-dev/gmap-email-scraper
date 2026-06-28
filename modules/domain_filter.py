import re

REJECTED_EXTENSIONS = {'.edu', '.gov', '.mil', '.in', '.co.in'}

REJECTED_KEYWORDS = {
    'hospital',
    'medical center',
    'health system',
    'healthcare network',
    'university',
    'college',
    'school',
    'directory',
    'listing',
    'yelp',
    'yellowpages',
    'careers',
    'indeed',
    'zocdoc',
    'healthgrades',
    'webmd',
    'vitals'
}

def is_rejected_domain(domain: str, business_name: str = "") -> tuple[bool, str]:
    """
    Checks if a domain should be rejected based on rules.
    Returns (is_rejected, reason).
    """
    if not domain:
        return True, "Empty domain"

    domain_lower = domain.lower()
    name_lower = business_name.lower() if business_name else ""

    # 1. Check extensions
    for ext in REJECTED_EXTENSIONS:
        if domain_lower.endswith(ext):
            return True, f"Rejected extension: {ext}"

    # 2. Check keywords in domain or business name
    for keyword in REJECTED_KEYWORDS:
        if keyword in domain_lower:
            return True, f"Rejected keyword in domain: {keyword}"
        if name_lower and keyword in name_lower:
            # Be careful with partial matches in name, use regex for word boundaries
            if re.search(rf'\b{re.escape(keyword)}\b', name_lower):
                return True, f"Rejected keyword in name: {keyword}"

    return False, ""
