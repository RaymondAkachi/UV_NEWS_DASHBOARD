import feedparser


async def get_news_headlines(sector=None | str):
    link = "https://news.google.com/rss?hl=en-US&gl=NG&ceid=US:en"
    if sector:
        sector = sector.lower()
        # if sector not in ["business", "world", "sports", "sci/tech"]:
        #     return []
        link = f"https://news.google.com/rss/search?q={sector}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(link)
    top_headlines = []

    for entry in feed.entries[:10]:  # Get top 5
        top_headlines.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,  # Example: 'Mon, 24 Jun 2025 07:34:00 GMT'
            "summary": entry.summary,
            # fallback
            "source": entry.get("source", {}).get("title", "Google News"),
        })
    return top_headlines


if __name__ == "__main__":
    import asyncio

    async def func():
        x = await get_news_headlines("Sports")
        print(x)
    asyncio.run(func())
