from duckduckgo_search import DDGS
import logging
import asyncio
from src.scraper import StaticScraper
from src.ai_utils import parse_with_ai
from src.utils import save_to_markdown

logger = logging.getLogger(__name__)

class CerebroAgent:
    """
    Autonomous Research Agent.
    Searches the web -> Scrapes content -> Synthesizes answer using AI.
    """
    def __init__(self, openai_key):
        self.openai_key = openai_key
        self.ddgs = DDGS()

    def search_web(self, query, max_results=5):
        """
        Searches DuckDuckGo for the query.
        """
        logger.info(f"🧠 Cerebro Searching: {query}")
        results = []
        try:
            # simple search
            ddg_results = self.ddgs.text(query, max_results=max_results)
            if ddg_results:
                for r in ddg_results:
                    results.append({'url': r['href'], 'title': r['title']})
        except Exception as e:
            logger.error(f"Search failed: {e}")
        return results

    async def research_topic(self, topic, status_callback=None):
        """
        Performs full research flow.
        """
        if status_callback: status_callback(f"🔍 Searching web for: {topic}...")
        
        sources = self.search_web(topic, max_results=4)
        if not sources:
            return "❌ No sources found."

        scraped_data = []
        
        # Scrape sources
        if status_callback: status_callback(f"📖 Reading {len(sources)} sources...")
        
        for source in sources:
            try:
                # Use Static Scraper for speed
                scraper = StaticScraper(source['url'], max_depth=1)
                res = await scraper.run()
                if res:
                    page = res[0] # Get first page
                    # Read markdown file content if available, else snippet
                    content = ""
                    if page.get('markdown_file'):
                        with open(page['markdown_file'], 'r', encoding='utf-8') as f:
                            content = f.read()
                    else:
                        content = page.get('content_snippet', '')
                    
                    scraped_data.append(f"Source: {source['url']}\nTitle: {source['title']}\nContent:\n{content[:5000]}\n\n---")
            except Exception as e:
                logger.error(f"Failed to read {source['url']}: {e}")

        if not scraped_data:
            return "❌ Failed to scrape any content."

        # Synthesize with AI
        if status_callback: status_callback("🧠 Thinking & Writing Report...")
        
        full_context = "\n".join(scraped_data)
        prompt = f"Write a comprehensive research report on: '{topic}'. Use the following sources. cite them if possible. Format in Markdown."
        
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_key)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are Cerebro, an advanced research assistant."},
                    {"role": "user", "content": f"Context:\n{full_context}\n\nInstruction: {prompt}"}
                ]
            )
            report = response.choices[0].message.content
            
            # Save report
            save_to_markdown(f"Report_{topic}", "Cerebro", report, folder="output/cerebro")
            return report
            
        except Exception as e:
            return f"❌ AI Error: {e}"
