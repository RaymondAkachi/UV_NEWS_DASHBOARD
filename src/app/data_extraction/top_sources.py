from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import asyncio

from app.db_logic.db import engine
from app.db_logic.models import NewsArticle


async def get_top_sources_with_avg_sentiment(days: int = 30, category: str | None = None):
    """
    Returns the top 5 sources by article count over the past `days`,
    along with their average sentiment scores.

    Optionally filtered by `category`.
    """
    cutoff = datetime.utcnow() - timedelta(days=float(days))

    async with AsyncSession(engine) as session:
        stmt = (
            select(
                NewsArticle.source_id,
                func.count(NewsArticle.id).label("article_count"),
                func.avg(NewsArticle.sentiment).label("avg_sentiment")
            )
            .where(NewsArticle.pubDate >= cutoff)
        )

        if category:
            stmt = stmt.where(NewsArticle.category == category)

        stmt = stmt.group_by(NewsArticle.source_id) \
                   .order_by(func.count(NewsArticle.id).desc()) \
                   .limit(10)

        result = await session.execute(stmt)
        top_sources = result.all()

    return [
        {
            "source": source_id,
            "article_count": count,
            "avg_sentiment": round(sentiment, 4)
        }
        for source_id, count, sentiment in top_sources
    ]

if __name__ == "__main__":
    x = asyncio.run(get_top_sources_with_avg_sentiment(
        days=30))
    print(x)
