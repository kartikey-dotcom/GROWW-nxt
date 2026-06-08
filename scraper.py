import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

import yaml

# Path to the corpus configuration
CORPUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus.yaml")

def load_urls_from_corpus(corpus_path=CORPUS_FILE):
    """
    Loads URLs from the corpus YAML configuration file.
    """
    try:
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            urls = [scheme["url"] for scheme in data.get("schemes", [])]
            return urls
    except Exception as e:
        print(f"Error loading {corpus_path}: {e}. Using fallback URLs.")
        return [
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            "https://groww.in/etfs/hdfc-silver-etf",
            "https://groww.in/mutual-funds/groww-nifty-india-defence-etf-fof-direct-growth",
            "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
        ]

URLS = load_urls_from_corpus()


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "scraped_data.json")

def format_mf_data(mf_data, url):
    """
    Format Mutual Fund data from the next_data JSON into readable structured text.
    """
    lines = []
    name = mf_data.get('scheme_name') or mf_data.get('fund_name') or url.split('/')[-1].replace('-', ' ').title()
    lines.append(f"# Scheme Name: {name}")
    lines.append(f"URL: {url}")
    lines.append(f"AMC: {mf_data.get('amc')}")
    lines.append(f"Fund House: {mf_data.get('fund_house')}")
    lines.append(f"Category: {mf_data.get('category')} - {mf_data.get('sub_category')}")
    lines.append(f"Launch Date: {mf_data.get('launch_date') or mf_data.get('allotment_date')}")
    lines.append(f"Description: {mf_data.get('description')}")
    lines.append(f"Current NAV: ₹{mf_data.get('nav')} (as of {mf_data.get('nav_date')})")
    
    # AUM
    aum = mf_data.get('aum')
    if aum:
        lines.append(f"AUM (Fund Size): ₹{aum:,.2f} Cr")
        
    # Expense Ratio
    exp = mf_data.get('expense_ratio')
    if exp:
        lines.append(f"Expense Ratio: {exp}%")
        
    # Exit Load
    exit_l = mf_data.get('exit_load')
    if exit_l:
        lines.append(f"Exit Load: {exit_l}")
        
    # Stamp Duty
    stamp = mf_data.get('stamp_duty')
    if stamp:
        lines.append(f"Stamp Duty: {stamp}")
        
    # Benchmark
    bench = mf_data.get('benchmark_name') or mf_data.get('benchmark')
    if bench:
        lines.append(f"Benchmark Index: {bench}")
        
    # Minimum Investments
    min_lump = mf_data.get('min_investment_amount')
    min_sip = mf_data.get('min_sip_investment')
    if min_lump:
        lines.append(f"Minimum Lumpsum Investment: ₹{min_lump:,}")
    if min_sip:
        lines.append(f"Minimum SIP Investment: ₹{min_sip:,}")
        
    # Fund Managers
    managers = []
    if mf_data.get('fund_manager_details'):
        for m in mf_data['fund_manager_details']:
            n = m.get('person_name') or m.get('fund_manager')
            if n:
                from_date = m.get('date_from', '')
                if from_date:
                    try:
                        year = from_date.split('-')[0]
                        n = f"{n} ({year} to Present)"
                    except:
                        pass
                managers.append(n)
    if not managers and mf_data.get('fund_manager'):
        managers = [mf_data['fund_manager']]
    if managers:
        lines.append(f"Fund Managers: {', '.join(managers)}")
        
    # Holdings
    holdings = mf_data.get('holdings', [])
    if holdings:
        lines.append("\nTop Holdings:")
        for h in holdings[:15]:
            lines.append(f"- {h.get('company_name') or h.get('name')}: {h.get('corpus_per') or h.get('percent') or h.get('assets')}% (Sector: {h.get('industry_name') or h.get('sector')})")
            
    # Returns
    stats = mf_data.get('return_stats', [])
    if stats:
        lines.append("\nHistorical Returns:")
        for s in stats:
            lines.append(f"- {s.get('period')}: {s.get('returns')}%")
            
    return "\n".join(lines)

def format_etf_data(page_props, url):
    """
    Format ETF data from the next_data JSON into readable structured text.
    """
    lines = []
    info = page_props.get('etfInfoData', {})
    etf = page_props.get('etfData', {})
    fund = page_props.get('fundamentalsData', {})
    
    name = etf.get('header', {}).get('name') or info.get('searchId', '').replace('-', ' ').title()
    lines.append(f"# ETF Name: {name}")
    lines.append(f"URL: {url}")
    lines.append(f"AMC: {info.get('amc')}")
    lines.append(f"Category: {info.get('category')}")
    lines.append(f"Launch Date: {info.get('foundationDate')}")
    lines.append(f"Description: {info.get('description')}")
    
    # NAV
    nav = fund.get('nav')
    if nav:
        lines.append(f"Current NAV: ₹{nav:.2f}")
        
    # AUM
    aum = fund.get('aumInCrores')
    if aum:
        lines.append(f"AUM (Fund Size): ₹{aum:,.2f} Cr")
        
    # Expense Ratio
    exp = fund.get('expenseRatio')
    if exp is not None:
        lines.append(f"Expense Ratio: {exp}%")
        
    # Tracking Error
    te = fund.get('trackingError')
    if te is not None:
        lines.append(f"Tracking Error: {te}%")
        
    # Benchmark
    bench = info.get('benchmarkIndex')
    if bench:
        lines.append(f"Benchmark Index: {bench}")
        
    # Fund Managers
    managers = []
    if info.get('fundManagers'):
        for m in info['fundManagers']:
            if isinstance(m, dict):
                n = m.get('personName') or m.get('name')
            else:
                n = str(m)
            if n:
                managers.append(n)
    if managers:
        lines.append(f"Fund Managers: {', '.join(managers)}")
        
    # Holdings
    holdings = page_props.get('sectorsData', {}).get('holdings', [])
    if holdings:
        lines.append("\nHoldings:")
        for h in holdings[:15]:
            lines.append(f"- {h.get('companyName')}: {h.get('percent')}% (Sector: {h.get('sectorName')})")
            
    return "\n".join(lines)

def clean_text_fallback(soup):
    """
    Fallback cleaner: Remove non-content HTML boilerplates and extract visible text.
    """
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
        tag.decompose()
        
    content_list = []
    main_content = soup.find("body") or soup

    for element in main_content.find_all(["h1", "h2", "h3", "p", "table", "li"]):
        if element.name == "table":
            rows = []
            for tr in element.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                content_list.append("\nTable Data:\n" + "\n".join(rows) + "\n")
        elif element.name in ["h1", "h2", "h3"]:
            content_list.append(f"\n# {element.get_text(strip=True)}\n")
        else:
            text = element.get_text(strip=True)
            if text:
                content_list.append(text)
                
    return "\n".join(content_list)

def scrape_urls():
    """
    Scrapes the 5 target URLs and saves the extracted clean text to a JSON file.
    Uses Next.js structured state for maximum detail/accuracy, falling back to raw DOM parsing.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    scraped_results = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    print(f"Starting ingestion process for {len(URLS)} URLs...")
    
    for url in URLS:
        print(f"Scraping: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.string.strip() if soup.title else url
                
                # Check for __NEXT_DATA__ for rich structured data
                next_data_script = soup.find("script", id="__NEXT_DATA__")
                extracted_text = ""
                used_next_data = False
                
                if next_data_script and next_data_script.string:
                    try:
                        data = json.loads(next_data_script.string)
                        page_props = data.get("props", {}).get("pageProps", {})
                        
                        # Process Mutual Fund vs ETF
                        if "mfServerSideData" in page_props:
                            extracted_text = format_mf_data(page_props["mfServerSideData"], url)
                            used_next_data = True
                        elif "etfData" in page_props or "etfInfoData" in page_props:
                            extracted_text = format_etf_data(page_props, url)
                            used_next_data = True
                    except Exception as json_err:
                        print(f"JSON parsing error for {url}: {json_err}. Falling back to DOM parsing...")
                
                if not used_next_data:
                    # Fallback to standard DOM text parsing
                    extracted_text = clean_text_fallback(soup)
                    extracted_text = f"# {title}\nURL: {url}\n\n" + extracted_text
                
                scraped_results.append({
                    "url": url,
                    "title": title,
                    "content": extracted_text,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                print(f"Successfully scraped: {title} (NextJS Data: {used_next_data})")
            else:
                print(f"Failed to fetch {url}. Status code: {response.status_code}")
                scraped_results.append({
                    "url": url,
                    "title": url.split("/")[-1].replace("-", " ").title(),
                    "content": f"Failed to retrieve data from {url}. Status code: {response.status_code}",
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "error": f"HTTP {response.status_code}"
                })
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            scraped_results.append({
                "url": url,
                "title": url.split("/")[-1].replace("-", " ").title(),
                "content": f"Error loading data for {url}: {str(e)}",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            })
            
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(scraped_results, f, ensure_ascii=False, indent=2)
        
    print(f"Ingestion process completed. Scraped data saved to {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    scrape_urls()
