from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.db_logic.db import engine
from app.db_logic.models import NewsArticle
import asyncio


async def get_daily_avg_sentiment(days: int = 30, category: str | None = None) -> dict[str, float]:
    """
    Returns a dict mapping date (YYYY-MM-DD) → average sentiment over the last 30 days.
    If `category` is provided, only articles in that category are considered.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    async with AsyncSession(engine) as session:
        stmt = (
            select(
                func.date(NewsArticle.pubDate).label("day"),
                func.avg(NewsArticle.sentiment).label("avg_sentiment")
            )
            .where(NewsArticle.pubDate >= cutoff)
        )

        if category:
            stmt = stmt.where(NewsArticle.category == category)

        stmt = stmt.group_by(func.date(NewsArticle.pubDate)) \
                   .order_by(func.date(NewsArticle.pubDate))

        result = await session.execute(stmt)
        rows = result.all()

    # Build a date → average map
    return {row.day.strftime("%Y-%m-%d %H:%M:%S"): float(row.avg_sentiment) for row in rows}

if __name__ == "__main__":
    # Overall last-month sentiment
    async def test():
        daily_all = await get_daily_avg_sentiment()
        print(daily_all)

        # Last-month sentiment for “Business”
        # daily_business = await get_daily_avg_sentiment("Business")
        # print(daily_business)
    asyncio.run(test())
