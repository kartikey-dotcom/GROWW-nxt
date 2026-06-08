import os
import re
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from retriever import retrieve_context
from guardrails import (
    check_pii,
    is_advisory,
    enforce_guardrails,
    get_advisory_refusal,
    get_out_of_scope_refusal,
    AMFI_URL,
    SEBI_URL
)

load_dotenv()

# Setup Gemini API client using the modern GenAI SDK
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None
    
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

def rule_based_fallback(query, context_chunks):
    """
    Factual extraction fallback when the LLM service/API key is unavailable.
    """
    best_chunk = context_chunks[0]
    text = best_chunk["text"]
    raw_lines = text.split("\n")
    
    # Exclude metadata headers to avoid false positives (e.g. title having the word 'NAV')
    lines = [l for l in raw_lines if not l.startswith("Document:") and not l.startswith("URL:")]
    
    query_lower = query.lower()
    
    # 1. Exit Load
    if "exit" in query_lower or "load" in query_lower:
        for line in lines:
            if "exit load" in line.lower():
                return f"For this scheme, the {line.strip().replace('- ', '').replace('Exit Load: ', 'exit load is ')}."
                
    # 2. Expense Ratio
    if "expense" in query_lower or "ratio" in query_lower:
        for line in lines:
            if "expense ratio" in line.lower():
                return f"The {line.strip().replace('- ', '').replace('Expense Ratio: ', 'expense ratio is ')} for this fund."
                
    # 3. Manager
    if "manager" in query_lower:
        for line in lines:
            if "manager" in line.lower():
                mgrs = line.strip().replace('- ', '').replace('Fund Managers:', '').strip()
                return f"The scheme is managed by {mgrs}."
                
    # 4. NAV
    if "nav" in query_lower or "price" in query_lower:
        for line in lines:
            if "nav" in line.lower() or "current nav" in line.lower():
                return f"The {line.strip().replace('- ', '').replace('Current NAV: ', 'current NAV is ')}."
                
    # 5. AUM / Size
    if "aum" in query_lower or "size" in query_lower or "asset" in query_lower:
        for line in lines:
            if "aum" in line.lower() or "fund size" in line.lower():
                aum_val = line.strip().replace('- ', '').replace('AUM (Fund Size): ', '').strip()
                return f"The AUM (Assets Under Management) for this fund is {aum_val}."
                
    # 6. Benchmark
    if "benchmark" in query_lower:
        for line in lines:
            if "benchmark" in line.lower():
                bench = line.strip().replace('- ', '').replace('Benchmark Index: ', '').strip()
                return f"The fund tracks the benchmark index {bench}."

    # 7. Holdings
    if "holding" in query_lower:
        holdings_lines = []
        capture = False
        for line in lines:
            if "holdings" in line.lower():
                capture = True
                continue
            if capture and line.startswith("- "):
                holdings_lines.append(line.strip().replace("- ", ""))
                if len(holdings_lines) >= 3:
                    break
        if holdings_lines:
            return f"The top holdings for this fund include: {', '.join(holdings_lines)}."
            
    # Default fallback: return description
    for line in lines:
        if "description:" in line.lower():
            desc = line.replace("Description:", "").strip()
            return desc
            
    return f"The requested details can be verified in the scheme document."

def query_llm(system_prompt, user_query):
    """
    Invokes the Gemini LLM with system instructions.
    """
    if not client:
        return "Error: GEMINI_API_KEY environment variable is not set."
        
    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"LLM Invocation Error: {e}")
        return f"Error: LLM invocation failed ({str(e)})"

def generate_response(query):
    """
    Main orchestrator for Mutual Fund FAQ chatbot.
    Handles PII pre-check, advisory check, RAG retrieval, LLM call, and compliance post-guardrails.
    """
    # 1. PII Security Check
    matched_pii = check_pii(query)
    if matched_pii:
        return (
            "Refusal: For privacy and security reasons, please do not share personal information "
            f"(like {', '.join(matched_pii)}). I can only answer objective, facts-only questions "
            "about mutual fund schemes."
        )
        
    # 2. Advisory Pre-check
    if is_advisory(query):
        refusal_msg = get_advisory_refusal()
        footer = f"\n\n*Last updated from sources: {datetime.now().strftime('%Y-%m-%d')}*"
        return refusal_msg + footer
        
    # 3. Retrieve Context
    context_chunks = retrieve_context(query, top_k=2)
    if not context_chunks:
        refusal_msg = get_out_of_scope_refusal(SEBI_URL)
        footer = f"\n\n*Last updated from sources: {datetime.now().strftime('%Y-%m-%d')}*"
        return refusal_msg + footer
        
    # Get the best matched source metadata
    best_chunk = context_chunks[0]
    source_url = best_chunk["source_url"]
    source_title = best_chunk["document_title"]
    fetch_date = best_chunk.get("last_updated", datetime.now().strftime("%Y-%m-%d")).split(" ")[0]
    
    # 4. Attempt LLM generation
    context_text = "\n\n".join([chunk["text"] for chunk in context_chunks])
    
    system_instruction = f"""You are a facts-only Mutual Fund FAQ Assistant.
Your goal is to answer the user's query using ONLY the provided Context below.

Context:
{context_text}

Rules:
1. Answer the query factually, objectively, and concisely.
2. Limit your answer to a MAXIMUM of 3 sentences.
3. Do NOT express opinions, return predictions, or provide investment advice.
4. You MUST include exactly one citation link in your answer. Use the source URL from the context in markdown format, e.g. [{source_title}]({source_url}).
5. If the context does not contain the answer, politely decline to answer, explaining that the information is not available in the official source. Do not make up facts.
"""
    
    raw_response = query_llm(system_instruction, query)
    
    # If LLM failed or API key returned 429 quota error, use the rule-based extraction fallback!
    if raw_response.startswith("Error"):
        print("LLM failed or API key has no quota. Falling back to exact regex/rule-based extraction...")
        fallback_text = rule_based_fallback(query, context_chunks)
        final_response = enforce_guardrails(fallback_text, source_url, source_title, fetch_date)
    else:
        # Check if LLM refused
        if "not available in the context" in raw_response.lower() or "cannot answer" in raw_response.lower():
            refusal_msg = get_out_of_scope_refusal(source_url)
            final_response = enforce_guardrails(refusal_msg, source_url, source_title, fetch_date)
        else:
            final_response = enforce_guardrails(raw_response, source_url, source_title, fetch_date)
            
    return final_response

if __name__ == "__main__":
    test_inputs = [
        "What is the exit load of HDFC Small Cap Fund?",
        "Who is the manager of HDFC Mid Cap Fund?",
        "Should I invest in HDFC Large Cap Fund?",
        "My Aadhaar is 1234-5678-9012, tell me my tax details",
        "What is the current nav of groww nifty india defence etf?"
    ]
    
    for user_in in test_inputs:
        print(f"\nUser: {user_in}")
        bot_out = generate_response(user_in)
        try:
            print(f"Bot: {bot_out}")
        except UnicodeEncodeError:
            # Fallback for systems/consoles without UTF-8 active
            print(f"Bot: {bot_out.encode('ascii', 'replace').decode('ascii')}")

