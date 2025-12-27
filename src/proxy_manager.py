import aiohttp
import asyncio
import logging
import random
import re

logger = logging.getLogger(__name__)

class ProxyManager:
    """
    Ghost Proxies. Harvests public proxies and manages rotation.
    """
    def __init__(self):
        self.proxies = []
        self.sources = [
            "https://www.sslproxies.org/",
            "https://free-proxy-list.net/",
            "https://us-proxy.org/"
        ]

    async def harvest_proxies(self):
        """
        Harvests proxies from public sources.
        """
        logger.info("🎭 Ghost Proxies: Starting Harvest...")
        found_proxies = set()
        
        async with aiohttp.ClientSession() as session:
            for url in self.sources:
                try:
                    async with session.get(url, timeout=10) as response:
                        text = await response.text()
                        # Regex to find IP:Port
                        matches = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', text)
                        for ip, port in matches:
                            found_proxies.add(f"http://{ip}:{port}")
                except Exception as e:
                    logger.error(f"Failed to harvest from {url}: {e}")
        
        self.proxies = list(found_proxies)
        logger.info(f"🎭 Ghost Proxies: Harvested {len(self.proxies)} proxies.")
        return len(self.proxies)

    def get_random_proxy(self):
        """Get a random proxy from the pool."""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
