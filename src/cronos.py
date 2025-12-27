import pandas as pd
import logging
from sqlalchemy import create_engine, text
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class Cronos:
    """
    The Timekeeper. Manages data versioning and difference detection.
    """
    def __init__(self, db_url="sqlite:///scraped_data.db"):
        self.engine = create_engine(db_url)

    def get_history(self, url):
        """
        Retrieves scraping history for a specific URL, ordered by time.
        """
        try:
            query = "SELECT * FROM scraped_results WHERE url = :url ORDER BY created_at DESC"
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params={"url": url})
            return df
        except Exception as e:
            logger.error(f"Cronos history fetch failed: {e}")
            return pd.DataFrame()

    def get_urls_with_history(self):
        """
        Returns URLs that have more than 1 version.
        """
        try:
            query = """
                SELECT url, COUNT(*) as count 
                FROM scraped_results 
                GROUP BY url 
                HAVING count > 1
            """
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn)
            return df['url'].tolist()
        except Exception as e:
            return []

    def calculate_diff(self, old_content, new_content):
        """
        Calculates a simple text diff ratio.
        Returns: (is_different: bool, similarity_ratio: float, details: str)
        """
        if not old_content or not new_content:
            return False, 0.0, "Empty content"
            
        matcher = SequenceMatcher(None, old_content, new_content)
        ratio = matcher.ratio()
        
        is_different = ratio < 1.0
        
        # Simple summary
        diff_len = len(new_content) - len(old_content)
        change_type = "Modified"
        if diff_len > 100: change_type = "Major Addition"
        elif diff_len < -100: change_type = "Major Deletion"
        
        return is_different, ratio, f"{change_type} ({diff_len:+d} chars)"

    def check_for_changes(self, url, new_content):
        """
        Compares new content against the LATEST version in DB.
        Used by Scheduler/SmartWatcher.
        """
        history = self.get_history(url)
        if history.empty:
            return True, 0.0, "New URL"
            
        latest_content = history.iloc[0]['content_snippet']
        return self.calculate_diff(latest_content, new_content)
