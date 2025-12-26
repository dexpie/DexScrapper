import asyncio
import json
import os
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

async def create_session(session_name, url="https://google.com"):
    """
    Launches a headed browser for the user to login manually.
    Saves the session state (cookies/storage) to a file upon closing.
    """
    session_file = os.path.join(SESSION_DIR, f"{session_name}.json")
    
    async with async_playwright() as p:
        logger.info(f"Launching browser to create session: {session_name}")
        browser = await p.chromium.launch(headless=False) # Headed for manual interaction
        context = await browser.new_context()
        
        page = await context.new_page()
        await page.goto(url)
        
        print(f"Please log in manually in the browser window.")
        print(f"Close the browser window when you are done to save the session.")
        
        # Wait for user to close the browser (checking periodically)
        try:
            while len(context.pages) > 0:
                await asyncio.sleep(1)
        except Exception:
            pass # Browser closed
            
        # Save storage state
        await context.storage_state(path=session_file)
        logger.info(f"Session saved to {session_file}")
        await browser.close()
        return session_file

async def load_session(context, session_name):
    """
    Loads a saved session into a Playwright context.
    """
    session_file = os.path.join(SESSION_DIR, f"{session_name}.json")
    if os.path.exists(session_file):
        # We can't load state into an existing context easily in all versions, 
        # usually session is passed at context creation. 
        # But if the context is already created, we might need to add cookies manually 
        # if using context.add_cookies for partial updates.
        # Ideally, this function returns the path to be used in browser.new_context(storage_state=path).
        return session_file
    return None

def get_available_sessions():
    """Returns a list of available session names."""
    if not os.path.exists(SESSION_DIR):
        return []
    files = [f.replace(".json", "") for f in os.listdir(SESSION_DIR) if f.endswith(".json")]
    return files
