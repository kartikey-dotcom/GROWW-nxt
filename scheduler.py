import os
import time
import threading
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from scraper import scrape_urls

# Load configuration from .env file
load_dotenv()

# India Standard Time (IST) is UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))

def get_seconds_until_10am_ist(now_ist=None):
    """
    Calculates the number of seconds until the next 10:00 AM IST (India Standard Time).
    If now_ist is provided, use it instead of the current time (useful for unit testing).
    """
    if now_ist is None:
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc.astimezone(IST)
    
    # Target 10:00 AM IST on the same day
    target_ist = now_ist.replace(hour=10, minute=0, second=0, microsecond=0)
    if now_ist >= target_ist:
        # If it is past 10:00 AM today in IST, target 10:00 AM IST tomorrow
        target_ist += timedelta(days=1)
        
    return (target_ist - now_ist).total_seconds()

def run_ingestion():
    """
    Function that performs the ingestion (scraping + indexing) and schedules the next run.
    """
    now_ist = datetime.now(timezone.utc).astimezone(IST)
    print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: Triggering ingestion component...")
    try:
        # Run scraper to fetch URLs and save raw scraped text
        scrape_urls()
        
        # After scraper completes, trigger indexer to rebuild embedding index
        try:
            from indexer import rebuild_index
            now_ist = datetime.now(timezone.utc).astimezone(IST)
            print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: Rebuilding vector index...")
            rebuild_index()
        except ImportError:
            now_ist = datetime.now(timezone.utc).astimezone(IST)
            print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: Warning: indexer.py not found.")
        except Exception as idx_err:
            now_ist = datetime.now(timezone.utc).astimezone(IST)
            print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: Indexer error: {idx_err}")
            
    except Exception as e:
        now_ist = datetime.now(timezone.utc).astimezone(IST)
        print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: Ingestion error: {e}")
        
    # Calculate delay for the next execution run
    test_interval = os.getenv("SCHEDULER_TEST_INTERVAL")
    if test_interval:
        try:
            delay = int(test_interval)
            now_ist = datetime.now(timezone.utc).astimezone(IST)
            print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: TEST MODE. Next run in {delay} seconds.")
        except ValueError:
            delay = 86400
            now_ist = datetime.now(timezone.utc).astimezone(IST)
            print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: Invalid test interval value. Using default 24 hours.")
    else:
        delay = get_seconds_until_10am_ist()
        now_ist = datetime.now(timezone.utc).astimezone(IST)
        next_run_time = now_ist + timedelta(seconds=delay)
        print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: Daily Mode active. Next run at {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} IST (in {delay:.2f} seconds).")
        
    t = threading.Timer(delay, run_ingestion)
    t.daemon = True
    t.start()

def start_scheduler(run_immediately=True):
    """
    Starts the daily ingestion scheduler.
    """
    now_ist = datetime.now(timezone.utc).astimezone(IST)
    print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Initializing Daily Ingestion Scheduler...")
    
    if run_immediately:
        run_ingestion()
    else:
        test_interval = os.getenv("SCHEDULER_TEST_INTERVAL")
        if test_interval:
            delay = int(test_interval)
            now_ist = datetime.now(timezone.utc).astimezone(IST)
            print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: TEST MODE. First run in {delay} seconds.")
        else:
            delay = get_seconds_until_10am_ist()
            now_ist = datetime.now(timezone.utc).astimezone(IST)
            next_run_time = now_ist + timedelta(seconds=delay)
            print(f"[{now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST] Scheduler: Daily Mode active. First run at {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} IST (in {delay:.2f} seconds).")
            
        t = threading.Timer(delay, run_ingestion)
        t.daemon = True
        t.start()
        
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped by user.")

if __name__ == "__main__":
    # In production/normal run, we can run immediately once to ensure sync on startup
    start_scheduler(run_immediately=True)
