from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import asyncio
import logging

from app.db_logic.db import engine
from app.db_logic.models import NewsArticle

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def get_top_sources_with_avg_sentiment(days: int = 30, category: str | None = None) -> list[dict]:
    """
    Returns the top 10 sources by article count over the past `days`,
    along with their average sentiment scores, optionally filtered by `category`.

    Args:
        days (int): Number of days to look back (e.g., 7 for last week, 30 for last month).
        category (str | None): Optional category filter (e.g., 'business', 'sports').

    Returns:
        list[dict]: List of dictionaries with keys:
            - source: Source ID (str)
            - article_count: Number of articles (int)
            - avg_sentiment: Average sentiment score (float, rounded to 4 decimal places)
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    logger.info(
        f"Fetching top sources for last {days} days, category: {category}, cutoff: {cutoff}")

    try:
        async with AsyncSession(engine) as session:
            stmt = (
                select(
                    NewsArticle.source_id,
                    func.count(NewsArticle.id).label("article_count"),
                    func.avg(NewsArticle.sentiment).label("avg_sentiment")
                )
                .where(NewsArticle.pubDate >= cutoff)
                .where(NewsArticle.pubDate <= datetime.utcnow())
            )

            if category:
                stmt = stmt.where(NewsArticle.category == category)

            stmt = stmt.group_by(NewsArticle.source_id) \
                       .order_by(func.count(NewsArticle.id).desc()) \
                       .limit(10)

            result = await session.execute(stmt)
            top_sources = result.all()

            logger.info(f"Retrieved {len(top_sources)} top sources")

            return [
                {
                    "source": source_id if source_id else "Unknown",
                    "article_count": int(count),
                    "avg_sentiment": round(float(sentiment), 4) if sentiment is not None else 0.0
                }
                for source_id, count, sentiment in top_sources
            ]
    except Exception as e:
        logger.error(f"Error fetching top sources: {str(e)}")
        return []

if __name__ == "__main__":
    x = asyncio.run(get_top_sources_with_avg_sentiment(
        days=30))
    print(x)
