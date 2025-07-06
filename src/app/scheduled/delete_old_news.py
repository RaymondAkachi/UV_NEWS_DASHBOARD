import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from sqlalchemy.exc import OperationalError, TimeoutError, StatementError
from tenacity import retry, wait_exponential, stop_after_attempt, before_log, after_log, retry_if_exception_type
from app.db_logic.db import engine
from app.db_logic.models import NewsArticle

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Retry Logic Configuration ---
RETRIABLE_DB_EXCEPTIONS = (OperationalError, TimeoutError, StatementError)


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RETRIABLE_DB_EXCEPTIONS),
    before_sleep=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARNING),
    reraise=True
)
async def delete_old_news_articles():
    """
    Deletes all news articles older than 30 days from the database with retry logic.

    Uses exponential backoff for transient database errors (e.g., connection issues, timeouts).
    Logs success or failure for debugging.
    """
    cutoff = datetime.utcnow() - timedelta(days=30)

    async with AsyncSession(engine) as session:
        try:
            result = await session.execute(
                delete(NewsArticle).where(NewsArticle.pubDate < cutoff)
            )
            await session.commit()
            deleted_count = result.rowcount
            logger.info(
                f"Successfully deleted {deleted_count} news articles older than 30 days")
        except RETRIABLE_DB_EXCEPTIONS as e:
            logger.error(f"Retriable database error during deletion: {e}")
            await session.rollback()
        except Exception as e:
            logger.error(f"Unexpected error during deletion: {e}")
            await session.rollback()

if __name__ == "__main__":
    import asyncio
    asyncio.run(delete_old_news_articles())
