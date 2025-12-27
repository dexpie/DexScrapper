from playwright.async_api import async_playwright
import asyncio
import re
import json
import logging
import os
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin
import aiohttp
from src.media_utils import download_file
from src.utils import save_to_markdown
from src.crawler_utils import parse_sitemap, check_robots_txt
import markdownify

logger = logging.getLogger(__name__)

class DynamicScraper:
    def __init__(self, url, max_depth=2, concurrency=3, headless=True, proxy=None, download_media=False, url_filter=None, session_file=None, link_regex=None, robots_compliance=False, vision_mode=False):
        self.start_url = url
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.headless = headless
        self.proxy = proxy
        self.download_media = download_media
        self.url_filter = url_filter
        self.session_file = session_file
        self.link_regex = link_regex
        self.robots_compliance = robots_compliance
        self.vision_mode = vision_mode
        self.ua = UserAgent()
        
        # State
        self.visited = set()
        self.results = []
        self.semaphore = asyncio.Semaphore(concurrency)
        self.domain = urlparse(url).netloc
        
        # Load state if exists
        self.state_file = f"crawl_state_{self.domain.replace(':', '_')}.json"
        self.load_state()

    def save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(list(self.visited), f)
        except: pass

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.visited = set(json.load(f))
                logger.info(f"🔄 Resumed crawl. {len(self.visited)} pages already visited.")
            except: pass
        
        # Load state if exists
        self.state_file = f"crawl_state_{self.domain.replace(':', '_')}.json"
        self.load_state()

    def save_state(self):
        """Saves visited URLs to a file for resuming."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(list(self.visited), f)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def load_state(self):
        """Loads visited URLs from file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.visited = set(json.load(f))
                logger.info(f"🔄 Resumed crawl. {len(self.visited)} pages already visited.")
            except: pass

    def is_same_domain(self, url):
        return urlparse(url).netloc == self.domain

    def is_allowed_by_regex(self, url):
        if not self.link_regex:
            return True
        return re.search(self.link_regex, url) is not None

    def is_allowed_by_regex(self, url):
        if not self.link_regex:
            return True
        return re.search(self.link_regex, url) is not None

    async def scrape_page(self, context, url):
        page = await context.new_page()
        # Apply Stealth (Manual Injection)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        try:
            logger.info(f"Crawling: {url}")
            await page.goto(url, timeout=45000, wait_until='networkidle')
            
            # Extract Data
            title = await page.title()
            content_snippet = await page.inner_text('body')
            content_snippet = content_snippet[:500] + "..." if content_snippet else ""
            
            # Markdown Conversion
            html_content = await page.content()
            md_text = markdownify.markdownify(html_content, heading_style="ATX")
            md_path = save_to_markdown(title, url, md_text)

            # Media Downloading
            media_files = []
            if self.download_media:
                # Find images
                images = await page.evaluate("""() => Array.from(document.querySelectorAll('img')).map(img => img.src)""")
                # Find PDF links
                pdfs = await page.evaluate("""() => Array.from(document.querySelectorAll('a[href$=".pdf"]')).map(a => a.href)""")
                
                async with aiohttp.ClientSession() as session:
                    for media_url in images + pdfs:
                        if media_url.startswith('http'):
                            saved_path = await download_file(session, media_url, "output/media")
                            if saved_path:
                                media_files.append(saved_path)

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
            if self.link_regex:
                valid_links = [l for l in valid_links if self.is_allowed_by_regex(l)]
            
            # Apply URL Filter for next steps? No, filters are usually for *what to scrape*, not just links.
            # But here we filter links to queue.
            if self.url_filter:
                 # If we only want to follow links that match keywords
                 valid_links = [l for l in valid_links if self.url_filter in l.lower()]
            
            return {
                'url': url,
                'title': title,
                'content_snippet': content_snippet,
                'links': valid_links,
                'media_files': media_files,
                'markdown_file': md_path
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
            
            # Robots check
            if self.robots_compliance:
                if not check_robots_txt(url, self.ua.random):
                    logger.warning(f"🚫 Skipped (Robots.txt): {url}")
                    queue.task_done()
                    continue

            # Filtering Check
            if self.url_filter and self.url_filter not in url.lower():
                # If we consider Base URL as exception or not? Usually we scrape base anyway.
                if url != self.base_url:
                     logger.info(f"Skipping {url} (Filtered)")
                     self.visited.add(url) # Mark as visited to avoid re-check
                     queue.task_done()
                     continue
            
            self.visited.add(url)
            self.save_state()
            
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
        logger.info(f"Starting Dynamic Crawl for {self.start_url} (Depth: {self.max_depth}, Proxy: {self.proxy})") # Changed self.base_url to self.start_url
        
        async with async_playwright() as p:
            browser_args = {}
            if self.proxy:
                 parsed = urlparse(self.proxy)
                 browser_args['proxy'] = {
                     'server': f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                 }
                 if parsed.username and parsed.password:
                     browser_args['proxy']['username'] = parsed.username
                     browser_args['proxy']['password'] = parsed.password

            browser = await p.chromium.launch(headless=self.headless, args=["--disable-blink-features=AutomationControlled"], **browser_args) # Added **browser_args here
            
            context_args = {
                "user_agent": self.ua.random, # Changed UserAgent().random to self.ua.random
                "viewport": {"width": 1280, "height": 720},
                "locale": "en-US"
            }
            if self.session_file and os.path.exists(self.session_file):
                context_args['storage_state'] = self.session_file
                logger.info(f"Loaded session from {self.session_file}")

            context = await browser.new_context(**context_args) # Removed **browser_args as it's already in launch
            
            # Anti-detect scripts
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            queue = asyncio.Queue()
            
            # Check if input is a sitemap
            if self.start_url.endswith('.xml'):
                logger.info("🗺️ Detected Sitemap input. loading URLs...")
                sitemap_urls = parse_sitemap(self.start_url)
                for u in sitemap_urls:
                    if u not in self.visited:
                        queue.put_nowait((u, 0))
            else:
                if self.start_url not in self.visited:
                    queue.put_nowait((self.start_url, 0))
            
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
