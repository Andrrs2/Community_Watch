import re

UNVERIFIED_KEYWORDS = [
    r"\brumor\b",
    r"\bunconfirmed\b",
    r"\bnot verified\b",
    r"\bforwarded as received\b",
    r"\bheard that\b",
    r"\bmaybe\b"
]

CONFIRMED_KEYWORDS = [
    r"\bconfirmed\b",
    r"\blegal observer\b",
    r"\bverified\b",
    r"\brapid response confirmed\b"
]

def evaluate_incident(description: str, default_verified: bool = False) -> bool:
    """
    Returns True if the incident meets verification standards.
    Drops explicit rumor/unconfirmed keywords immediately.
    """
    text = description.lower()
    
    # 1. Immediate rejection on unverified markers
    for pattern in UNVERIFIED_KEYWORDS:
        if re.search(pattern, text):
            return False
            
    # 2. Accept if source already flagged verified or text contains explicit confirmation
    if default_verified:
        return True
        
    for pattern in CONFIRMED_KEYWORDS:
        if re.search(pattern, text):
            return True
            
    return False