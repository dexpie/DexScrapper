from openai import OpenAI
import logging
import os
import asyncio
from src.dynamic_scraper import DynamicScraper
from src.ai_utils import parse_with_ai

logger = logging.getLogger(__name__)

class GenesisAgent:
    """
    The Creator. Analyzes websites and writes specialized Playwright scrapers.
    """
    def __init__(self, api_key, model="gpt-4o", base_url=None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    async def analyze_and_generate(self, url, objective, update_callback=None):
        """
        Analyzes the target URL and generates a Python script.
        """
        if update_callback: update_callback(f"🕵️ Genesis is scouting target: {url}...")
        
        # 1. Scout the site (Get HTML/Screenshot)
        # We use DynamicScraper in Vision Mode to get the best context
        scout = DynamicScraper(url, max_depth=1, headless=True, vision_mode=True)
        # Quick run
        # We need to manually invoke scrape_page because run() does too much queuing
        async with asyncio.Lock(): 
             # Just a quick hack to use the existing logic without full crawl
             # Actually, let's just properly use the class
             # But run() is designed for crawling.
             # Let's instantiate playwright manually for speed or reuse scrape_page if possible.
             # Re-using DynamicScraper structure:
             from playwright.async_api import async_playwright
             async with async_playwright() as p:
                 browser = await p.chromium.launch(headless=True)
                 context = await browser.new_context(user_agent=scout.ua.random)
                 content, links, screenshot = await scout.scrape_page(context, url, screenshot=True)
                 await browser.close()

        if update_callback: update_callback("🧠 Constructing Terminator blueprint...")

        # 2. Construct Prompt
        system_prompt = (
            "You are GENESIS, an elite autonomous coder. "
            "Write a COMPLETE, STANDALONE Python script using `playwright` (async_api) to scrape the requested data. "
            "The script must: \n"
            "1. Be self-contained (imports included).\n"
            "2. Run via `asyncio.run(main())`.\n"
            "3. Print the result as valid JSON to STDOUT at the very end.\n"
            "4. Handle errors gracefully.\n"
            "5. Use headless mode.\n"
            "6. NO markdown fencing (```python). Return ONLY raw code."
        )
        
        user_msg = f"Target URL: {url}\nObjective: {objective}\n\n"
        if screenshot:
            user_msg += "I have provided a screenshot of the page to help you understand the layout."
        else:
            user_msg += f"HTML snippet:\n{content[:2000]}..."

        # 3. Call AI
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": user_msg}
            ]}
        ]
        
        if screenshot:
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{screenshot}"}
            })

        if update_callback: update_callback(f"🧬 Writing code ({self.model})...")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        
        code = response.choices[0].message.content
        
        # Clean markdown if present (just in case)
        code = code.replace("```python", "").replace("```", "").strip()
        
        if update_callback: update_callback("✅ Terminator ready.")
        return code

    def save_spider(self, code, name):
        filename = f"scrapers/{name}.py"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        return filename
