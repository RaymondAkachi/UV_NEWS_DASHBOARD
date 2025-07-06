
import logging
# from typing import NoneType
from pathlib import Path
from dotenv import load_dotenv
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tenacity import retry, wait_exponential, stop_after_attempt, before_log, after_log, retry_if_exception_type
from app.scheduled.delete_old_news import delete_old_news_articles
from app.store_in_db import NewsProcessor
from sqlalchemy.exc import OperationalError, TimeoutError, StatementError

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
# Default to Africa/Lagos if not set
TIME_ZONE = os.getenv("TIME_ZONE", "Africa/Lagos")
logger.info(f"Using timezone: {TIME_ZONE}")

# --- Retry Logic Configuration ---
RETRIABLE_EXCEPTIONS = (OperationalError, TimeoutError, StatementError)

# --- Scheduler Instance ---
scheduler = AsyncIOScheduler(timezone=TIME_ZONE)

# --- Retry Wrapper for Jobs ---


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RETRIABLE_EXCEPTIONS),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARNING),
    reraise=False
)
async def retry_job(func):
    """Wrap an async job function with retry logic."""
    try:
        await func()
    except RETRIABLE_EXCEPTIONS as e:
        logger.error(f"Job failed after retries: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error in job: {e}")
        return

# --- Scheduler Management Functions ---


async def startup_function():
    """
    Initialize and start the APScheduler with scheduled jobs.
    Logs when the scheduler starts and adds jobs for deleting old news and storing new articles.
    """
    try:
        # Add job: Delete old news articles daily at midnight
        scheduler.add_job(
            retry_job,
            args=[delete_old_news_articles],
            trigger='cron',
            hour=0,
            minute=0,
            id='delete_old_news',
            name='Delete News Older Than 1 Month',
            replace_existing=True
        )
        logger.info(
            "Scheduled job: 'Delete News Older Than 1 Month' at midnight daily")

        # Add job: Store news articles every 4 hours
        news_processor = NewsProcessor()  # Create instance once
        scheduler.add_job(
            retry_job,
            args=[news_processor.store_in_db],
            trigger='interval',
            hours=4,
            id='store_news',
            name='Store News Articles Every 4 Hours',
            replace_existing=True
        )
        logger.info(
            "Scheduled job: 'Store News Articles Every 4 Hours' every 4 hours")

        # Start the scheduler
        scheduler.start()
        logger.info("APScheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise


async def shutdown_function():
    """
    Gracefully shut down the APScheduler.
    Logs when the scheduler is stopped.
    """
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("APScheduler shut down successfully")
        else:
            logger.info("APScheduler was not running")
    except Exception as e:
        logger.error(f"Failed to shut down scheduler: {e}")
        raise

# --- Test Function ---


if __name__ == "__main__":
    import asyncio

    async def main_test():
        try:
            await startup_function()
            # Keep the event loop running to allow scheduled jobs
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await shutdown_function()

    asyncio.run(main_test())
