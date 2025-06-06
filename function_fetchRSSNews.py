import feedparser
from typing import List
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field

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
if __name__ == "__main__":
    # Test with Engadget RSS feed
    rss_url = "https://www.theverge.com/rss/tech/index.xml"
    news = FetchRSSNews(rss_url)
    
    print("\nLatest tech news from Engadget:")
    for item in news[:3]:  # Show first 3 items
        print(f"\nTitle: {item.title}")
        print(f"Link: {item.link}")
        print(f"Published: {item.published}")
        print(f"Summary: {item.summary[:150]}...")
