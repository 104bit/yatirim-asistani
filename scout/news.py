import feedparser
from datetime import datetime
from typing import List
import urllib.parse
from .models import NewsItem

def fetch_news(query: str) -> List[NewsItem]:
    """
    Fetches news from Google News RSS feed for the given query.
    """
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=tr&gl=TR&ceid=TR:tr"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    for entry in feed.entries:
        # Extract fields
        title = entry.title
        link = entry.link
        published = entry.published_parsed
        source = entry.source.title if 'source' in entry else "Unknown"
        summary = entry.summary if 'summary' in entry else ""
        
        # Parse timestamp
        timestamp = datetime(*published[:6]) if published else datetime.now()
        
        news_item = NewsItem(
            title=title,
            timestamp=timestamp,
            source=source,
            snippet=summary
        )
        news_items.append(news_item)
        
    return news_items
