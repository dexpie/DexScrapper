import logging
import asyncio
import pandas as pd
from src.scraper import StaticScraper
from src.dynamic_scraper import DynamicScraper
from src.alchemy import Alchemist
from src.cerebro import CerebroAgent

logger = logging.getLogger(__name__)

class NexusPipeline:
    """
    The Orchestrator. Chains modules together.
    """
    def __init__(self, api_key=None):
        self.steps = []
        self.api_key = api_key
        # Data passed between steps
        self.context = {
            "urls": [],     # List of URLs to process
            "data": [],     # List of scraped dicts
            "df": None,     # DataFrame representation
            "report": ""    # Text report
        }

    def add_step(self, module_name, config):
        self.steps.append({"module": module_name, "config": config})

    async def execute(self, update_callback=None):
        """
        Runs the pipeline sequentially.
        """
        for i, step in enumerate(self.steps):
            module = step['module']
            config = step['config']
            
            if update_callback: update_callback(f"🔗 Nexus: Running Step {i+1} - {module}...")
            
            try:
                if module == "Cerebro (Finder)":
                    # Output: List of URLs
                    agent = CerebroAgent(self.api_key)
                    # We assume Cerebro returns a report, but for Pipeline we might need structured URL extraction
                    # For V15 simple implementation: Use Cerebro to just "find" URLs? 
                    # Cerebro's research_topic returns text. Let's make a rudimentary URL extractor from it.
                    report = await agent.research_topic(config['query'], lambda x: None)
                    # Extract URLs from report (Naive)
                    import re
                    urls = re.findall(r'(https?://[^\s]+)', report)
                    self.context['urls'] = list(set(urls))
                    self.context['report'] = report
                    if update_callback: update_callback(f"🧠 Cerebro found {len(self.context['urls'])} URLs.")

                elif module == "Scraper (Harvester)":
                    # Input: context['urls'] or config['urls']
                    target_urls = config.get('urls', [])
                    if not target_urls and self.context['urls']:
                        target_urls = self.context['urls']
                    
                    if not target_urls:
                        raise Exception("No URLs to scrape!")
                    
                    results = []
                    # Limit for safety in demo
                    limit = int(config.get('limit', 5))
                    target_urls = target_urls[:limit]
                    
                    mode = config.get('mode', 'Static')
                    
                    for url in target_urls:
                        if mode == "Static":
                            s = StaticScraper(url, max_depth=1)
                            res = await s.run()
                        else:
                            s = DynamicScraper(url, max_depth=1)
                            res = await s.run()
                        results.extend(res)
                    
                    self.context['data'] = results
                    self.context['df'] = pd.DataFrame(results)
                    if update_callback: update_callback(f"🚀 Scraper harvested {len(results)} items.")

                elif module == "Alchemy (Enricher)":
                    # Input: context['df']
                    if self.context['df'] is None or self.context['df'].empty:
                         raise Exception("No data to enrich!")
                    
                    alchemist = Alchemist(self.api_key)
                    new_df = await alchemist.transmute(
                        self.context['df'], 
                        config['target_col'], 
                        config['prompt'],
                        lambda x: None
                    )
                    self.context['df'] = new_df
                    if update_callback: update_callback(f"⚗️ Alchemy enriched {len(new_df)} rows.")

                elif module == "Webhook (Exporter)":
                    # Input: context['df'] or context['data']
                    webhook_url = config['url']
                    payload = {
                        "source": "DexScrapper Nexus",
                        "count": len(self.context['data']),
                        "data": self.context['data'] # Might be huge
                    }
                    # If DF exists and enriched, prefer that
                    if self.context['df'] is not None:
                        payload['data'] = self.context['df'].to_dict(orient='records')

                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        await session.post(webhook_url, json=payload)
                    if update_callback: update_callback(f"🔌 Payload sent to Webhook.")

            except Exception as e:
                logger.error(f"Pipeline failed at step {i}: {e}")
                if update_callback: update_callback(f"❌ Error at {module}: {e}")
                raise e
        
        return self.context
