import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class StaticScraper:
    def __init__(self, base_url, max_depth=1, concurrency=5, proxy=None):
        self.base_url = base_url
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.proxy = proxy
        self.visited = set()
        self.ua = UserAgent()
        self.results = []

    def get_headers(self):
        return {
            'User-Agent': self.ua.random
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(aiohttp.ClientError)
    )
    async def fetch_page(self, session, url):
        try:
            logger.info(f"Fetching: {url}")
            async with session.get(url, headers=self.get_headers(), proxy=self.proxy, timeout=15) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise

    def parse(self, html, url):
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else 'No Title'
        
        # Extract content snippet
        body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
        content_snippet = body_text[:500] + "..." if len(body_text) > 500 else body_text

        links = set()
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if href.startswith('http'):
                links.add(href)
            # Add more sophisticated collection if needed

        return {
            'url': url,
            'title': title,
            'links': list(links),
            'content_snippet': content_snippet
        }

    async def crawl(self, url, depth, session):
        if depth > self.max_depth or url in self.visited:
            return

        self.visited.add(url)
        
        try:
            html = await self.fetch_page(session, url)
            if html:
                data = self.parse(html, url)
                if data:
                    self.results.append(data)
                    logger.info(f"Scraped {url}: {data['title']}")

                    if depth < self.max_depth:
                        tasks = []
                        links_to_follow = data['links'][:5] 
                        
                        for link in links_to_follow:
                             if link not in self.visited:
                                 tasks.append(self.crawl(link, depth + 1, session))
                        
                        if tasks:
                            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")

    async def run(self):
        logger.info(f"Starting Static Crawl for {self.base_url} (Depth: {self.max_depth})")
        async with aiohttp.ClientSession() as session:
            await self.crawl(self.base_url, 0, session)
        return self.results
