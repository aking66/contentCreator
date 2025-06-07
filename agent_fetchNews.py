import asyncio
from typing import List, Dict, Any
from pydantic import BaseModel
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
from function_fetchRSSNews import FetchRSSNews, NewsItem
from rss_feeds import RSS_FEEDS, get_feeds_by_category

# Configuration for the agents
config_list = [
    {
        "model": "mistral:7b-instruct",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]



# Create the news assistant agent
news_assistant = AssistantAgent(
    name="news_assistant",
    system_message="""You are a helpful news assistant that can fetch and analyze news from RSS feeds. 
    You can fetch news from specific categories: 'arabic', 'international', 'general', or 'reddit'.
    When presenting news, format them in a clear and readable way with titles and summaries.
    You can specify how many news sources to fetch from using the limit parameter.""",
    llm_config={
        "config_list": config_list,
        "functions": [
            {
                "name": "fetch_rss_news",
                "description": "Fetch news from RSS feeds by category",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["arabic", "international", "general", "reddit", "all"],
                            "description": "Category of news to fetch"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of feeds to fetch from (default: all feeds in category)"
                        }
                    },
                    "required": ["category"]
                }
            }
        ]
    }
)

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
            
    return [news.dict() for news in all_news]

def format_news_items(news_items: List[Dict[str, Any]]) -> str:
    """
    Format news items into a readable string
    """
    result = ""
    for item in news_items:
        result += f"Title: {item['title']}\n"
        result += f"Link: {item['link']}\n"
        if item['published']:
            result += f"Published: {item['published']}\n"
        if item['summary']:
            result += f"Summary: {item['summary']}\n"
        result += "-" * 50 + "\n"
    return result

# Create the user proxy agent
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    code_execution_config={"work_dir": ".", "use_docker": False},
    function_map={"fetch_rss_news": fetch_rss_news}
)

def format_news_items(news_items: List[NewsItem]) -> str:
    """Format news items into a readable string"""
    result = "\nLatest News:\n" + "=" * 50 + "\n"
    for i, item in enumerate(news_items, 1):
        result += f"\n{i}. {item.title}\n"
        result += f"   Published: {item.published}\n"
        result += f"   Link: {item.link}\n"
        result += f"   Summary: {item.summary[:150]}...\n"
        result += "-" * 50 + "\n"
    return result

async def main():
    # Start the conversation
    await user_proxy.initiate_chat(
        news_assistant,
        message="Fetch and show me the latest Arabic tech news"
    )
    

if __name__ == "__main__":
    asyncio.run(main())
