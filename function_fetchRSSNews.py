import feedparser
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field
from rss_feeds import RSS_FEEDS, get_feeds_by_category

class NewsItem(BaseModel):
    title: str = Field(default="")
    link: HttpUrl
    published: str = Field(default="")
    summary: str = Field(default="")

def FetchRSSNews(rss_url: str) -> List[NewsItem]:
    """
    Fetch and parse an RSS feed, returning a list of news items.
    
    Args:
        rss_url (str): URL of the RSS feed to fetch
        
    Returns:
        List[NewsItem]: List of news items, each containing title, link, published date, and summary
    """
    try:
        # Parse the RSS feed
        feed = feedparser.parse(rss_url)
        
        # Extract news items
        news_items = []
        for entry in feed.entries:
            try:
                news_item = NewsItem(
                    title=entry.get('title', ''),
                    link=entry.get('link', ''),
                    published=entry.get('published', ''),
                    summary=entry.get('summary', '')
                )
                news_items.append(news_item)
            except Exception as e:
                print(f"Error parsing news item: {str(e)}")
                continue
            
        return news_items
        
    except Exception as e:
        print(f"Error fetching RSS feed: {str(e)}")
        return []

# Example usage
async def fetch_rss_news(category: str, limit: int = None) -> List[Dict[str, Any]]:
    """
    Fetch news from RSS feeds based on category
    
    Args:
        category (str): Category of news to fetch ('arabic', 'international', 'general', 'reddit', 'all')
        limit (int, optional): Maximum number of feeds to process
        
    Returns:
        List[Dict[str, Any]]: List of news items
    """
    feeds = get_feeds_by_category(category) if category != "all" else RSS_FEEDS
    if limit:
        feeds = feeds[:limit]
        
    all_news = []
    for feed_url in feeds:
        try:
            news_items = FetchRSSNews(feed_url)
            all_news.extend(news_items)
        except Exception as e:
            print(f"Error fetching from {feed_url}: {str(e)}")
            continue
            
    return [news.model_dump() for news in all_news]

if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Test fetching international news with limit of 2 feeds
        print("Fetching international news...")
        news = await fetch_rss_news(category="international", limit=2)
        print(f"Found {len(news)} articles")
        for item in news[:3]:  # Show first 3 articles
            print(f"\nTitle: {item['title']}")
            print(f"Link: {item['link']}")
            print(f"Published: {item['published']}")
        
        # Test fetching Arabic news
        print("\n\nFetching Arabic news...")
        news = await fetch_rss_news(category="arabic", limit=2)
        print(f"Found {len(news)} articles")
        for item in news[:3]:  # Show first 3 articles
            print(f"\nTitle: {item['title']}")
            print(f"Link: {item['link']}")
            print(f"Published: {item['published']}")
    
    # Run the async main function
    asyncio.run(main())
