import logging
from urllib.parse import urlparse
from ultimate_sitemap_parser.parser import Parser as SitemapParser
from robotexclusionrulesparser import RobotExclusionRulesParser

logger = logging.getLogger(__name__)

def parse_sitemap(url):
    """
    Parses a Sitemap XML and returns a list of all URLs found.
    Handles nested sitemaps automatically.
    """
    logger.info(f"🗺️ Parsing Sitemap: {url}")
    try:
        parser = SitemapParser(url)
        # The parser fetches and parses the sitemap tree
        urls = [page.url for page in parser.parse()]
        logger.info(f"✅ Found {len(urls)} URLs in sitemap.")
        return urls
    except Exception as e:
        logger.error(f"❌ Failed to parse sitemap: {e}")
        return []

def check_robots_txt(url, user_agent="DexScrapper"):
    """
    Checks if the URL is allowed to be crawled according to robots.txt.
    Returns True if allowed, False otherwise.
    """
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = f"{base_url}/robots.txt"
        
        rerp = RobotExclusionRulesParser()
        rerp.fetch(robots_url)
        
        is_allowed = rerp.is_allowed(user_agent, url)
        if not is_allowed:
            logger.warning(f"🚫 Blocked by robots.txt: {url}")
        
        return is_allowed
    except Exception as e:
        # If robots.txt fails (e.g. 404), usually we assume allowed
        logger.debug(f"Could not check robots.txt (assuming allowed): {e}")
        return True
