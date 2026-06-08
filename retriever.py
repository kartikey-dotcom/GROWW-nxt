import os
import json
import re
import math
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INDEX_FILE = os.path.join(DATA_DIR, "vector_store.json")

# Globally cached embedding model
_model = None

def get_embedding_model():
    """
    Loads and caches the SentenceTransformer model to avoid multiple initializations.
    """
    global _model
    if _model is None:
        print("Loading BGE-small query model for semantic retrieval...")
        _model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    return _model

def cosine_similarity(v1, v2):
    """
    Computes cosine similarity between two vectors.
    """
    if not v1 or not v2:
        return 0.0
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = math.sqrt(sum(x * x for x in v1))
    norm_v2 = math.sqrt(sum(x * x for x in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def get_query_embedding(query):
    """
    Generates embedding for a query using BGE-small.
    """
    try:
        model = get_embedding_model()
        embedding = model.encode(query, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        print(f"Error embedding query: {e}")
        return None

def get_matching_scheme(query):
    """
    Layer 1: Identifies if the query targets a specific scheme and returns its slug.
    If matched, retrieval will pre-filter to only chunks of this scheme.
    """
    q = query.lower()
    if any(kw in q for kw in ["mid cap", "midcap", "hdfc mid"]):
        return "hdfc-mid-cap-fund-direct-growth"
    elif any(kw in q for kw in ["small cap", "smallcap", "hdfc small"]):
        return "hdfc-small-cap-fund-direct-growth"
    elif any(kw in q for kw in ["silver", "etf"]) and "hdfc" in q:
        return "hdfc-silver-etf"
    elif any(kw in q for kw in ["defence", "defense", "groww nifty"]):
        return "groww-nifty-india-defence-etf-fof-direct-growth"
    elif any(kw in q for kw in ["large cap", "largecap", "hdfc large", "top 100", "top100"]):
        return "hdfc-large-cap-fund-direct-growth"
    return None

def get_section_boost(query, chunk_id):
    """
    Layer 2: Applies a relevance boost (1.5x) to chunks based on keyword matching
    of specific investor intent (Holdings vs Returns vs Core Details).
    """
    q = query.lower()
    
    is_core = "_chunk_0" in chunk_id
    is_holdings = "_chunk_1" in chunk_id
    is_returns = "_chunk_2" in chunk_id
    
    # Portfolio/Holdings intent
    if any(kw in q for kw in ["holding", "portfolio", "stock", "share", "invested", "company", "companies"]):
        if is_holdings:
            return 1.5
            
    # Yield/Returns intent
    if any(kw in q for kw in ["return", "performance", "yield", "history", "historical", "growth"]):
        if is_returns:
            return 1.5
            
    # Core Details (exit load, expense ratio, NAV, AUM, manager) intent
    if any(kw in q for kw in ["exit load", "expense", "ratio", "manager", "nav", "aum", "size", "benchmark", "sip", "lumpsum", "stamp", "launch"]):
        if is_core:
            return 1.5
            
    return 1.0

def compute_idf(chunks):
    """
    Computes IDF values for all words across the corpus of chunks.
    """
    N = len(chunks)
    doc_freqs = {}
    for chunk in chunks:
        for word in chunk.get("word_freq", {}).keys():
            doc_freqs[word] = doc_freqs.get(word, 0) + 1
            
    idf = {}
    for word, freq in doc_freqs.items():
        idf[word] = math.log((N + 1) / (freq + 0.5)) + 1
    return idf

def keyword_search(query, chunks, top_k=3):
    """
    Performs a TF-IDF bag-of-words search fallback when vector embeddings are unavailable.
    Applies the same pre-filtering and section boosting rules.
    """
    query_words = re.findall(r'\w+', query.lower())
    if not query_words:
        return []
        
    idf = compute_idf(chunks)
    scores = []
    
    for chunk in chunks:
        score = 0.0
        word_freq = chunk.get("word_freq", {})
        
        # Calculate matching score using TF-IDF
        for word in query_words:
            if word in word_freq:
                tf = word_freq[word]
                word_idf = idf.get(word, 1.0)
                score += tf * word_idf
                
        # Normalize score slightly by chunk length
        length = sum(word_freq.values())
        if length > 0:
            norm_factor = math.sqrt(length)
            score = score / norm_factor
            
        # Apply section boost
        boost = get_section_boost(query, chunk["id"])
        score = score * boost
        
        if score > 0:
            scores.append((chunk, score))
            
    # Sort descending by TF-IDF score
    scores.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in scores[:top_k]]

def retrieve_context(query, top_k=3):
    """
    Retrieves the top_k relevant context chunks for a query.
    Tries BGE vector search first, falls back to TF-IDF keyword search.
    """
    if not os.path.exists(INDEX_FILE):
        print(f"Index file {INDEX_FILE} not found. Returning empty context.")
        return []
        
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    if not chunks:
        return []
        
    # Layer 1: Scheme-Aware Pre-Filtering
    target_scheme = get_matching_scheme(query)
    if target_scheme:
        print(f"Routing query strictly to scheme: {target_scheme}")
        candidates = [c for c in chunks if target_scheme in c.get("source_url", "")]
        if not candidates:
            # Fallback to all if filtering yielded nothing
            candidates = chunks
    else:
        print("No specific scheme detected in query. Searching all candidates.")
        candidates = chunks
        
    # Check if vector search is possible (chunks contain embeddings)
    can_vector_search = candidates[0].get("embedding") is not None
    
    if can_vector_search:
        query_vector = get_query_embedding(query)
        if query_vector:
            scores = []
            for chunk in candidates:
                sim = cosine_similarity(query_vector, chunk["embedding"])
                
                # Layer 2: Section Boosting
                boost = get_section_boost(query, chunk["id"])
                final_score = sim * boost
                scores.append((chunk, final_score))
            
            # Sort by boosted cosine similarity descending
            scores.sort(key=lambda x: x[1], reverse=True)
            return [item[0] for item in scores[:top_k]]
        else:
            print("Vector generation failed. Falling back to keyword search...")
    else:
        print("Vector embeddings unavailable. Performing keyword search fallback...")
        
    return keyword_search(query, candidates, top_k=top_k)

if __name__ == "__main__":
    # Test queries to verify routing and boosting logic
    test_queries = [
        "What is the exit load of HDFC Small Cap Fund?",
        "Who is the manager of HDFC Mid Cap Fund?",
        "Groww Nifty India Defence ETF FoF holdings",
        "What are the historical returns for HDFC Large Cap?"
    ]
    
    for q in test_queries:
        print(f"\n=========================================\nQuery: {q}")
        results = retrieve_context(q, top_k=2)
        for i, res in enumerate(results):
            print(f"Result {i+1} from {res['document_title']} ({res['id']}):")
            print(res["text"][:300] + "...")

