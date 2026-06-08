import os
import json

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INPUT_FILE = os.path.join(DATA_DIR, "scraped_data.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "chunks.json")

def split_content_to_chunks(document):
    """
    Split the content of a document into logical sections (by double newlines),
    preserving the Scheme/ETF Name and source URL context in each chunk.
    This guarantees that every chunk contains the identity of the fund.
    """
    content = document.get("content", "")
    url = document.get("url", "")
    title = document.get("title", "")
    
    if not content:
        return []
        
    lines = content.split("\n")
    
    # Extract Scheme/ETF Name (first header line starting with #)
    scheme_header = ""
    for line in lines:
        if line.startswith("#"):
            scheme_header = line
            break
            
    if not scheme_header:
        # Fallback if no markdown title exists
        scheme_header = f"# Scheme Name: {title}"
        
    header_prefix = f"{scheme_header}\nURL: {url}\n\n"
    
    # Remove the top headers (# Scheme Name and URL) to avoid duplicating them in the section split
    filtered_lines = []
    for line in lines:
        if line.startswith("#"):
            continue
        if line.startswith("URL:"):
            continue
        filtered_lines.append(line)
        
    remaining_text = "\n".join(filtered_lines).strip()
    
    # Split the remaining text by double newlines into logical sections
    sections = remaining_text.split("\n\n")
    
    last_updated = document.get("last_updated", "")
    
    chunks = []
    for idx, section in enumerate(sections):
        section_text = section.strip()
        if not section_text:
            continue
            
        # Prepend the scheme context header
        chunk_text = header_prefix + section_text
        
        chunks.append({
            "id": f"{url.split('/')[-1]}_chunk_{idx}",
            "text": chunk_text,
            "source_url": url,
            "document_title": title,
            "last_updated": last_updated
        })
    return chunks

def chunk_scraped_data():
    """
    Reads the scraped raw data, splits it into semantic chunks, and writes chunks to chunks.json.
    """
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found at {INPUT_FILE}. Please run scraper.py first.")
        return None
        
    print(f"Reading scraped data from {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        docs = json.load(f)
        
    all_chunks = []
    for doc in docs:
        if "error" in doc:
            print(f"Skipping document with scrape error: {doc['url']}")
            continue
        doc_chunks = split_content_to_chunks(doc)
        all_chunks.extend(doc_chunks)
        print(f"Generated {len(doc_chunks)} chunks for {doc.get('url')}")
        
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        
    print(f"Chunking process completed. Saved {len(all_chunks)} chunks to {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    chunk_scraped_data()
