from duckduckgo_search import DDGS
from typing import List
from dataclasses import dataclass
from datetime import datetime

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
        """
        Search for a specific topic and return the latest results
        
        Args:
            query (str): The search query
            max_results (int): Maximum number of results to return (default: 5)
            
        Returns:
            List[SearchResult]: List of search results containing title, link, snippet and published date
        """
        results = []
        try:
            # Use DuckDuckGo news search to get latest results
            for r in self.ddgs.news(query, max_results=max_results):
                result = SearchResult(
                    title=r.get('title', ''),
                    link=r.get('url', ''),
                    snippet=r.get('excerpt', ''),
                    published=r.get('published', '')
                )
                results.append(result)
                
        except Exception as e:
            print(f"Error during search: {str(e)}")
            
        return results

# Example usage
if __name__ == "__main__":
    agent = SearchAgent()
    # Example search for AI news
    results = agent.search_topic("artificial intelligence news")
    
    for result in results:
        print(f"\nTitle: {result.title}")
        print(f"Link: {result.link}")
        print(f"Snippet: {result.snippet}")
        print(f"Published: {result.published}")
        print("-" * 50)
