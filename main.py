from src.scraper import Scraper
from src.utils import save_to_csv, ensure_dir

def main():
    # Example URL (replace with actual target)
    url = "https://example.com"
    
    print(f"Starting scraper for {url}...")
    scraper = Scraper(url)
    data = scraper.run()
    
    if data:
        print("Scraping successful!")
        print(f"Title: {data.get('title')}")
        print(f"Found {len(data.get('links', []))} links.")
        
        # Save results
        ensure_dir('output')
        # Flattening for CSV example
        csv_data = [{'title': data['title'], 'link': link} for link in data['links']]
        save_to_csv(csv_data, 'output/data.csv')
    else:
        print("Scraping failed.")

if __name__ == "__main__":
    main()
