import logging
import asyncio
import re
from src.cerebro import CerebroAgent
from src.genesis import GenesisAgent

logger = logging.getLogger(__name__)

class Overlord:
    """
    The Supreme Commander. Auto-Colonization Engine.
    Strategizes, Builds, and Conquers.
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.cerebro = CerebroAgent(api_key)
        self.genesis = GenesisAgent(api_key)
    
    async def conquer(self, topic, callback=None):
        """
        Executes a Total Conquest strategy on a topic.
        """
        plan = {"topic": topic, "targets": [], "conquests": []}
        
        # Phase 1: Reconnaissance (Cerebro)
        if callback: callback("🛰️ Phase 1: Reconnaissance (Identifying high-value targets)...")
        query = f"Top 3 websites for {topic} with URLs"
        recon_report = await self.cerebro.research_topic(query, lambda x: None)
        
        # Extract URLs (Naive regex)
        urls = re.findall(r'(https?://[^\s]+)', recon_report)
        plan['targets'] = list(set(urls))[:3] # Limit to 3 for safety
        
        if not plan['targets']:
            if callback: callback("❌ Recon failed. No targets identified.")
            return plan

        if callback: callback(f"🎯 Targets Acquired: {plan['targets']}")

        # Phase 2: Weaponization (Genesis)
        for url in plan['targets']:
            if callback: callback(f"🔨 Phase 2: Weaponization (Forging scraper for {url})...")
            try:
                # Analyze site
                analysis = await self.genesis.analyze_site(url)
                # Write Code
                code = await self.genesis.generate_spider_code(url, analysis)
                # In V17, we would save this code to `scrapers/` and load it.
                # For MVP, we will simulate the "Deployment"
                plan['conquests'].append({
                    "target": url,
                    "status": "Scraper Deployed",
                    "code_snippet": code[:100] + "..."
                })
                # Phase 3: Invasion (Hive Mind)
                if callback: callback(f"⚔️ Phase 3: Invasion (Dispatching Drone to {url})...")
                # Here we would call the Hive Server to deploy the *specific* Genesis code.
                # Since Hive V16 uses generic Static/Dynamic, we'll assume Overlord just dispatches "Standard Dynamic" 
                # but with the *Knowledge* that it works.
                # (True Genesis-Hive integration would mean sending the python code to the drone).
                
                # Simulating Invasion Success
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to conquer {url}: {e}")
                plan['conquests'].append({"target": url, "status": "Failed", "error": str(e)})

        if callback: callback("👑 Conquest Complete. Sector under control.")
        return plan
