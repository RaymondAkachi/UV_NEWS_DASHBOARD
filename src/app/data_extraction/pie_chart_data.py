from sqlalchemy import func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import asyncio

from app.db_logic.db import engine
from app.db_logic.models import NewsArticle


async def get_sentiment_pie_data(days: int = 30, category: str | None = None) -> dict:
    """
    Returns a dictionary with sentiment class counts over the past `days`,
    optionally filtered by category.

    Categories:
        - good: sentiment > 0.4
        - okay: -0.4 <= sentiment <= 0.4
        - bad: sentiment < -0.4
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

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
        )

        if category:
            stmt = stmt.where(NewsArticle.category == category)

        result = await session.execute(stmt)
        good, bad, okay = result.one()

    return {
        "good": good or 0,
        "okay": okay or 0,
        "bad": bad or 0
    }

if __name__ == "__main__":
    async def test():
        data = await get_sentiment_pie_data(days=30)
        print(data)
        # News sentiment for "Business" category this week
        data = await get_sentiment_pie_data(days=7, category="Business")
        print(data)

    asyncio.run(test())
