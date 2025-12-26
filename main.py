import asyncio
import argparse
import logging
from src.scraper import StaticScraper
from src.dynamic_scraper import DynamicScraper
from src.db_manager import DBManager
from src.utils import ensure_dir, save_to_csv, save_to_excel, save_to_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="DexScrapper Ultimate - Gacor Edition")
    parser.add_argument('--url', type=str, required=True, help='Target URL to scrape')
    parser.add_argument('--dynamic', action='store_true', help='Use Dynamic Scraper (Playwright) for JS sites')
    parser.add_argument('--depth', type=int, default=1, help='Crawl depth (Static mode only)')
    parser.add_argument('--db', type=str, help='Database filename (e.g., results.db) to save results to SQLite')
    parser.add_argument('--output', type=str, help='Output filename (supports .csv, .json, .xlsx)')
    parser.add_argument('--proxy', type=str, help='Proxy URL (e.g., http://user:pass@host:port)')
    
    args = parser.parse_args()
    
    url = args.url
    results = []

    # Initialize scraper with proxy if provided
    # Note: Scrapers need to be updated to accept proxy arg, adding logic here assuming they will be updated next.
    if args.dynamic:
        print(f"🚀 Starting Dynamic Scraper for {url} (Depth: {args.depth})...")
        scraper = DynamicScraper(url, max_depth=args.depth, proxy=args.proxy)
        results = await scraper.run()
    else:
        print(f"🕸️ Starting Static Scraper for {url} with depth {args.depth}...")
        scraper = StaticScraper(url, max_depth=args.depth, proxy=args.proxy)
        results = await scraper.run()
    
    if results:
        print(f"✅ Scraping successful! Found {len(results)} items.")
        
        # Save to DB if requested
        if args.db:
            db_path = f"sqlite:///{args.db}"
            db = DBManager(db_path)
            for item in results:
                db.save_result(
                    url=item['url'],
                    title=item['title'],
                    content_snippet=item.get('content_snippet')
                )
            print(f"💾 Data saved to database: {args.db}")
        
        # Handle File Output
        ensure_dir('output')
        
        # Prepare data for export
        export_data = []
        for item in results:
            entry = {
                'url': item.get('url'),
                'title': item.get('title'),
                'links_count': len(item.get('links', [])),
                'snippet': item.get('content_snippet', '')[:100]
            }
            export_data.append(entry)

        # Determine output format
        output_file = args.output if args.output else 'output/latest_run.csv'
        
        if output_file.endswith('.json'):
            save_to_json(export_data, output_file)
        elif output_file.endswith('.xlsx'):
            save_to_excel(export_data, output_file)
        else:
            # Default to CSV
            if not output_file.endswith('.csv'):
                 output_file += '.csv'
            save_to_csv(export_data, output_file)

        print(f"📂 Data exported to: {output_file}")

    else:
        print("❌ Scraping failed or no data found.")

if __name__ == "__main__":
    asyncio.run(main())
