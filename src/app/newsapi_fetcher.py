import logging
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv
import httpx
import os
from tenacity import retry, wait_exponential, stop_after_attempt, before_log, after_log, retry_if_exception_type

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

# --- Utility Functions ---


def safe_join(value: Any) -> str:
    """Convert a value to a string, joining lists with commas."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v)
    if isinstance(value, (str, int, float)):
        return str(value)
    return ""

# --- News Fetcher Class ---


class NewsFetcher:
    RETRIABLE_EXCEPTIONS = (
        httpx.RequestError,  # Network issues, connection errors
        httpx.HTTPStatusError,  # HTTP errors like 429, 503
        httpx.TimeoutException  # Timeout errors
    )

    def __init__(self, base_url: str = "https://newsdata.io/api/1/latest"):
        self.api_key = NEWS_API_KEY
        self.base_url = base_url
        self.news_url = f"{base_url}?apikey={self.api_key}&language=en"

    def extract_data(self, json_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract relevant fields from the Newsdata.io API response."""
        if not isinstance(json_data, dict):
            logger.error("Invalid JSON data: not a dictionary")
            return {}

        if json_data.get("status") != "success":
            logger.warning(
                f"API returned non-success status: {json_data.get('status')}")
            return {}

        results = json_data.get("results", [])
        if not results:
            logger.info("No results found in API response")
            return {
                "countries": [], "descriptions": [], "pubDates": [],
                "source_ids": [], "links": [], "titles": []
            }

        source_ids = []
        descriptions = []
        countries = []
        pub_dates = []
        titles = []
        links = []

        for article in results:
            source_ids.append(safe_join(article.get("source_id")))
            descriptions.append(
                safe_join(article.get("description") or article.get("title"))
            )
            titles.append(safe_join(article.get("title")))
            links.append(safe_join(article.get("link")))
            countries.append(safe_join(article.get("country")))
            pub_dates.append(safe_join(article.get("pubDate")))

        logger.info(f"Extracted data for {len(titles)} articles")
        return {
            "countries": countries,
            "descriptions": descriptions,
            "pubDates": pub_dates,
            "source_ids": source_ids,
            "links": links,
            "titles": titles
        }

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RETRIABLE_EXCEPTIONS),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.WARNING),
        reraise=True
    )
    async def fetch_news(self) -> Dict[str, List[str]]:
        """Fetch news articles from the Newsdata.io API with retry logic."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(self.news_url)
                response.raise_for_status()
                data_json = response.json()
                logger.info("Successfully fetched news from API")
                return self.extract_data(data_json)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503):
                    logger.warning(
                        f"Retriable HTTP error {e.response.status_code}: {e}")
                    raise
                logger.error(
                    f"Non-retriable HTTP error {e.response.status_code}: {e}")
                return {}
            except (httpx.RequestError, httpx.TimeoutException) as e:
                logger.warning(f"Retriable network error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching news: {e}")
                return {}

# --- Test Function ---


async def main_test():
    # fetcher = NewsFetcher()
    try:
        news_data = await NewsFetcher().fetch_news()
        logger.info(
            f"Fetched news data: {len(news_data.get('titles', []))} articles")
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_test())
