from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base, ScrapedData
import logging

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self, db_path='sqlite:///scraped_data.db'):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_result(self, url, title, content_snippet=None):
        session = self.Session()
        try:
            # Check if exists
            existing = session.query(ScrapedData).filter_by(url=url).first()
            if existing:
                existing.title = title
                existing.content_snippet = content_snippet
                logger.info(f"Updated DB entry for {url}")
            else:
                new_entry = ScrapedData(url=url, title=title, content_snippet=content_snippet)
                session.add(new_entry)
                logger.info(f"Created DB entry for {url}")
            session.commit()
        except Exception as e:
            logger.error(f"DB Error: {e}")
            session.rollback()
        finally:
            session.close()
