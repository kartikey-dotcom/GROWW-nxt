# System Architecture: Mutual Fund FAQ Assistant (Facts-Only Q&A)

This document outlines the architecture for the Retrieval-Augmented Generation (RAG)-based Mutual Fund FAQ Assistant. The system is designed to provide objective, verifiable, and compliance-compliant answers to mutual fund queries using a curated corpus of official Groww URLs.

---

## 1. System Overview

The system consists of four primary components:
1. **Ingestion & Indexing Pipeline**: A time-based **scheduler** periodically triggers the ingestion workflow to scrape/crawl the Groww URLs, extract clean text, split it into semantic chunks, and update the Vector database.
2. **Retrieval Pipeline**: Computes query embeddings, performs vector similarity search, and retrieves the most relevant document chunks.
3. **Generation & Guardrail Pipeline**: Constructs a constrained system prompt, sends it to the LLM (e.g., Gemini / OpenAI), and validates that the response adheres to compliance rules (sentence limits, single source link, refusal criteria).
4. **User Interface**: A clean, minimalist chat interface (e.g., Streamlit) presenting the disclaimer, sample questions, and Q&A history.

---

## 2. Architecture Diagram

```mermaid
graph TD
    Z[Scheduler / Cron Job] -->|Triggers Ingestion| A
    %% Ingestion Stage
    subgraph Ingestion Pipeline [1. Ingestion & Indexing]
        A[Groww URLs] -->|Web Scraper / Parser| B[Clean Text Extractor]
        B -->|Recursive Text Splitter| C[Semantic Chunks]
        C -->|Embedding Model| D[Vector Store / Index]
    end

    %% Query & Retrieval Stage
    subgraph Retrieval Pipeline [2. Query & Retrieval]
        E[User Query] -->|Embedding Model| F[Query Vector]
        F -->|Cosine Similarity Search| D
        D -->|Top-K Retrieve| G[Relevant Context Chunks]
    end

    %% Generation & Guardrails Stage
    subgraph Generation & Guardrail Pipeline [3. Generation & Compliance]
        G --> H[Prompt Builder]
        E --> H
        H -->|System Prompt + Context| I[LLM Engine]
        I -->|Raw Response| J[Guardrail & Compliance Validator]
        J -->|Check 1: Max 3 Sentences| K[Verification]
        J -->|Check 2: Single Source Link| K
        J -->|Check 3: Refusal Check| K
    end

    %% Frontend Stage
    subgraph User Interface [4. Presentation Layer]
        L[Web UI / Chat Interface] <-->|Q&A Stream| K
        L -->|Includes Disclaimer + Sample Qs| M[User Screen]
    end

    style Ingestion Pipeline fill:#f9f,stroke:#333,stroke-width:2px
    style Retrieval Pipeline fill:#bbf,stroke:#333,stroke-width:2px
    style Generation & Guardrail Pipeline fill:#dfd,stroke:#333,stroke-width:2px
    style User Interface fill:#fdd,stroke:#333,stroke-width:2px
```

---

## 3. Component Details

### A. Ingestion & Indexing Pipeline
*   **Scheduler**: A time-based scheduler (e.g., daily/weekly cron job) that automatically triggers the web scraping and indexing workflow to keep the database context current.
*   **Web Scraper**: Downloads content from the 5 specified Groww URLs. Filters out standard boilerplate elements (header, footer, sidebars, cookie banners).
*   **Text Splitter**: Splits document content into chunks of ~500–1000 characters with an overlap of 100–200 characters to keep context intact. Every chunk retains metadata tracking its original source URL.
*   **Embedding Model**: Converts text chunks into high-dimensional vectors (e.g., `text-embedding-3-small` or HuggingFace embeddings).
*   **Vector Database**: Stores the vectors and corresponding metadata (e.g., Chroma, FAISS, or a simple in-memory dictionary-based index since the dataset is very small).

### B. Retrieval Pipeline
*   **Query Embedding**: Converts the user's input query using the same embedding model.
*   **Vector Matcher**: Performs cosine similarity search between the query vector and index vectors.
*   **Metadata Injector**: Retrieves the top-K matches (e.g., K=3) and aggregates both the text content and their source URLs.

### C. Generation & Guardrail Pipeline
*   **Prompt Engineering**: Combines the retrieved context, source URLs, and query into a strictly-guided system prompt.
    > [!IMPORTANT]
    > **System Prompt Guidelines:**
    > - Act strictly as a factual mutual fund FAQ assistant.
    > - Do NOT express opinions, return predictions, or provide investment advice.
    > - Answer only using the provided context. If the answer is not in the context, politely refuse.
    > - Constrain length to 3 sentences max.
    > - Output exactly one source URL as a markdown hyperlink.
*   **Refusal Engine**: Specifically triggers a predefined refusal template with an educational resource link (e.g., AMFI or SEBI) if:
    1. The query contains subjective/advisory keywords (e.g., "should I invest", "better", "buy", "sell", "recommend").
    2. The retrieved context does not contain the answer.
*   **Compliance Guardrails (Post-Processing)**:
    - **Sentence Counter**: Counts punctuation to ensure responses are within 1 to 3 sentences.
    - **Link Extractor**: Ensures exactly one source URL exists in the response and validates it against the source URL list.
    - **Fallback Handler**: Re-prompts the LLM or falls back to a template if compliance checks fail.

### D. User Interface (Streamlit-based)
*   **Chat Box**: Standard conversational interface.
*   **Disclaimers**: A persistent, clear disclaimer: `Disclaimer: Facts-only. No investment advice.`
*   **Sample Questions**: Fast-click questions like:
    1. *"What is the exit load of HDFC Small Cap Fund?"*
    2. *"Who manages the Groww Nifty India Defence ETF FoF?"*
    3. *"Should I invest in HDFC Mid-Cap Fund?"* (Tests the refusal handling)

---

## 4. Technology Stack (Recommended)

| Layer | Component | Technology / Library |
| :--- | :--- | :--- |
| **Frontend** | Chat UI & App Hosting | Streamlit / Python |
| **Orchestration** | RAG Logic Flow | LangChain / LlamaIndex (or vanilla python for lightweight build) |
| **Vector Index** | Semantic Vector Search | FAISS / ChromaDB (or simple local NumPy index) |
| **Embedding** | Text Representation | OpenAI Embeddings / HuggingFace `all-MiniLM-L6-v2` |
| **LLM** | Factual Generation | Gemini 1.5 Flash / OpenAI GPT-4o-mini |
| **Scraping** | Document Parsing | BeautifulSoup4 / Playwright |

---

## 5. Security & Privacy Safeguards
*   **PII Filtering**: A pre-processing regex check scans queries for sensitive numbers (e.g., PAN, Aadhaar, bank accounts, emails, OTP patterns) and blocks the prompt if any matches are found.
*   **State Isolation**: User sessions are completely stateless; queries are evaluated independently with no persistent storage of conversations on the server database.
