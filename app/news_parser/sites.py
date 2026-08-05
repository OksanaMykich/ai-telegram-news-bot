from datetime import datetime

import feedparser


def parse_rss_feed(source_name: str, feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)

    news_items = []

    for entry in feed.entries:
        published_at = datetime.utcnow()

        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_at = datetime(*entry.published_parsed[:6])

        news_items.append(
            {
                "title": entry.get("title", ""),
                "url": entry.get("link"),
                "summary": entry.get("summary", ""),
                "source": source_name,
                "published_at": published_at,
                "raw_text": entry.get("summary", ""),
            }
        )

    return news_items

