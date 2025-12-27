import requests
import time
import uuid
import sys
import logging
import asyncio
# Import Scrapers (This drone has the codebase)
from src.scraper import StaticScraper
from src.dynamic_scraper import DynamicScraper

# Configuration
QUEEN_URL = "http://localhost:8000" # Change this to Queen's IP if remote
DRONE_ID = f"Drone-{uuid.uuid4().hex[:6]}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(f"[{DRONE_ID}]")

def register():
    try:
        resp = requests.post(f"{QUEEN_URL}/register", json={"drone_id": DRONE_ID, "capabilities": ["static", "dynamic"]})
        if resp.status_code == 200:
            logger.info("✅ Registered with Queen Bee.")
            return True
    except Exception as e:
        logger.error(f"❌ Could not reach Queen: {e}")
        return False

async def execute_task(task):
    logger.info(f"🚀 Executing Task: {task['url']} ({task.get('mode')})")
    url = task['url']
    mode = task.get('mode', 'Static')
    
    data = []
    if mode == "Static":
        s = StaticScraper(url, max_depth=1)
        data = await s.run()
    else:
        s = DynamicScraper(url, max_depth=1, headless=True)
        data = await s.run()
        
    return data

def run_drone():
    logger.info("🛸 Drone initializing...")
    if not register():
        return

    while True:
        try:
            # Ask for work
            resp = requests.get(f"{QUEEN_URL}/get_task", params={"drone_id": DRONE_ID})
            if resp.status_code == 200:
                payload = resp.json()
                task = payload.get("task")
                
                if task:
                    # Do work
                    try:
                        results = asyncio.run(execute_task(task))
                        
                        # Submit work
                        requests.post(f"{QUEEN_URL}/submit_result", json={
                            "task_id": task['id'],
                            "drone_id": DRONE_ID,
                            "data": results
                        })
                        logger.info(f"📦 Result submitted. ({len(results)} items)")
                    except Exception as e:
                        logger.error(f"Task Failed: {e}")
                else:
                    # Idle
                    print(".", end="", flush=True)
            
            time.sleep(2) # Heartbeat / Poll
            
        except Exception as e:
            logger.error(f"Connection lost: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Allow overriding Queen URL via CLI
    if len(sys.argv) > 1:
        QUEEN_URL = sys.argv[1]
    run_drone()
