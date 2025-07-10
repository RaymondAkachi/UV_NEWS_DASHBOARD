from sqlalchemy import func, case
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


async def get_sentiment_pie_data(days: int = 30, category: str | None = None) -> dict:
    """
    Returns a dictionary with sentiment class counts over the past `days`,
    optionally filtered by category.

    Categories:
        - good: sentiment > 0.4
        - okay: -0.4 <= sentiment <= 0.4
        - bad: sentiment < -0.4

    Args:
        days (int): Number of days to look back (e.g., 7 for last week, 30 for last month).
        category (str | None): Optional category filter (e.g., 'business', 'sports').

    Returns:
        dict: {"good": int, "okay": int, "bad": int} with counts of articles in each sentiment category.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    logger.info(
        f"Fetching pie chart data for last {days} days, category: {category}, cutoff: {cutoff}")

    try:
        async with AsyncSession(engine) as session:
            stmt = (
                select(
                    func.sum(case((NewsArticle.sentiment > 0.4, 1), else_=0)).label(
                        "good"),
                    func.sum(case((NewsArticle.sentiment < -0.4, 1),
                             else_=0)).label("bad"),
                    func.sum(case(
                        ((NewsArticle.sentiment >= -0.4) &
                         (NewsArticle.sentiment <= 0.4), 1),
                        else_=0
                    )).label("okay")
                )
                .where(NewsArticle.pubDate >= cutoff)
                .where(NewsArticle.pubDate <= datetime.utcnow())
            )

            if category:
                stmt = stmt.where(NewsArticle.category == category)

            result = await session.execute(stmt)
            row = result.one()
            good, bad, okay = row.good or 0, row.bad or 0, row.okay or 0

            logger.info(
                f"Pie chart data retrieved: good={good}, okay={okay}, bad={bad}")

            return {
                "good": int(good),
                "okay": int(okay),
                "bad": int(bad)
            }
    except Exception as e:
        logger.error(f"Error fetching pie chart data: {str(e)}")
        return {"good": 0, "okay": 0, "bad": 0}

if __name__ == "__main__":
    async def test():
        data = await get_sentiment_pie_data(days=30)
        print(data)
        # News sentiment for "Business" category this week
        data = await get_sentiment_pie_data(days=7, category="Business")
        print(data)

    asyncio.run(test())
