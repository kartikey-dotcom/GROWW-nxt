import os
import json
import re
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INPUT_CHUNKS_FILE = os.path.join(DATA_DIR, "chunks.json")
INDEX_FILE = os.path.join(DATA_DIR, "vector_store.json")

def rebuild_index():
    """
    Reads chunks.json (generating it if missing), computes dense vector embeddings
    using BGE-small, computes word frequencies for TF-IDF fallback, and saves the
    completed database index to vector_store.json.
    """
    # Always run the chunker process to ensure chunks are refreshed from the latest scraped data
    print("Refreshing chunks from scraped data to ensure freshness...")
    try:
        from chunker import chunk_scraped_data
        chunk_scraped_data()
    except Exception as e:
        print(f"Error triggering chunking process: {e}")
        
    if not os.path.exists(INPUT_CHUNKS_FILE):
        print(f"Error: Chunks file {INPUT_CHUNKS_FILE} does not exist.")
        return False
        
    print(f"Loading chunks from {INPUT_CHUNKS_FILE}...")
    with open(INPUT_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    print(f"Total chunks loaded: {len(chunks)}")
    
    # Initialize the lightweight BGE-small model
    print("Loading BGE-small embedding model ('BAAI/bge-small-en-v1.5')...")
    try:
        model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        return False
        
    # Extract text content for embedding
    texts = [chunk["text"] for chunk in chunks]
    
    print("Generating dense vector embeddings...")
    try:
        embeddings = model.encode(texts, normalize_embeddings=True)
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return False
        
    indexed_chunks = []
    for i, chunk in enumerate(chunks):
        # Convert embedding numpy array to a standard list for JSON serialization
        emb_list = embeddings[i].tolist()
        
        # Compute basic word frequencies for TF-IDF keyword search fallback
        words = re.findall(r'\w+', chunk["text"].lower())
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
            
        indexed_chunks.append({
            "id": chunk["id"],
            "text": chunk["text"],
            "source_url": chunk["source_url"],
            "document_title": chunk["document_title"],
            "embedding": emb_list,
            "word_freq": word_freq
        })
        
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(indexed_chunks, f, ensure_ascii=False, indent=2)
        
    print(f"Vector store successfully saved to {INDEX_FILE}")
    return True

if __name__ == "__main__":
    rebuild_index()

