import re
from datetime import datetime

# Predefined educational links for refusals
AMFI_URL = "https://www.amfiindia.com"
SEBI_URL = "https://www.sebi.gov.in"

# Regex patterns for PII checks
PII_PATTERNS = {
    "Aadhaar": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "Phone": r"\b(?:\+91\s?)?[6-9]\d{9}\b",
    "OTP": r"\b\d{4,6}\b"
}

def check_pii(text):
    """
    Checks if the user text contains any personally identifiable information (PII).
    Returns list of matched PII types.
    """
    matched_pii = []
    for pii_type, pattern in PII_PATTERNS.items():
        if pii_type == "OTP":
            if "otp" in text.lower() and re.search(pattern, text):
                matched_pii.append(pii_type)
        else:
            if re.search(pattern, text):
                matched_pii.append(pii_type)
    return matched_pii

def is_advisory(text):
    """
    Detects if the user query is asking for subjective investment advice, opinions, or recommendations.
    """
    advisory_keywords = [
        r"\bshould\s+i\s+invest\b",
        r"\bwhich\s+(?:\w+\s+){0,3}better\b",
        r"\bbetter\s+than\b",
        r"\bbuy\s+or\s+sell\b",
        r"\brecommend\b",
        r"\bsuggest\b",
        r"\bopinion\b",
        r"\bis\s+this\s+fund\s+good\b",
        r"\bperformance\s+comparison\b"
    ]
    
    text_lower = text.lower()
    for kw in advisory_keywords:
        if re.search(kw, text_lower):
            return True
    return False

def clean_and_truncate_sentences(text, max_sentences=3):
    """
    Splits text into sentences and truncates to max_sentences.
    Uses regex that ignores common abbreviations (like Rs., Co., Ltd.) to avoid false sentence cuts.
    """
    # Split using punctuation delimiter not preceded by common abbreviations
    sentence_ends = r'(?<!\bRs)(?<!\bCo)(?<!\bLtd)(?<!\b[A-Z])(?<=[.!?])\s+'
    sentences = re.split(sentence_ends, text.strip())
    sentences = [s for s in sentences if s.strip()]
    if len(sentences) > max_sentences:
        return " ".join(sentences[:max_sentences])
    return " ".join(sentences)

def extract_hyperlinks(text):
    """
    Finds all markdown links in the text.
    """
    return re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', text)

def enforce_guardrails(response_text, source_url, source_title, fetch_date):
    """
    Enforces compliance constraints post-generation:
    1. Maximum of 3 sentences.
    2. Exactly one source hyperlink.
    3. Proper footer showing the last updated date.
    """
    # Remove any existing last-updated footers to avoid duplication
    response_text = re.sub(r'Last updated from sources:.*', '', response_text, flags=re.IGNORECASE).strip()
    
    links = extract_hyperlinks(response_text)
    
    if not links:
        citation_link = f" [{source_title}]({source_url})"
        response_text = clean_and_truncate_sentences(response_text, max_sentences=3)
        if response_text.endswith('.'):
            response_text = response_text[:-1] + citation_link + "."
        else:
            response_text = response_text + citation_link + "."
    else:
        # If there are multiple links, we keep only the first occurrence and remove formatting from the rest
        if len(links) > 1:
            first_link = links[0]
            first_occurrence = True
            for display, href in links:
                if first_occurrence:
                    first_occurrence = False
                    continue
                response_text = response_text.replace(f"[{display}]({href})", display)
        
        response_text = clean_and_truncate_sentences(response_text, max_sentences=3)
        
    footer = f"\n\n*Last updated from sources: {fetch_date}*"
    return response_text + footer

def get_advisory_refusal():
    """
    Generates educational refusal responses for investment advice/opinion queries.
    """
    refusal_msg = (
        "I am a facts-only assistant and do not provide investment advice, opinions, or recommendations. "
        "Please refer to official resources like the Association of Mutual Funds in India (AMFI) or the "
        f"Securities and Exchange Board of India (SEBI) for educational guidance. "
        f"[AMFI website]({AMFI_URL})"
    )
    return refusal_msg

def get_out_of_scope_refusal(url=None):
    """
    Generates polite refusal responses when information isn't found in context.
    """
    target_url = url if url else SEBI_URL
    refusal_msg = (
        "I am a facts-only assistant and could not find the answer to your query in the official sources. "
        f"Please check the [official documentation]({target_url}) directly for complete details."
    )
    return refusal_msg
