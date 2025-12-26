import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

class Scraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.ua = UserAgent()
        self.session = requests.Session()

    def get_headers(self):
        return {
            'User-Agent': self.ua.random
        }

    def fetch_page(self, url):
        try:
            response = self.session.get(url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse(self, html):
        if not html:
            return None
        soup = BeautifulSoup(html, 'html.parser')
        # This is a placeholder parsing logic.
        # It simply extracts the title and all links.
        data = {
            'title': soup.title.string if soup.title else 'No Title',
            'links': [a.get('href') for a in soup.find_all('a', href=True)]
        }
        return data

    def run(self):
        html = self.fetch_page(self.base_url)
        if html:
            return self.parse(html)
        return None
