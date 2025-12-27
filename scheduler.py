import asyncio
import json
import logging
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.scraper import StaticScraper
from src.dynamic_scraper import DynamicScraper
from src.db_manager import DBManager
from src.notifications import send_discord_webhook

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "sqlite:///scraped_data.db"
JOBS_FILE = "scheduled_jobs.json"

def run_job(job_config):
    """
    Executes a scraping job based on configuration.
    """
    url = job_config.get('url')
    mode = job_config.get('mode', 'Static')
    depth = job_config.get('depth', 1)
    webhook = job_config.get('webhook')
    
    logger.info(f"⏰ Starting Scheduled Job: {url} ({mode})")
    
    try:
        results = []
        if mode == "Static":
            scraper = StaticScraper(url, max_depth=depth, concurrency=3)
            results = asyncio.run(scraper.run())
        else:
            # Dynamic
            scraper = DynamicScraper(url, max_depth=depth, concurrency=3)
            results = asyncio.run(scraper.run())
            
        if results:
            # Save to DB
            db = DBManager(DB_PATH)
            for item in results:
                db.save_result(
                    url=item['url'],
                    title=item['title'],
                    content_snippet=item.get('content_snippet')
                )
            
            
            logger.info(f"✅ Job Complete. Scraped {len(results)} pages.")
            
            # --- V14: SMART WATCHER (Diff Check) ---
            from src.cronos import Cronos
            cronos = Cronos()
            
            # Check for changes in the first result (primary target)
            if results:
                target_result = results[0]
                is_diff, ratio, details = cronos.check_for_changes(target_result['url'], target_result.get('content_snippet', ''))
                
                if is_diff:
                    msg = f"🔔 **Smart Alert**: Change Detected on {target_result['url']}\nDetails: {details}\nSimilarity: {ratio*100:.1f}%"
                    logger.info(msg)
                    
                    if webhook:
                        send_discord_webhook(webhook, msg)
                else:
                    logger.info(f"💤 No significant change on {target_result['url']}. Alert suppressed.")
            
        else:
            logger.warning("Job finished but no data found.")
            
    except Exception as e:
        logger.error(f"Job Failed: {e}")
        if webhook:
             send_discord_webhook(webhook, f"⚠️ DexScrapper Job Failed: {url}\nError: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Load Jobs
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, 'r') as f:
                jobs = json.load(f)
                
            for job in jobs:
                if job.get('active', True):
                    interval = job.get('interval_minutes', 60)
                    scheduler.add_job(
                        run_job, 
                        IntervalTrigger(minutes=interval), 
                        args=[job],
                        id=f"job_{job['url']}",
                        replace_existing=True
                    )
                    logger.info(f"Scheduled: {job['url']} every {interval} mins")
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")
    else:
        logger.info("No jobs file found.")

    scheduler.start()
    logger.info("Scheduler Started. Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    start_scheduler()
