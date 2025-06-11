import asyncio
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_agentchat.agents import AssistantAgent
from duckduckgo_search import DDGS
from typing import List
from dataclasses import dataclass

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
        results = []
        try:
            for r in self.ddgs.news(query, max_results=max_results * 2):  # Fetch more results since we'll filter some out
                url = r.get('url', '')
                if 'msn.com' not in url.lower():  # Filter out msn.com domains
                    result = SearchResult(
                        title=r.get('title', ''),
                        link=url,
                        snippet=r.get('excerpt', ''),
                        published=r.get('published', '')
                    )
                    results.append(result)
                    if len(results) >= max_results:  # Stop once we have enough valid results
                        break
        except Exception as e:
            print(f"Error during search: {str(e)}")
        return results

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
        
)

async def main() -> None:
    # Initialize the search agent
    search_agent = SearchAgent()
    
    # Search for relevant articles
    search_results = search_agent.search_topic("The Illusion of Thinking", max_results=3)
    
    # Define the web surfer agent
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
    
    # Print found articles
    print("\nFound related articles:")
    for result in search_results:
        print(f"\nTitle: {result.title}")
        print(f"Link: {result.link}")
        print(f"Published: {result.published}")
        print("-" * 50)
        
        # Update web_surfer_agent's start page to current article
        web_surfer_agent._page = None  # Reset page to allow new navigation
        web_surfer_agent.start_page = result.link
        
        # Run the team and stream messages to the console
        print(f"\nAnalyzing article: {result.title}")
        stream = agent_team.run_stream(
            task=f"Please visit {result.link} and provide a detailed summary of the article. Include: main points, key findings, and any significant quotes. Published date: {result.published}"
        )
        await Console(stream)

    # Close the browser controlled by the agent
    await web_surfer_agent.close()

asyncio.run(main())

