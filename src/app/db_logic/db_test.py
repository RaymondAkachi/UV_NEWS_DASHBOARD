# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import declarative_base, sessionmaker
# from sqlalchemy import Column, Integer, String, Float, DateTime, Text
# from sqlalchemy.exc import (
#     OperationalError, IntegrityError, ProgrammingError,  # Common SQLAlchemy exceptions
#     DBAPIError, StatementError, TimeoutError  # Broader exceptions
# )
# from tenacity import (
#     retry,
#     wait_exponential,
#     stop_after_attempt,
#     before_log,
#     after_log,
#     retry_if_exception_type,
#     AsyncRetrying  # For async functions
# )

# from dotenv import load_dotenv
# import os
# import asyncio
# from datetime import datetime  # Ensure datetime is imported for your data processing
# import logging
# import re  # For URL_REGEX if not defined elsewhere

# # --- Configuration ---
# load_dotenv()
# DATABASE_URL = os.getenv("TEST_DATABASE_URL")
# print(DATABASE_URL)

# # Configure logging
# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Define a simple URL regex if it's not defined elsewhere in your code
# # (Assuming it's used in your data processing loop)
# URL_REGEX = re.compile(
#     r'^(?:http|ftp)s?://'  # http:// or https://
#     # domain...
#     r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
#     r'localhost|'  # localhost...
#     r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
#     r'(?::\d+)?'  # optional port
#     r'(?:/?|[/?]\S+)$', re.IGNORECASE
# )


# # --- SQLAlchemy Setup ---
# # Create an asynchronous engine
# # It's good practice to set pool parameters explicitly, especially for a Gunicorn app
# # Default pool size for asyncpg is 10, max_overflow 0
# # Consider increasing if you have many concurrent workers/requests
# engine = create_async_engine(
#     DATABASE_URL,
#     echo=False,  # Set to True for verbose SQL logging (useful for debugging)
#     pool_size=10,  # Number of connections to keep in the pool
#     max_overflow=5,  # Number of connections that can be opened beyond pool_size
#     pool_timeout=30,  # seconds to wait for a connection from the pool
#     connect_args={
#         "timeout": 10  # Connection timeout for asyncpg (in seconds)
#     }
# )

# # Declarative base for defining models
# Base = declarative_base()

# # AsyncSessionLocal is your session factory
# AsyncSessionLocal = sessionmaker(
#     bind=engine,
#     class_=AsyncSession,
#     expire_on_commit=False,  # Prevents objects from expiring after commit
# )

# # --- Database Model (as provided) ---


# class NewsArticle(Base):
#     __tablename__ = "news_articles"

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, nullable=False)
#     source_id = Column(String, nullable=False)
#     country = Column(String, nullable=False)
#     pubDate = Column(DateTime, nullable=False)
#     sentiment = Column(Float, nullable=False)
#     category = Column(String, nullable=False)
#     link = Column(String)


# # --- Database Initialization / Table Creation ---
# async def create_tables():
#     logger.info("Attempting to create database tables...")
#     try:
#         async with engine.begin() as conn:
#             await conn.run_sync(Base.metadata.create_all)
#         logger.info("Database tables ensured to exist.")
#     except Exception as e:
#         logger.critical(f"Failed to create database tables: {e}")
#         # Depending on your app, this might be a fatal error on startup
#         raise

# # --- Retry Logic for Async Database Operations ---

# # Exceptions that are generally safe to retry for database operations
# # These often indicate transient network issues, temporary overload, or deadlocks
# RETRIABLE_DB_EXCEPTIONS = (
#     # Connection issues, pool timeouts (e.g., asyncpg.exceptions.PostgresConnectionError)
#     OperationalError,
#     TimeoutError,          # SQLAlchemy's internal timeout error from connection pool
#     StatementError,        # Broader statement execution errors, might wrap transient issues
#     # Directly catch asyncpg exceptions wrapped by DBAPIError if needed,
#     # but `OperationalError` usually covers connection issues well.
#     # For deadlocks, asyncpg.exceptions.SerializationError or StatementError might wrap it.
#     # If using explicit asyncpg for specific queries, you might add:
#     # asyncpg.exceptions.DeadlockDetectedError, asyncpg.exceptions.SerializationError
# )


# @retry(
#     # Exponential backoff: 1, 2, 4, 8, 10 seconds max
#     wait=wait_exponential(multiplier=1, min=1, max=10),
#     stop=stop_after_attempt(5),                          # Maximum 5 attempts
#     retry=retry_if_exception_type(RETRIABLE_DB_EXCEPTIONS),
#     # Log before sleeping for retry
#     before_sleep=before_log(logger, logging.INFO),
#     # Log after each attempt (success/failure)
#     after=after_log(logger, logging.WARNING),
#     # Re-raise the exception if all retries fail
#     reraise=True
# )
# async def execute_with_retry(async_func, *args, **kwargs):
#     """
#     Generic async retry wrapper for database operations.
#     The wrapped async_func should ideally take an AsyncSession as its first argument
#     or contain the session context.
#     """
#     # This design assumes the async_func handles the session context itself,
#     # e.g., it uses 'async with AsyncSessionLocal() as session:' internally.
#     return await async_func(*args, **kwargs)

# # --- Database Operations (Adapted for async and retry) ---


# async def insert_article(session: AsyncSession, data: dict):
#     """
#     Inserts a single news article into the database.
#     This function expects an active session.
#     """
#     new_article = NewsArticle(**data)
#     session.add(new_article)
#     # The commit is handled by the `async with session:` block outside
#     # or you might commit here if this is a single, isolated transaction
#     # await session.commit() # Only if this is the ONLY operation in its transaction
#     logger.info(f"Prepared to insert article: {data['title']}")

# # --- Wrapper for database interactions that includes session management and retry ---


# async def save_articles_to_db(news: dict, classifications: list):
#     """
#     Fetches news, processes it, and saves articles to the database with retry logic.
#     This function manages the AsyncSession and calls the retry-wrapped insert_article.
#     """
#     try:
#         async with AsyncSessionLocal() as session:  # Session lifecycle managed here
#             # Perform operations that constitute a single transaction
#             for i, (country, description, pub_date, source_id, link, title) in enumerate(zip(
#                 news['countries'], news['descriptions'], news['pubDates'],
#                 news['source_ids'], news['links'], news['titles']
#             )):
#                 try:
#                     dt = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S')
#                 except ValueError:
#                     logger.warning(
#                         f"Invalid pubDate format for article '{title}': {pub_date}. Skipping.")
#                     continue

#                 # Dummy sentiment analysis function, replace with your actual
#                 sentiment = 0.5  # analyze_sentiment(description)
#                 if not URL_REGEX.match(link):
#                     link = None

#                 data = {
#                     "source_id": source_id,
#                     "sentiment": sentiment,
#                     "country": country,
#                     "pubDate": dt,
#                     "category": classifications[i],
#                     "link": link,
#                     "title": title
#                 }
#                 # Call the insert function within the session context
#                 # No need for execute_with_retry directly on insert_article if the session is managed externally
#                 # and you commit/rollback the whole batch.
#                 # If you want retries per-article, you'd need a different session strategy
#                 # or separate transactions for each article.
#                 # For batch inserts, the retry should wrap the *entire batch* and transaction.
#                 session.add(NewsArticle(**data))

#             # After adding all articles, commit the transaction
#             await session.commit()
#             logger.info(
#                 f"Successfully committed {len(news['titles'])} news articles to the database.")

#     except IntegrityError as e:
#         # This is a non-retriable error (e.g., unique constraint violation)
#         logger.error(f"Database Integrity Error (non-retriable): {e}")
#         # You might log the specific data that caused the conflict or attempt to update instead
#         await session.rollback()  # Ensure rollback if any changes were staged before the error
#     except OperationalError as e:
#         # This error is retried by tenacity if execute_with_retry wraps the higher-level function
#         logger.error(f"Database Operational Error (might be retried): {e}")
#         await session.rollback()
#         raise  # Re-raise to let tenacity catch it
#     except Exception as e:
#         logger.error(f"An unexpected error occurred during database save: {e}")
#         await session.rollback()
#         raise


# # Dummy async news fetcher and sentiment analyzer for demonstration
# async def get_news_dummy():
#     await asyncio.sleep(0.1)  # Simulate network delay
#     return {
#         'countries': ['US', 'CA', 'US'],
#         'descriptions': ['Desc 1', 'Desc 2', 'Desc 3'],
#         'pubDates': ['2025-07-01 10:00:00', '2025-07-01 11:00:00', '2025-07-01 12:00:00'],
#         'source_ids': ['src1', 'src2', 'src3'],
#         'links': ['http://example.com/a', 'http://example.com/b', 'invalid-link'],
#         'titles': ['Title 1', 'Title 2', 'Title 3']
#     }


# def analyze_sentiment(text):
#     return 0.5  # Dummy sentiment


# # --- Main execution block for testing ---
# if __name__ == "__main__":
#     async def main():
#         await create_tables()

#         logger.info("Fetching dummy news data...")
#         # Replace with your actual get_news
#         news_data = await get_news_dummy()
#         classifications_data = ["Politics", "Sports",
#                                 "Technology"]  # Dummy classifications

#         logger.info("Attempting to save news articles with retry logic...")
#         try:
#             # Wrap the entire saving process in execute_with_retry
#             await execute_with_retry(save_articles_to_db, news_data, classifications_data)
#             logger.info(
#                 "All news articles processed and saved successfully (or after retries).")
#         except Exception as e:
#             logger.error(
#                 f"Final failure to save news articles after all retries: {e}")

#     asyncio.run(main())
