from playwright.async_api import async_playwright
import asyncio
import logging
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class DynamicScraper:
    def __init__(self, base_url, max_depth=1, concurrency=3, headless=True, proxy=None):
        self.base_url = base_url
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.headless = headless
        self.proxy = {'server': proxy} if proxy else None
        self.ua = UserAgent()
        
        # State
        self.visited = set()
        self.results = []
        self.domain = urlparse(base_url).netloc

    def is_same_domain(self, url):
        return urlparse(url).netloc == self.domain

    async def scrape_page(self, context, url):
        page = await context.new_page()
        try:
            logger.info(f"Crawling: {url}")
            await page.goto(url, timeout=45000, wait_until='networkidle')
            
            # Extract Data
            title = await page.title()
            content_snippet = await page.inner_text('body')
            content_snippet = content_snippet[:500] + "..." if content_snippet else ""

            # Extract Links
            links = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('a'))
                        .map(a => a.href)
                        .filter(href => href.startsWith('http'));
                }
            """)
            
            # Filter links to same domain
            valid_links = [l for l in links if self.is_same_domain(l)]
            
            return {
                'url': url,
                'title': title,
                'content_snippet': content_snippet,
                'links': valid_links
            }
        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            return None
        finally:
            await page.close()

    async def worker(self, queue, context, semaphore):
        while True:
            url, depth = await queue.get()
            if depth > self.max_depth:
                queue.task_done()
                continue
            
            if url in self.visited:
                queue.task_done()
                continue
            
            self.visited.add(url)
            
            async with semaphore:
                data = await self.scrape_page(context, url)
            
            if data:
                self.results.append(data)
                
                # Add child links to queue if depth allows
                if depth < self.max_depth:
                    for link in data['links']:
                         if link not in self.visited:
                             await queue.put((link, depth + 1))
            
            queue.task_done()

    async def run(self):
        logger.info(f"Starting Dynamic Crawl for {self.base_url} (Depth: {self.max_depth}, Proxy: {self.proxy})")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless, proxy=self.proxy)
            context = await browser.new_context(
                user_agent=self.ua.random,
                viewport={'width': 1920, 'height': 1080}
            )
            
            queue = asyncio.Queue()
            await queue.put((self.base_url, 0))
            
            semaphore = asyncio.Semaphore(self.concurrency)
            
            # Start workers
            workers = [asyncio.create_task(self.worker(queue, context, semaphore)) 
                      for _ in range(self.concurrency)]
            
            # Wait for queue to process
            await queue.join()
            
            # Cancel workers
            for w in workers:
                w.cancel()
                
            await browser.close()
            
        return self.results
