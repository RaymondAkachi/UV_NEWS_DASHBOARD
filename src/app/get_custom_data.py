import logging
from typing import Tuple, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
from requests.exceptions import RequestException, HTTPError
from urllib.error import URLError
import socket
import feedparser
from tenacity import retry, wait_exponential, stop_after_attempt, before_log, after_log, retry_if_exception_type
from app.models.sentiment import analyze_sentiment

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
logger.info("Successfully loaded NEWS_API_KEY")

# --- Dummy Data ---
ALT_HEADLINES = [
    {"title": "Tech Giant Unveils New AI Processor",
     "link": "https://www.verylongexample.com/ai-innovation/tech-giant-unveils-revolutionary-new-artificial-intelligence-processor-details.html"},
    {"title": "Global Markets React to Interest Rate Hike",
     "link": "https://www.financeworldnews.org/economy/global-markets-show-mixed-reactions-to-recent-central-bank-interest-rate-hike-analysis.html"},
    {"title": "Breakthrough in Renewable Energy Storage",
     "link": "https://www.greenenergynow.net/research/new-breakthrough-in-long-duration-renewable-energy-storage-technology-paving-the-way.html"},
    {"title": "Local Charity Exceeds Fundraising Goal",
     "link": "https://www.communityvoice.com/local-updates/local-charity-campaign-exceeds-fundraising-goal-thanks-to-overwhelming-community-support.html"},
    {"title": "New Study on Climate Change Impacts",
     "link": "https://www.environmentalsciencejournal.org/climate-research/comprehensive-new-study-highlights-severe-climate-change-impacts-globally.html"}
]

# --- Retry Logic Configuration ---
RETRIABLE_EXCEPTIONS = (RequestException, HTTPError, URLError, socket.timeout)

# --- Utility Functions ---


def safe_join(value: Any) -> str:
    """Convert a value to a string, joining lists with commas."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v)
    if isinstance(value, (str, int, float)):
        return str(value)
    return ""


def _extract_needed_data(response: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Extract descriptions and publication dates from Newsdata.io API response."""
    descriptions = []
    dates = []

    if not isinstance(response, dict):
        logger.error("Invalid API response: not a dictionary")
        return [], []

    results = response.get("results", [])
    if not results:
        logger.info("No results found in API response")
        return [], []

    for article in results:
        description = article.get("description") or article.get("title", "")
        descriptions.append(safe_join(description))
        dates.append(safe_join(article.get("pubDate", "")))

    logger.info(f"Extracted {len(descriptions)} articles from API response")
    return descriptions, dates

# --- Main Functions ---


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RETRIABLE_EXCEPTIONS),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARNING),
    reraise=False
)
def get_data(input: str) -> Tuple[List[str], List[float], List[int], List[Dict[str, str]]]:
    """
    Fetch news data from Newsdata.io API and Google News RSS, analyze sentiments, and prepare visualization data.
    Returns dummy headlines if RSS fetch fails.

    Args:
        input (str): Search query for news articles.

    Returns:
        Tuple containing:
            - List[str]: Publication dates.
            - List[float]: Sentiment scores for descriptions.
            - List[int]: Counts of positive, neutral, negative sentiments for pie chart.
            - List[Dict[str, str]]: Top headlines with titles and links.
    """
    # Default return value for failures
    default_return = ([], [], [0, 0, 0], ALT_HEADLINES)

    # Fetch from Newsdata.io API
    NEWS_URL = f"https://newsdata.io/api/1/latest?apikey={NEWS_API_KEY}&language=en&q={input}"
    try:
        response = requests.get(NEWS_URL, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        descriptions, dates = _extract_needed_data(response_data)
    except HTTPError as e:
        if e.response.status_code in (429, 503):
            logger.warning(
                f"Retriable HTTP error {e.response.status_code} for {NEWS_URL}: {e}")
            raise
        logger.error(
            f"Non-retriable HTTP error {e.response.status_code} for {NEWS_URL}: {e}")
        return default_return
    except RETRIABLE_EXCEPTIONS as e:
        logger.warning(
            f"Retriable error fetching API data from {NEWS_URL}: {e}")
        return default_return
    except Exception as e:
        logger.error(
            f"Unexpected error fetching API data from {NEWS_URL}: {e}")
        return default_return

    # Analyze sentiments
    sentiments = []
    try:
        for description in descriptions:
            sentiments.append(analyze_sentiment(description))
    except Exception as e:
        logger.error(f"Error analyzing sentiments: {e}")
        return default_return

    # Prepare pie chart data
    positive, neutral, negative = 0, 0, 0
    positive_threshold, negative_threshold = 0.2, -0.2
    for score in sentiments:
        if score > positive_threshold:
            positive += 1
        elif score < negative_threshold:
            negative += 1
        else:
            neutral += 1
    pie_data = [positive, neutral, negative]

    # Fetch RSS headlines
    cleaned_input = ''.join(input.split())
    rss_url = f"https://news.google.com/rss/search?q={cleaned_input}&hl=en-US&gl=US&ceid=US:en"
    try:
        top_headlines = top_news(rss_url)
    except Exception as e:
        logger.error(f"Failed to fetch RSS headlines from {rss_url}: {e}")
        top_headlines = ALT_HEADLINES

    logger.info(
        f"Fetched {len(descriptions)} API articles and {len(top_headlines)} RSS headlines")
    return dates, sentiments, pie_data, top_headlines


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RETRIABLE_EXCEPTIONS),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARNING),
    reraise=True
)
def top_news(url: str) -> List[Dict[str, str]]:
    """
    Fetch the top 5 news headlines from an RSS feed URL.
    Returns dummy data (ALT_HEADLINES) if the fetch fails or no headlines are found.

    Args:
        url (str): The RSS feed URL to fetch headlines from.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing 'title' and 'link' for each headline.
    """
    top_headlines = []
    try:
        feed = feedparser.parse(url)
        if feed.get("bozo", False):
            logger.warning(
                f"Invalid RSS feed at {url}: {feed.get('bozo_exception')}")
            return ALT_HEADLINES

        for entry in feed.entries[:5]:  # Get top 5 headlines
            if hasattr(entry, "title") and hasattr(entry, "link"):
                top_headlines.append({
                    "title": entry.title,
                    "link": entry.link
                })

        if not top_headlines:
            logger.info(
                f"No valid headlines found at {url}, returning dummy data")
            return ALT_HEADLINES

        logger.info(
            f"Successfully fetched {len(top_headlines)} headlines from {url}")
        return top_headlines

    except RETRIABLE_EXCEPTIONS as e:
        logger.warning(f"Retriable error fetching RSS feed from {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching RSS feed from {url}: {e}")
        return ALT_HEADLINES

# --- Test Function ---


def main_test():
    try:
        dates, sentiments, pie_data, headlines = get_data("technology")
        logger.info(
            f"Fetched {len(dates)} dates, {len(sentiments)} sentiments, pie data {pie_data}, {len(headlines)} headlines")
        for headline in headlines:
            logger.info(
                f"Title: {headline['title']}, Link: {headline['link']}")
    except Exception as e:
        logger.error(f"Test failed: {e}")


if __name__ == "__main__":
    main_test()


# from dotenv import load_dotenv
# import os
# import requests
# import feedparser
# from app.models.sentiment import analyze_sentiment
# from pathlib import Path  # Import Path

# # ... (other imports) ...

# BASE_DIR = Path(__file__).resolve().parent.parent

# dotenv_path = BASE_DIR / 'app' / '.env'

# load_dotenv(dotenv_path)
# NEWSAPI_KEY = os.getenv("NEWS_API_KEY")
# print(f"DEBUG: NEWSAPI_KEY loaded: {NEWSAPI_KEY}")


# def _extract_needed_data(response):
#     dates = []
#     descriptions = []

#     results = response.get("results", [])
#     if results == []:
#         print("No results found")
#     for article in results:
#         def safe_join(value):
#             if isinstance(value, list):
#                 return ", ".join(value)
#             if isinstance(value, str):
#                 return value
#             return ""
#         description = article["description"]
#         if description is None:
#             description = article['title']
#         descriptions.append(safe_join(description))
#         dates.append(safe_join(article["pubDate"]))
#     return descriptions, dates


# def get_data(input: str):
#     top_news = []
#     NEWS_URL = f"https://newsdata.io/api/1/latest?apikey={NEWSAPI_KEY}&language=en&q={input}"
#     response = requests.get(NEWS_URL)
#     response = response.json()
#     sentiments = []
#     descriptions, dates = _extract_needed_data(response)
#     # Needed data for line graph sentiment scores, dates
#     for i in descriptions:
#         sentiments.append(analyze_sentiment(i))

#     # needed data for pie chart
#     positive = 0
#     neutral = 0
#     negative = 0
#     positive_threshold = 0.2
#     negative_threshold = -0.2

#     for score in sentiments:
#         if score > positive_threshold:
#             positive += 1
#         elif score < negative_threshold:
#             negative += 1
#         else:
#             neutral += 1

#     pie_data = [positive, neutral, negative]

#     # We will empty the table
#     cleaned_input = input.split()
#     cleaned_input = ''.join(cleaned_input)
#     link = f"https://news.google.com/rss/search?q={cleaned_input}&hl=en-US&gl=US&ceid=US:en"
#     feed = feedparser.parse(link)
#     top_headlines = []

#     for entry in feed.entries[:10]:  # Get top 5
#         top_headlines.append({
#             "title": entry.title,
#             "link": entry.link,
#         })
#     return dates, sentiments, pie_data, top_headlines


# def top_news(url):
#     alt_headlines = [
#         {"title": "Tech Giant Unveils New AI Processor",
#          "link": "https://www.verylongexample.com/ai-innovation/tech-giant-unveils-revolutionary-new-artificial-intelligence-processor-details.html"},
#         {"title": "Global Markets React to Interest Rate Hike",
#          "link": "https://www.financeworldnews.org/economy/global-markets-show-mixed-reactions-to-recent-central-bank-interest-rate-hike-analysis.html"},
#         {"title": "Breakthrough in Renewable Energy Storage",
#          "link": "https://www.greenenergynow.net/research/new-breakthrough-in-long-duration-renewable-energy-storage-technology-paving-the-way.html"},
#         {"title": "Local Charity Exceeds Fundraising Goal",
#          "link": "https://www.communityvoice.com/local-updates/local-charity-campaign-exceeds-fundraising-goal-thanks-to-overwhelming-community-support.html"},
#         {"title": "New Study on Climate Change Impacts",
#          "link": "https://www.environmentalsciencejournal.org/climate-research/comprehensive-new-study-highlights-severe-climate-change-impacts-globally.html"},
#         {"title": "Startup Secures Series B Funding Round",
#          "link": "https://www.startupinsights.co/funding/promising-fintech-startup-secures-oversubscribed-series-b-funding-round-for-expansion.html"},
#         {"title": "Major Sports Event Kicks Off This Weekend",
#          "link": "https://www.sportseverywhere.com/events/annual-international-sports-tournament-kicks-off-this-weekend-full-schedule-and-athlete-profiles.html"},
#         {"title": "Health Organization Issues New Guidelines",
#          "link": "https://www.healthnewsdaily.org/public-health/major-health-organization-issues-new-public-health-guidelines-for-seasonal-illnesses.html"},
#         {"title": "Cultural Festival Draws Record Crowds",
#          "link": "https://www.artsculturemagazine.com/festival-reviews/annual-cultural-arts-festival-draws-record-breaking-crowds-and-acclaim.html"},
#     ]
#     top_headlines = []
#     try:
#         feed = feedparser.parse(url)
#         for entry in feed.entries[:10]:  # Get top 5
#             top_headlines.append({
#                 "title": entry.title,
#                 "link": entry.link,
#             })
#         if not top_headlines:
#             return alt_headlines
#     except BaseException:
#         return alt_headlines
#     return top_headlines


# a, b, c, d = get_data("Iran")
# print(a, '\n', b, '\n', c, '\n', d)
# Data needed for line graph
# - sentiment scores
# dates in string     form

# Data needed for pie chart
# - sentiment scores

# Top sources table
# sources, sentiment,

# Top news articles
# custom api call to the google url
