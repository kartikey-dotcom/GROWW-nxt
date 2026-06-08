# Mutual Fund FAQ Assistant Implementation Plan (Revised)

This document outlines the revised phase-wise implementation plan for building the facts-only Retrieval-Augmented Generation (RAG) assistant for mutual fund schemes using Groww data. The phases have been restructured to match the 10-phase pipeline (Phase 0 to Phase 9) requested.

---

## Goal Description

Build a lightweight RAG chatbot that answers facts-only questions regarding 5 specific mutual fund/ETF schemes on Groww. It periodically updates its corpus via a scheduler, restricts replies strictly to 1–3 sentences, includes exactly one source link, refusal-handles non-factual/advisory queries, and features a clean, disclaimer-supported chat UI.

---

## User Review Required

> [!IMPORTANT]
> **Key Architectural and Library Selections:**
> 1. **Framework & API Layer**: We will implement a REST API backend with a `POST /api/chat` endpoint using **FastAPI** or **Flask** in **Phase 4** to decouple the RAG orchestrator from the frontend UI.
> 2. **Scheme-Aware Retrieval & Section Boosting**: In **Phase 3**, we will build a custom retrieval layer that filters candidates by mutual fund scheme identity (extracted from the query/metadata) and boosts specific sections (e.g., exit load, expense ratio) based on query keywords.
> 3. **Validation & PII Guard**: In **Phase 5**, query inputs and LLM outputs will pass through regex-based and heuristic validation layers to sanitize PII, intercept advisory queries, and verify compliance constraints (<= 3 sentences, 1 citation URL).

---

## Proposed Changes (Phases 0 - 9)

We will build and refine the codebase inside [GROWW NXTLP](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP).

### Phase 0: Project Scaffold, `corpus.yaml`, Dependencies
Initialize the project environment, configure external library dependencies, and establish a central source configuration file.

#### [NEW] [corpus.yaml](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/corpus.yaml)
*   Define the 5 seed mutual fund/ETF Groww URLs and metadata attributes:
    *   `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth`
    *   `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth`
    *   `https://groww.in/etfs/hdfc-silver-etf`
    *   `https://groww.in/mutual-funds/groww-nifty-india-defence-etf-fof-direct-growth`
    *   `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth`

#### [MODIFY] [requirements.txt](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/requirements.txt)
*   Include dependencies: `fastapi`, `uvicorn`, `pyyaml`, `streamlit`, `beautifulsoup4`, `requests`, `numpy`, `pytest`, `google-genai`.

---

### Phase 1: Fetch, Parse, Chunk 5 Groww URLs
Develop scraper modules to acquire pages, clean document boilerplates (navigation bars, footers, script files), extract Next.js `__NEXT_DATA__` state, and recursively chunk the remaining text.

#### [MODIFY] [scraper.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/scraper.py)
*   Read targets from `corpus.yaml` dynamically.
*   Scrape HTML and extract structured details from Next.js state data blocks.

#### [NEW] [chunker.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/chunker.py)
*   Implement a scheme-aware section-based chunker that divides documents by logical double newlines (\n\n) and prepends the scheme name and source URL context to each chunk to preserve semantic integrity.

---

### Phase 2: Embeddings, Vector Store, Metadata Index
Compute semantic vectors for document chunks and build a locally queryable vector store.

#### [MODIFY] [indexer.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/indexer.py)
*   Use the lightweight, CPU-efficient `BAAI/bge-small-en-v1.5` sentence-transformer model to represent chunks as dense 384-dimensional vectors.
*   Save the vectors directly in a transparent, human-readable local JSON database (`vector_store.json`) alongside metadata indexing (source URL, scheme title, last updated timestamp) and precomputed word frequencies for TF-IDF fallback.


---

### Phase 3: Scheme-Aware Retrieval with Section Boosting
Enhance retrieval accuracy by mapping queries to scheme metadata and applying relevance weight adjustments.

#### [MODIFY] [retriever.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/retriever.py)
*   **Layer 1 (Scheme-Aware Pre-Filtering)**: Parse queries to detect target mutual funds/ETFs, restricting retrieval strictly to the matched scheme chunks to eliminate cross-fund hallucinations.
*   **Layer 2 (Section Boosting)**: Boost candidate retrieval scores (1.5x multiplier) based on keyword intent (e.g., holdings keywords boost Chunk 1, returns keywords boost Chunk 2, exit load/NAV/managers keywords boost Chunk 0).
*   **Layer 3 (Hybrid Retriever)**: Implement cosine similarity search using the local `BGE-small` model, with a robust TF-IDF fallback matcher using precomputed `word_freq` tables.

---

### Phase 4: RAG Orchestrator + POST `/api/chat`
Create the orchestrator connecting retrieval and generation, exposing it via a structured API endpoint.

#### [MODIFY] [rag_engine.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/rag_engine.py)
*   Coordinate query parsing, context retrieval, system prompt formatting, and LLM invocation using the modern Google AI Studio SDK (`google-genai`) with `gemini-2.5-flash`.
*   Include fallback heuristics to extract answers from the retrieved text if API key quota limits or network errors occur.

#### [NEW] [api.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/api.py)
*   Develop a FastAPI server hosting a `POST /api/chat` endpoint returning JSON payloads containing the generated response, citation link, and model metadata.


---

### Phase 5: Classifier, Refusals, Validator, Formatter, PII Guard
Build the guardrail and compliance framework to ensure response safety and format compliance.

#### [NEW] [guardrails.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/guardrails.py)
*   **PII Guard**: Screen input queries for sensitive personal details (PAN, Aadhaar, email, phone) using regular expressions and block matching prompts.
*   **Classifier**: Differentiate factual queries from advisory/opinion-seeking queries.
*   **Refusal Handler**: Provide polite rejection answers with educational links (AMFI/SEBI) for advisory queries.
*   **Validator**: Check output length (<= 3 sentences) and the presence of exactly one source URL.
*   **Formatter**: Add the required footer `Last updated from sources: <date>` and style markdown links.

---

### Phase 6: Minimal Chat UI with Disclaimer and Example Questions
Build the chat user interface connected to the `/api/chat` backend.

#### [MODIFY] [app.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/app.py)
*   Create a Streamlit/HTML interface exhibiting a persistent, visible disclaimer: `Facts-only. No investment advice.`
*   Provide quick-action click buttons for factual queries, advisory questions (testing refusal), and PII questions.

---

### Phase 7: Daily Scheduler for Automated Ingestion (Timezone-Aware IST)
Automate daily indexing tasks to sync vector data and scheme information at exactly 10:00 AM IST daily.

#### [MODIFY] [scheduler.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/scheduler.py)
*   Calculate timezone-aware daily timing delay targeting exactly 10:00 AM IST (India Standard Time / UTC+5:30) regardless of the host system's configuration.
*   Log scheduling events using explicit, timezone-labeled IST timestamps.
*   Keep the background thread daemonized and support test interval mock overrides.

#### [MODIFY] [indexer.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/indexer.py)
*   Update index rebuilding sequence to always refresh source data chunking beforehand, preventing indexing stale content when scheduler runs scraper changes.

---

### Phase 8: Automated Tests + Manual Evaluation Matrix
Establish regression tests and a benchmark evaluation dataset to qualify response precision.

#### [MODIFY] [test_rag.py](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/test_rag.py)
*   Define unit and integration tests covering PII checks, classification, length validation, and citation counts.

#### [NEW] [evaluation_matrix.md](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/Docs/evaluation_matrix.md)
*   Document test queries representing factual, advisory, and out-of-scope requests to systematically track system behavior.

---

### Phase 9: README, Runbooks, Deployment
Produce deployment instructions and operational references.

#### [NEW] [README.md](file:///c:/Users/DELL/Downloads/GROWW%20NXTLP/README.md)
*   Provide execution instructions, architectural schemas, configuration steps, and runbooks handling common maintenance workflows.

---

## Verification Plan

### Automated Tests
Run standard automated checks to certify API responses and guardrails:
*   `pytest test_rag.py` or `python test_rag.py`

### Manual Verification
*   Launch the API backend via `uvicorn api:app --reload` and check the `/api/chat` route with `curl` or Postman.
*   Launch the frontend via `streamlit run app.py` and interact with the user interface to verify the disclaimer, click-to-query samples, and chat outputs.
