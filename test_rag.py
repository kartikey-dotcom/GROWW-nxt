import re
from datetime import datetime
from rag_engine import generate_response, check_pii, is_advisory

def test_pii_check():
    print("Running test_pii_check...")
    assert "Aadhaar" in check_pii("My Aadhaar is 1234-5678-9012")
    assert "PAN" in check_pii("Here is my PAN: ABCDE1234F")
    assert "Email" in check_pii("contact me at test@example.com")
    assert "Phone" in check_pii("My phone number is 9876543210")
    assert len(check_pii("What is the exit load?")) == 0
    print("test_pii_check PASSED")

def test_advisory_check():
    print("Running test_advisory_check...")
    assert is_advisory("Should I invest in HDFC Small Cap?")
    assert is_advisory("Which fund is better: HDFC Mid Cap or Large Cap?")
    assert is_advisory("Can you recommend a fund to buy?")
    assert not is_advisory("What is the exit load of HDFC Small Cap Fund?")
    assert not is_advisory("Who is the fund manager?")
    print("test_advisory_check PASSED")

def test_pii_response_refusal():
    print("Running test_pii_response_refusal...")
    response = generate_response("My Aadhaar is 1234-5678-9012. Tell me about HDFC Small Cap.")
    assert "Refusal: For privacy and security reasons" in response
    print("test_pii_response_refusal PASSED")

def test_advisory_response_refusal():
    print("Running test_advisory_response_refusal...")
    response = generate_response("Should I invest in HDFC Mid Cap?")
    assert "do not provide investment advice" in response
    assert "AMFI" in response or "SEBI" in response
    assert "Last updated from sources:" in response
    print("test_advisory_response_refusal PASSED")

def test_factual_query_constraints():
    print("Running test_factual_query_constraints...")
    response = generate_response("What is the exit load of HDFC Small Cap Fund?")
    
    # 1. Check sentence limit (<= 3 sentences)
    clean_text = re.sub(r'Last updated from sources:.*', '', response, flags=re.IGNORECASE).strip()
    sentences = re.split(r'(?<=[.!?])\s+', clean_text)
    sentences = [s for s in sentences if s.strip()]
    assert len(sentences) <= 3, f"Response has too many sentences: {len(sentences)}"
    
    # 2. Check exactly one citation link
    links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', response)
    assert len(links) == 1, f"Response must contain exactly one citation link, found: {len(links)}"
    
    # 3. Check footer is present
    assert "Last updated from sources:" in response
    print("test_factual_query_constraints PASSED")

def test_nav_query():
    print("Running test_nav_query...")
    response = generate_response("What is the current nav of HDFC Mid Cap Fund?")
    assert "current NAV" in response or "nav" in response.lower()
    links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', response)
    assert len(links) == 1
    assert "hdfc-mid-cap" in links[0][1]
    print("test_nav_query PASSED")

def test_scheduler_delay():
    print("Running test_scheduler_delay...")
    from scheduler import get_seconds_until_10am_ist, IST
    from datetime import datetime
    
    # Case 1: Before 10 AM IST (e.g. 8:00 AM IST)
    t1 = datetime(2026, 6, 8, 8, 0, 0, tzinfo=IST)
    delay1 = get_seconds_until_10am_ist(t1)
    assert delay1 == 2 * 3600, f"Expected 7200 seconds, got {delay1}"
    
    # Case 2: Exactly 10:00:00 AM IST -> should target next day
    t2 = datetime(2026, 6, 8, 10, 0, 0, tzinfo=IST)
    delay2 = get_seconds_until_10am_ist(t2)
    assert delay2 == 24 * 3600, f"Expected 86400 seconds, got {delay2}"
    
    # Case 3: After 10 AM IST (e.g. 11:30 AM IST) -> should target next day at 10 AM
    t3 = datetime(2026, 6, 8, 11, 30, 0, tzinfo=IST)
    delay3 = get_seconds_until_10am_ist(t3)
    # Time to midnight (12.5 hours) + 10 hours = 22.5 hours
    assert delay3 == 22.5 * 3600, f"Expected 81000 seconds, got {delay3}"
    print("test_scheduler_delay PASSED")

if __name__ == "__main__":
    print("=========================================")
    print("STARTING UNIT TESTS FOR RAG COMPLIANCE...")
    print("=========================================")
    try:
        test_pii_check()
        test_advisory_check()
        test_pii_response_refusal()
        test_advisory_response_refusal()
        test_factual_query_constraints()
        test_nav_query()
        test_scheduler_delay()
        print("=========================================")
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=========================================")
    except AssertionError as e:
        print("\n!!! TEST FAILED !!!")
        print(e)
        import sys
        sys.exit(1)
