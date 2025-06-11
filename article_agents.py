import asyncio
import logging
import time
import json
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_agentchat.agents import AssistantAgent
from duckduckgo_search import DDGS
from typing import List, Dict
from dataclasses import dataclass
from article_saver import save_to_markdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Add custom sleep function to handle rate limits
def sleep_with_progress(seconds, reason=""):
    """Sleep with a progress indicator in the logs"""
    if reason:
        logging.info(f"{reason} - Waiting for {seconds} seconds...")
    
    interval = 1
    for i in range(0, seconds, interval):
        time.sleep(interval)
        if i % 5 == 0 and i > 0:  # Show progress every 5 seconds
            logging.info(f"Still waiting... {i}/{seconds} seconds elapsed.")
    
    if seconds > interval:
        time.sleep(seconds % interval)  # Sleep the remaining seconds
        
    if reason:
        logging.info(f"Done waiting for {reason}")

@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    published: str

class SearchAgent:
    def __init__(self):
        self.ddgs = DDGS()
    
    def search_topic(self, query: str, max_results: int = 5) -> List[SearchResult]:
        logging.info(f"🔍 Searching for: '{query}' (max results: {max_results})")
        start_time = time.time()
        results = []
        try:
            logging.info("Starting DuckDuckGo news search...")
            for idx, r in enumerate(self.ddgs.news(query, max_results=max_results * 2)):
                url = r.get('url', '')
                if 'msn.com' not in url.lower():  # Filter out msn.com domains
                    result = SearchResult(
                        title=r.get('title', ''),
                        link=url,
                        snippet=r.get('excerpt', ''),
                        published=r.get('published', '')
                    )
                    results.append(result)
                    logging.info(f"  Found article {len(results)}: {result.title[:40]}...")
                    if len(results) >= max_results:  # Stop once we have enough valid results
                        break
                elif idx % 2 == 0:  # Log every few skipped results
                    logging.info(f"  Skipping MSN article: {r.get('title', '')[:40]}...")
        except Exception as e:
            logging.error(f"❌ Error during search: {str(e)}")
        
        search_time = time.time() - start_time
        logging.info(f"✅ Search completed in {search_time:.2f} seconds. Found {len(results)} articles.")
        return results

# Setup API client with rate limiting awareness
model_client = OpenAIChatCompletionClient(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        model_info={
            "vision": True,
            "function_calling": True,
            "json_output": False,
            "family": "unknown",
            "structured_output": True
        },
        base_url="https://api.groq.com/openai/v1",
        api_key="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",
        timeout=60,  # Longer timeout
        max_retries=5  # More retries for rate limits
)

async def main() -> None:
    total_start_time = time.time()
    logging.info("🚀 Starting article processing pipeline")
    
    # Initialize the search agent
    logging.info("Initializing search agent...")
    search_agent = SearchAgent()
    
    # Search for relevant articles with a configurable query
    search_query = "The Illusion of Thinking"  # You can change this to any topic
    max_results = 4  # Reduced from 3 to avoid rate limits
    logging.info(f"Beginning search for topic: '{search_query}' with max_results={max_results}")
    search_results = search_agent.search_topic(search_query, max_results=max_results)
    
    if not search_results:
        logging.warning("❗ No search results found. Exiting.")
        return
    
    # Define the web surfer agent
    logging.info("Initializing web surfer agent...")
    web_surfer_agent = MultimodalWebSurfer(
        name="WebSurfer",
        model_client=model_client,
        headless=False,
        start_page=search_results[0].link if search_results else "https://www.msn.com",
    )

    # Define the summarizer agent with enhanced system message
    summarizer_agent = AssistantAgent(
        name="Summarizer",
        model_client=model_client,
        system_message="""You are a skilled content analyzer and summarizer. Your tasks are:
1. Analyze and summarize the main content from the WebSurfer agent
2. If multiple articles are provided, compare and contrast their key points
3. Highlight any conflicting information or different perspectives
4. Provide a concise, well-structured summary with key findings

Format your response using markdown for better readability."""
    )

    # Define a team with both agents
    agent_team = RoundRobinGroupChat([web_surfer_agent, summarizer_agent], max_turns=6)
    
    # Collection to store article data (including summaries)
    articles_data = []
    
    # Print found articles
    logging.info("\n📋 Found related articles:")
    for article_data_index, result in enumerate(search_results):
        logging.info(f"\n📰 Article {article_data_index + 1}/{len(search_results)}:")
        logging.info(f"   Title: {result.title}")
        logging.info(f"   Link: {result.link}")
        logging.info(f"   Published: {result.published}")
        logging.info("-" * 60)
        
        # Create article data dictionary
        article_data = {
            'title': result.title,
            'link': result.link,
            'published': result.published,
            'summary': ""
        }
        
        # Update web_surfer_agent's start page to current article
        article_start_time = time.time()
        logging.info(f"\n🔍 Analyzing article {article_data_index + 1}/{len(search_results)}: {result.title}")
        logging.info(f"   Resetting web surfer agent and setting start page...")
        
        # Add a delay between articles to avoid rate limits
        if article_data_index > 0:
            sleep_with_progress(30, "Adding delay between articles to avoid rate limits")
        
        web_surfer_agent._page = None  # Reset page to allow new navigation
        web_surfer_agent.start_page = result.link
        
        # Run the team and stream messages to the console
        logging.info(f"   Starting browser navigation and analysis...")
        summary = ""
        task = f"Please visit {result.link} and provide a detailed summary of the article. Include: main points, key findings, and any significant quotes. Published date: {result.published}"
        logging.info(f"   Sending task to agents: {task[:50]}...")
        
        # Try/except to handle API errors
        try:
            stream = agent_team.run_stream(task=task)
        except Exception as e:
            logging.error(f"❌ Error starting agent stream: {str(e)}")
            logging.info("   Will attempt to continue with next article...")
            article_data['summary'] = f"Error processing this article: {str(e)}"
            articles_data.append(article_data)
            continue
        
        # Capture the summary from the summarizer agent
        message_count = 0
        async for msg in stream:
            message_count += 1
            if hasattr(msg, 'source'):
                if msg.source == "WebSurfer":
                    logging.info(f"   💬 WebSurfer is processing... (message {message_count})")
                elif msg.source == "Summarizer":
                    logging.info(f"   📝 Summarizer is generating content... (message {message_count})")
                    summary = msg.content
            
            # Display message content properly instead of using Console.display_message
            if hasattr(msg, 'content') and msg.content:
                content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                source = msg.source if hasattr(msg, 'source') else "Unknown"
                logging.info(f"      Message from {source}: {content_preview}")
            else:
                logging.info(f"      Received message: {str(msg)[:100]}...")
        
        # Add summary to article data
        article_data['summary'] = summary
        articles_data.append(article_data)
        
        article_time = time.time() - article_start_time
        logging.info(f"   ✅ Article processing completed in {article_time:.2f} seconds")

    # Close the browser controlled by the agent
    logging.info("\n🔒 Closing browser session...")
    await web_surfer_agent.close()
    
    # Save all collected data to markdown file
    logging.info("💾 Saving article data to markdown...")
    filename = save_to_markdown(articles_data)
    
    total_time = time.time() - total_start_time
    logging.info(f"\n✅ All done! Article data saved to {filename}")
    logging.info(f"⏱️ Total execution time: {total_time:.2f} seconds")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\n⚠️ Program interrupted by user")
    except Exception as e:
        logging.error(f"❌ Unhandled exception: {str(e)}", exc_info=True)

