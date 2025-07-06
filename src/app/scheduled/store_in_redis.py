import redis.asyncio as redis
from dotenv import load_dotenv
import os
import json
from app.data_extraction.line_graph_data import get_daily_avg_sentiment
from app.data_extraction.pie_chart_data import get_sentiment_pie_data
from app.data_extraction.top_sources import get_top_sources_with_avg_sentiment
from app.data_extraction.top_news import get_news_headlines  # optional if implemented
from app.redis_logic.async_redis import RedisClient

load_dotenv('.env')


async def store_summary_period(client: RedisClient, label: str, days: int, category: str | None = None):
    """
    Helper to store summary for a given period (week/month) and optional category
    under Redis key: sentiment:{label}
    """
    key = label
    data = {
        "line_graph": await get_daily_avg_sentiment(days=days, category=category),
        "pie_chart": await get_sentiment_pie_data(days=days, category=category),
        "top_sources": await get_top_sources_with_avg_sentiment(days=days, category=category),
    }
    await client.set(key, json.dumps(data))


async def store_data_in_redis():
    REDIS_URL = os.getenv("REDIS_URL")
    client = RedisClient(REDIS_URL)
    await client.initialize()

    # Monthly summaries
    await store_summary_period(client, "monthly_summary", days=30)
    await store_summary_period(client, "monthly_business", days=30, category="Business")
    await store_summary_period(client, "monthly_sports", days=30, category="Sports")
    await store_summary_period(client, "monthly_sci_tech", days=30, category="Sci/Tech")
    await store_summary_period(client, "monthly_world", days=30, category="World")

    # Weekly summaries
    await store_summary_period(client, "weekly_summary", days=7)
    await store_summary_period(client, "weekly_business", days=7, category="Business")
    await store_summary_period(client, "weekly_sports", days=7, category="Sports")
    await store_summary_period(client, "weekly_sci_tech", days=7, category="Sci/Tech")
    await store_summary_period(client, "weekly_world", days=7, category="World")

    await client.close()

    # Headline news (optional if implemented)
    # headlines = {
    #     "main": await get_news_headlines(sector=None),
    #     "business": await get_news_headlines(sector="Business"),
    #     "sports": await get_news_headlines(sector="Sports"),
    #     "sci_tech": await get_news_headlines(sector="Sci/Tech"),
    #     "world": await get_news_headlines(sector="World"),
    # }
    # await client.set("headline_news", json.dumps(headlines))


# To run directly
if __name__ == "__main__":
    import asyncio
    asyncio.run(store_data_in_redis())

    # async def test():
    #     REDIS_URL = os.getenv("REDIS_URL")
    #     print(REDIS_URL)
    #     client = redis.from_url(REDIS_URL, decode_responses=True)
    #     x = await client.get("monthly_summary")
    #     print(x)

    # asyncio.run(test())
