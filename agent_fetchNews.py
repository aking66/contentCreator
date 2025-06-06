import asyncio
from typing import List, Dict, Any
from pydantic import BaseModel
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
from function_fetchRSSNews import FetchRSSNews, NewsItem

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
    You can use the fetch_rss_news function to get news from any RSS feed URL.
    When presenting news, format them in a clear and readable way.""",
    llm_config={
        "config_list": config_list,
        "functions": [
            {
                "name": "fetch_rss_news",
                "description": "Fetch news from an RSS feed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "rss_url": {
                            "type": "string",
                            "description": "URL of the RSS feed"
                        }
                    },
                    "required": ["rss_url"]
                }
            }
        ]
    }
)

# Create the user proxy agent
user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    code_execution_config={"work_dir": ".", "use_docker": False},
    function_map={"fetch_rss_news": FetchRSSNews}
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
    # Initial message to start the conversation
    initial_message = "Please fetch and analyze the latest tech news from The Verge (https://www.theverge.com/rss/tech/index.xml)"
    
    # Start the conversation
    await user_proxy.a_initiate_chat(
        news_assistant,
        message=initial_message
    )

if __name__ == "__main__":
    asyncio.run(main())
