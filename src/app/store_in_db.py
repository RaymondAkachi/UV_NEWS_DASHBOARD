import logging
import re
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Callable, Any
from pathlib import Path
from dotenv import load_dotenv
import os
from sqlalchemy.exc import OperationalError, IntegrityError, StatementError, TimeoutError
from tenacity import retry, wait_exponential, stop_after_attempt, before_log, after_log, retry_if_exception_type
from app.models.sentiment import analyze_sentiment
from app.models.news_classifier import classify_articles
from app.db_logic.models import NewsArticle, create_tables
from app.db_logic.db import AsyncSessionLocal
from app.newsapi_fetcher import NewsFetcher
from sqlalchemy.ext.asyncio import AsyncSession

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Environment Variable Loading ---
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / 'app' / '.env'

if not dotenv_path.exists():
    raise FileNotFoundError(f".env file not found at {dotenv_path}")

load_dotenv(dotenv_path)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_API_KEY:
    raise ValueError("NEWS_API_KEY not set in .env file")

# NEWS_URL = f"https://newsdata.io/api/1/latest?apikey={NEWS_API_KEY}&q=pizza"

# --- Regex for URL Validation ---


def is_valid_url(url: str) -> bool:
    """Validate a URL using a regex pattern."""
    url_regex = re.compile(
        r'^(https?:\/\/)?'  # Optional http:// or https://
        r'(www\.)?'         # Optional www.
        r'([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}'  # Domain name and TLD
        r'(\/[^\s]*)?$'     # Optional path/query
    )
    return bool(url_regex.match(url))


# --- Retry Logic for Async Database Operations ---
RETRIABLE_DB_EXCEPTIONS = (OperationalError, TimeoutError, StatementError)


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RETRIABLE_DB_EXCEPTIONS),
    before_sleep=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARNING),
    reraise=True
)
async def execute_with_retry(async_func: Callable[..., Any], *args, **kwargs) -> Any:
    """Execute an async function with retry logic for database operations."""
    if not asyncio.iscoroutinefunction(async_func):
        raise ValueError(
            f"Function {async_func.__name__} must be an async function")
    return await async_func(*args, **kwargs)

# --- News Processor Class ---


class NewsProcessor:
    # def __init__(self, news_url: str):
    #     self.news_url = news_url
    async def insert_article(self, session: AsyncSession, data: Dict[str, Any]) -> bool:
        """Insert a single article into the database with retry logic."""
        try:
            article = NewsArticle(**data)
            session.add(article)
            await session.commit()
            await session.refresh(article)
            logger.info(f"Inserted article: {data['title']}")
            return True
        except IntegrityError as e:
            logger.warning(
                f"Skipping duplicate article '{data['title']}': {e}")
            await session.rollback()
            return False
        except RETRIABLE_DB_EXCEPTIONS as e:
            logger.error(
                f"Retriable error inserting article '{data['title']}': {e}")
            await session.rollback()
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error inserting article '{data['title']}': {e}")
            await session.rollback()
            return False

    async def process_news_data(self, session: AsyncSession) -> int:
        """Fetch, process, and store news articles in the database."""
        news = await NewsFetcher().fetch_news()
        for value in news.values():
            if value is None:
                logger.info("No news fetched")
                return 0

        classifications = classify_articles(news["descriptions"])
        inserted_count = 0

        for i, (country, description, pub_date, source_id, link, title) in enumerate(zip(
            news['countries'], news['descriptions'], news['pubDates'],
            news['source_ids'], news['links'], news['titles']
        )):
            try:
                dt = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S')
                sentiment = analyze_sentiment(description)
                validated_link = link if is_valid_url(link) else None

                data = {
                    "source_id": source_id,
                    "sentiment": sentiment,
                    "country": country,
                    "pubDate": dt,
                    "category": classifications[i],
                    "link": validated_link,
                    "title": title
                }

                success = await execute_with_retry(self.insert_article, session, data)
                if success:
                    inserted_count += 1
            except Exception as e:
                logger.error(f"Failed to process article '{title}': {e}")

        logger.info(
            f"Successfully processed {inserted_count} of {len(news['titles'])} articles")
        return inserted_count

    async def store_in_db(self) -> None:
        """Main method to create tables, process news, and store in Redis."""
        await create_tables()
        async with AsyncSessionLocal() as session:
            try:
                inserted_count = await self.process_news_data(session)
                if inserted_count > 0:
                    from app.scheduled.store_in_redis import store_data_in_redis
                    await store_data_in_redis()
                    logger.info(
                        "Stored data in Redis after successful DB insertion")
            except Exception as e:
                logger.error(f"Failed to process and store news: {e}")
                await session.rollback()

# --- Test Function ---


async def main_test():
    processor = NewsProcessor()
    await processor.store_in_db()

if __name__ == "__main__":
    asyncio.run(main_test())
