import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from urllib.parse import urlparse, urljoin
from .media_utils import download_file
from .utils import save_to_markdown
import markdownify
import re
import os
import json
from src.crawler_utils import parse_sitemap, check_robots_txt

logger = logging.getLogger(__name__)

class StaticScraper:
    def __init__(self, base_url, max_depth=1, concurrency=5, proxy=None, download_media=False, url_filter=None, link_regex=None, robots_compliance=False):
        self.base_url = base_url
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.proxy = proxy
        self.download_media = download_media
        self.url_filter = url_filter.lower() if url_filter else None
        self.link_regex = link_regex
        self.robots_compliance = robots_compliance
        self.visited = set()
        self.ua = UserAgent()
        self.results = []
        self.domain = urlparse(base_url).netloc
        
        # State
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
            except: pass

    def is_allowed_by_regex(self, url):
        if not self.link_regex: return True
        return re.search(self.link_regex, url) is not None

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
                if self.link_regex and not self.is_allowed_by_regex(href):
                    continue
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

        # Filtering Check
        if self.url_filter and self.url_filter not in url.lower():
            if url != self.base_url:
                logger.info(f"Skipping {url} (Filtered)")
                self.visited.add(url)
                return

        self.visited.add(url)
        
        try:
            html = await self.fetch_page(session, url)
            if html:
                data = self.parse(html, url)
                if data:
                    # Media Downloading
                    media_files = []
                    if self.download_media:
                        soup = BeautifulSoup(html, 'html.parser')
                        media_urls = []
                        # Images
                        for img in soup.find_all('img', src=True):
                            src = urljoin(url, img['src'])
                            media_urls.append(src)
                        # PDFs
                        for a in soup.find_all('a', href=True):
                            if a['href'].lower().endswith('.pdf'):
                                href = urljoin(url, a['href'])
                                media_urls.append(href)
                        
                        for media_url in media_urls:
                            saved_path = await download_file(session, media_url, "output/media")
                            if saved_path:
                                media_files.append(saved_path)
                    
                    data['media_files'] = media_files
                    
                    # Markdown Conversion
                    md_text = markdownify.markdownify(html, heading_style="ATX")
                    md_path = save_to_markdown(data['title'], url, md_text)
                    data['markdown_file'] = md_path

                    self.results.append(data)
                    logger.info(f"Scraped {url}: {data['title']}")

                    if depth < self.max_depth:
                        tasks = []
                        links_to_follow = data['links'] # Follow all valid links instead of limiting to 5, as concurrency limits execution
                        
                        for link in links_to_follow:
                             if link not in self.visited:
                                 # Basic domain check for crawl scope
                                 if urlparse(link).netloc == self.domain:
                                     tasks.append(self.crawl(link, depth + 1, session))
                        
                        if tasks:
                            # Apply concurrency using semaphore if we were to refactor, 
                            # but for now recursive gather is simple. 
                            # Ideally we should use a queue like DynamicScraper but this is "Static (Fast)"
                            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")

    async def run(self):
        logger.info(f"Starting Static Crawl for {self.base_url} (Depth: {self.max_depth})")
        async with aiohttp.ClientSession() as session:
            # Sitemap check
            if self.base_url.endswith('.xml'):
                logger.info("🗺️ Detected Sitemap input.")
                urls = parse_sitemap(self.base_url)
                tasks = []
                for u in urls:
                    if u not in self.visited:
                        tasks.append(self.crawl(u, 0, session))
                if tasks: await asyncio.gather(*tasks)
            else:
                await self.crawl(self.base_url, 0, session)
        return self.results
