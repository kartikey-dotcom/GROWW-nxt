# Mutual Fund FAQ Assistant - Verification Walkthrough

This document summarizes the implementation and verification results for the facts-only Retrieval-Augmented Generation (RAG) assistant for Groww mutual fund schemes.

---

## 🚀 Accomplished Tasks

We successfully built the ten-phase implementation plan:
- **Phase 0 (Project Scaffold & Dependencies)**: Configured project scaffolding, environments, and libraries.
- **Phase 1 (Ingestion & Scraping)**: Built [scraper.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/scraper.py) to fetch and parse Groww mutual fund URLs.
- **Phase 2 (Embeddings & Vector Store)**: Developed [indexer.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/indexer.py) to compute embeddings and maintain local vector files.
- **Phase 3 (Scheme-aware Retrieval)**: Implemented [retriever.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/retriever.py) with scheme routing/filtering.
- **Phase 4 (RAG Orchestration)**: Built the core query orchestrator in [rag_engine.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/rag_engine.py).
- **Phase 5 (Guardrails)**: Integrated PII filtering, advisory refusal checks, and validation layers.
- **Phase 6 (Chat UI)**: Created [app.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/app.py) as a premium facts-only user dashboard.
- **Phase 7 (Daily Scheduler)**: Embedded [scheduler.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/scheduler.py) for daily automatic index syncs.
- **Phase 8 (Automated Tests)**: Set up the [test_rag.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/test_rag.py) suite to automate verification of compliance rules.
- **Phase 9 (Deployment & README)**: Finalized deployment guides and system runbooks.

---

## 📺 UI Verification & Visual Flow

Below is the recording of the automated browser subagent interacting with the Streamlit app:

![Browser demo video/animation](C:\Users\DELL\.gemini\antigravity-ide\brain\2b24725f-9437-4e93-bc1d-f988c85106f4\rag_chat_demo_1780613218901.webp)

Here are the step-by-step screenshots captured during manual and browser verification:

````carousel
![1. Streamlit App Loading Page](C:\Users\DELL\.gemini\antigravity-ide\brain\2b24725f-9437-4e93-bc1d-f988c85106f4\streamlit_main_loaded_1780613285639.png)
<!-- slide -->
![2. First Preset Query Response](C:\Users\DELL\.gemini\antigravity-ide\brain\2b24725f-9437-4e93-bc1d-f988c85106f4\after_first_query_1780613324527.png)
<!-- slide -->
![3. Custom Query and Expense Ratio Output](C:\Users\DELL\.gemini\antigravity-ide\brain\2b24725f-9437-4e93-bc1d-f988c85106f4\final_response_1780613400211.png)
````

---

## 🧪 Automated Unit Test Results

We ran the automated test suite in [test_rag.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/test_rag.py) which tests compliance on PII checks, advisory check regexes, factual constraints, sentence-length limiters, and single-source citation requirements.

### Test Log Output:
```
C:\Users\DELL\Downloads\GROWW NXTLP\rag_engine.py:5: FutureWarning: 
All support for the `google.generativeai` package has ended. It will no longer be receiving 
updates or bug fixes. Please switch to the `google.genai` package as soon as possible.
  import google.generativeai as genai
=========================================
STARTING UNIT TESTS FOR RAG COMPLIANCE...
=========================================
Running test_pii_check...
test_pii_check PASSED
Running test_advisory_check...
test_advisory_check PASSED
Running test_pii_response_refusal...
test_pii_response_refusal PASSED
Running test_advisory_response_refusal...
test_advisory_response_refusal PASSED
Running test_factual_query_constraints...
Performing vector similarity search...
LLM failed or API key has no quota. Falling back to exact regex/rule-based extraction...
test_factual_query_constraints PASSED
Running test_nav_query...
Performing vector similarity search...
LLM failed or API key has no quota. Falling back to exact regex/rule-based extraction...
test_nav_query PASSED
=========================================
ALL TESTS PASSED SUCCESSFULLY!
=========================================
```

---

## 🔒 Verification Details & RAG Engine Highlights

1. **Facts-Only Fallback**: Since the LLM API key did not have active free-tier quota (resulting in 429 errors), the RAG engine successfully utilized the rule-based extraction fallback. It directly isolated exact numbers (such as NAV and Expense Ratios) from the retrieved vector chunks, formatting them correctly.
2. **PII Censorship**: Correctly identifies Aadhaar, PAN, Emails, Phone Numbers, and OTPs. Refuses to process the query, reminding the user about security.
3. **Advisory Block**: Queries containing words indicating recommendations/comparisons (like "Should I invest", "Which is better", "recommend", "suggest") are intercepted and redirected to AMFI/SEBI educational resource pages.
4. **Length and Citation Constraints**: Output lengths are constrained to ≤ 3 sentences and append exactly one hyperlink pointing directly to the source page on Groww.
