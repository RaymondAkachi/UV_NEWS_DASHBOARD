from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta
from app.db_logic.db import engine
from app.db_logic.models import NewsArticle
import asyncio
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def get_daily_avg_sentiment(days: int = 30, category: str | None = None) -> dict[str, float]:
    """
    Returns a dict mapping date (YYYY-MM-DD) → average sentiment over the last specified days.
    If `category` is provided, only articles in that category are considered.
    Supports days=30 (last 30 days) and days=7 (last 7 days).

    Args:
        days (int): Number of days to look back (e.g., 7 for last week, 30 for last month).
        category (str | None): Optional category filter (e.g., 'business', 'sports').

    Returns:
        dict[str, float]: Dictionary mapping dates (YYYY-MM-DD HH:MM:SS) to average sentiment scores.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    logger.info(
        f"Fetching daily avg sentiment for last {days} days, category: {category}, cutoff: {cutoff}")

    try:
        async with AsyncSession(engine) as session:
            # Define the date_trunc expression once for reuse
            day_trunc = func.date_trunc(
                'day', NewsArticle.pubDate).label("day")
            stmt = (
                select(
                    day_trunc,
                    func.avg(NewsArticle.sentiment).label("avg_sentiment")
                )
                .where(NewsArticle.pubDate >= cutoff)
                .where(NewsArticle.pubDate <= datetime.utcnow())
            )

            if category:
                stmt = stmt.where(NewsArticle.category == category)

            stmt = stmt.group_by(day_trunc).order_by(day_trunc)

            result = await session.execute(stmt)
            rows = result.all()

            logger.info(f"Retrieved {len(rows)} daily sentiment records")

            # Build a date → average map
            return {row.day.strftime("%Y-%m-%d 00:00:00"): float(row.avg_sentiment) for row in rows}
    except Exception as e:
        logger.error(f"Error fetching daily avg sentiment: {str(e)}")
        return {}

if __name__ == "__main__":
    # Overall last-month sentiment
    async def test():
        daily_all = await get_daily_avg_sentiment()
        print(daily_all)

        # Last-month sentiment for “Business”
        # daily_business = await get_daily_avg_sentiment("Business")
        # print(daily_business)
    asyncio.run(test())
