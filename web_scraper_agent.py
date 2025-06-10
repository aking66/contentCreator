from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from typing import List, Dict
import json
import asyncio

class WebScraperAgent:
    def _extract_article_text(self, result):
        """
        Extract article text and metadata from web surfer response
        
        Args:
            result: The result object from the web surfer agent
            
        Returns:
            dict: Extracted article data with focus on article text
        """
        try:
            # Initialize structured data dictionary
            article_data = {
                "title": "",
                "author": "",
                "date": "",
                "summary": "",
                "article_text": ""
            }
            
            # Extract raw content from messages
            raw_content = ""
            if hasattr(result, 'messages') and result.messages:
                for msg in result.messages:
                    if hasattr(msg, 'content'):
                        # If content is a list, join all text elements
                        if isinstance(msg.content, list):
                            for item in msg.content:
                                if isinstance(item, str):
                                    raw_content += item + "\n"
                        elif isinstance(msg.content, str):
                            raw_content += msg.content + "\n"
            
            if not raw_content:
                return "No content could be extracted"
                
            # Parse formatted sections from the response
            import re
            
            # Extract title
            title_match = re.search(r'---TITLE---\s*([^\n]+(?:\n[^\n]+)*?)\s*(?:---AUTHOR---|---DATE---|---SUMMARY---|---ARTICLE_TEXT---|$)', raw_content, re.DOTALL)
            if title_match:
                article_data["title"] = title_match.group(1).strip()
            
            # Extract author
            author_match = re.search(r'---AUTHOR---\s*([^\n]+(?:\n[^\n]+)*?)\s*(?:---TITLE---|---DATE---|---SUMMARY---|---ARTICLE_TEXT---|$)', raw_content, re.DOTALL)
            if author_match:
                article_data["author"] = author_match.group(1).strip()
                
            # Extract date
            date_match = re.search(r'---DATE---\s*([^\n]+(?:\n[^\n]+)*?)\s*(?:---TITLE---|---AUTHOR---|---SUMMARY---|---ARTICLE_TEXT---|$)', raw_content, re.DOTALL)
            if date_match:
                article_data["date"] = date_match.group(1).strip()
            
            # Extract summary
            summary_match = re.search(r'---SUMMARY---\s*([^\n]+(?:\n[^\n]+)*?)\s*(?:---TITLE---|---AUTHOR---|---DATE---|---ARTICLE_TEXT---|$)', raw_content, re.DOTALL)
            if summary_match:
                article_data["summary"] = summary_match.group(1).strip()
            
            # Extract article text - most important part
            article_text_match = re.search(r'---ARTICLE_TEXT---\s*([\s\S]*?)(?:---TITLE---|---AUTHOR---|---DATE---|---SUMMARY---|$)', raw_content, re.DOTALL)
            if article_text_match:
                article_data["article_text"] = article_text_match.group(1).strip()
            
            # Fallback: if we couldn't extract via formatting, try to extract the main content
            if not article_data["article_text"]:
                # Try to find paragraph-like content - longer blocks of text
                paragraphs = []
                lines = raw_content.split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for sentences that might be paragraphs
                    if len(line) > 100 and line.count('.') >= 2 and not line.startswith('{') and not line.startswith('"'):
                        paragraphs.append(line)
                
                if paragraphs:
                    article_data["article_text"] = "\n\n".join(paragraphs)
            
            # If we still don't have article text, check for any JSON containing article body
            if not article_data["article_text"]:
                body_match = re.search(r'"articleBody"\s*:\s*"([^"]+)"', raw_content)
                if body_match:
                    article_data["article_text"] = body_match.group(1)
            
            # Clean the extracted data
            import html
            for key in article_data:
                if isinstance(article_data[key], str):
                    # Unescape HTML entities
                    article_data[key] = html.unescape(article_data[key])
                    # Remove escaped quotes and slashes
                    article_data[key] = article_data[key].replace('\"', '"').replace('\\', '')
                    # Remove common artifacts
                    article_data[key] = re.sub(r'\\u[0-9a-fA-F]{4}', lambda m: chr(int(m.group(0)[2:], 16)), article_data[key])
            
            return article_data
        except Exception as e:
            return f"Error extracting article text: {str(e)}"
    def _parse_metadata_from_content(self, raw_content):
        """
        Parse metadata from raw content to extract structured fields
        
        Args:
            raw_content (str): Raw content from web surfer
            
        Returns:
            dict: Extracted structured metadata
        """
        data = {
            "title": "",
            "author": "",
            "date": "",
            "content": "",
            "summary": ""
        }
        
        # Extract title from metadata or text content
        title_patterns = [
            r'"og:title":\s*"([^"]+)"',
            r'"headline":\s*"([^"]+)"',
            r'\[([^\]]+)\]\(https?://[^\)]+\)',  # Markdown link text
            r'<title>([^<]+)</title>'
        ]
        
        for pattern in title_patterns:
            import re
            match = re.search(pattern, raw_content)
            if match:
                data["title"] = match.group(1).strip()
                break
                
        # Extract author information
        author_patterns = [
            r'"author":\s*"([^"]+)"',
            r'"author":\s*\{[^\}]*"name":\s*"([^"]+)"',
            r'"article:author":\s*"([^"]+)"'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, raw_content)
            if match:
                data["author"] = match.group(1).strip()
                break
                
        # Extract publication date
        date_patterns = [
            r'"datePublished":\s*"([^"]+)"',
            r'"article:published_time":\s*"([^"]+)"',
            r'"pubDate":\s*"([^"]+)"'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, raw_content)
            if match:
                data["date"] = match.group(1).strip()
                break
                
        # Extract main content - look for largest text blocks
        # This is simplified but could be enhanced with NLP/content analysis
        content_candidates = []
        lines = raw_content.split('\n')
        current_block = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 100:  # Potential content paragraph
                current_block.append(line)
            elif current_block:
                content_candidates.append('\n'.join(current_block))
                current_block = []
                
        if current_block:
            content_candidates.append('\n'.join(current_block))
            
        # Select largest content block as main content
        if content_candidates:
            data["content"] = max(content_candidates, key=len)
            
        # Try to extract summary from metadata or content
        summary_patterns = [
            r'"og:description":\s*"([^"]+)"',
            r'"description":\s*"([^"]+)"'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, raw_content)
            if match:
                data["summary"] = match.group(1).strip()
                break
                
        return data
        
    def _clean_and_enhance_data(self, data):
        """
        Clean and enhance structured data
        
        Args:
            data (dict): Structured data to clean
            
        Returns:
            dict: Cleaned and enhanced data
        """
        # Remove HTML entities and common escape sequences
        for key in data:
            if isinstance(data[key], str):
                # Replace HTML entities
                import html
                data[key] = html.unescape(data[key])
                
                # Replace escaped quotes
                data[key] = data[key].replace('\"', '"')
                
                # Replace Unicode escapes like \u2019
                import re
                data[key] = re.sub(r'\\u[0-9a-fA-F]{4}', lambda m: chr(int(m.group(0)[2:], 16)), data[key])
                
        # If no summary but we have content, create a summary
        if not data["summary"] and len(data["content"]) > 150:
            data["summary"] = data["content"][:150] + "..."
            
        # Format date consistently if possible
        if data["date"] and data["date"].isdigit():
            # Convert Unix timestamp to human-readable date
            from datetime import datetime
            try:
                timestamp = int(data["date"])
                data["date"] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass  # Keep original if conversion fails
                
        return data
    def _extract_structured_content(self, result):
        """
        Extract structured content from web surfer response and format it consistently
        
        Args:
            result: The result object from the web surfer agent
            
        Returns:
            dict: Extracted structured content with unified format
        """
        try:
            # Initialize structured data dictionary
            structured_data = {
                "title": "",
                "author": "",
                "date": "",
                "content": "",
                "summary": ""
            }
            
            # Extract raw content from messages
            raw_content = ""
            if hasattr(result, 'messages') and result.messages:
                for msg in result.messages:
                    if hasattr(msg, 'content'):
                        # If content is a list, join all text elements
                        if isinstance(msg.content, list):
                            for item in msg.content:
                                if isinstance(item, str):
                                    raw_content += item + "\n"
                        elif isinstance(msg.content, str):
                            raw_content += msg.content + "\n"
            
            if not raw_content:
                return "No content could be extracted"
            
            # Extract metadata from raw content
            structured_data.update(self._parse_metadata_from_content(raw_content))
            
            # Process and enhance the structured data
            structured_data = self._clean_and_enhance_data(structured_data)
            
            return structured_data
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    def __init__(self):
        self.model_client = OpenAIChatCompletionClient(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            model_info={
                "vision": True,
                "function_calling": True,
                "json_output": False,
                "family": "unknown",
                "structured_output": True
            },
            base_url="https://api.groq.com/openai/v1",
            api_key="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"
        )

        # Create the web surfer agent
        self.web_surfer = MultimodalWebSurfer(
            name="web_surfer",
            model_client=self.model_client,
            headless=False,
            start_page="about:blank"
        )

    async def scrape_url(self, url: str) -> Dict:
        """
        Scrape content from a given URL using MultimodalWebSurfer
        
        Args:
            url (str): The URL to scrape
            
        Returns:
            Dict: Dictionary containing scraped information
        """
        try:
            # Create a team with just the web surfer agent
            agent_team = RoundRobinGroupChat([self.web_surfer], max_turns=3)
            
            # Create the prompt to visit URL and extract information with focus on article text
            prompt = f"""Visit this URL: {url}
            Once you've accessed the page, please extract the following in order of importance:
            
            1. MAIN ARTICLE TEXT: Extract the full text of the main article content (this is the most important)
            2. Article title
            3. Author name
            4. Publication date
            5. Brief summary (1-2 sentences)
            
            FORMAT YOUR RESPONSE LIKE THIS:
            ---TITLE---
            [Article title here]
            
            ---AUTHOR---
            [Author name here]
            
            ---DATE---
            [Publication date here]
            
            ---SUMMARY---
            [Brief summary here]
            
            ---ARTICLE_TEXT---
            [Full article text here]
            
            Focus on getting the actual article text - not metadata, not JSON, not HTML - just the readable article text that a human would want to read."""

            # Run the team with the prompt
            result = await agent_team.run(task=prompt)
            
            # Process the response
            response = self._extract_article_text(result)

            # Process and structure the response
            if isinstance(response, dict):
                # Add URL to the structured data
                response["url"] = url
                response["success"] = True
                return response
            elif response:
                return {
                    "url": url,
                    "raw_content": response,
                    "success": True
                }
            return {
                "url": url,
                "error": "No content extracted",
                "success": False
            }

        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "success": False
            }

    async def scrape_multiple_urls(self, urls: List[str]) -> List[Dict]:
        """
        Scrape content from multiple URLs
        
        Args:
            urls (List[str]): List of URLs to scrape
            
        Returns:
            List[Dict]: List of dictionaries containing scraped information
        """
        results = []
        for url in urls:
            result = await self.scrape_url(url)
            results.append(result)
        return results


# Example usage
if __name__ == "__main__":
    import asyncio
    from search_agent import SearchAgent
    import json
    
    async def main():
        try:
            # First use search agent to get URLs
            search_agent = SearchAgent()
            search_results = search_agent.search_topic("The Illusion of Thinking", max_results=2)
            print(f"\n🔍 Found {len(search_results)} search results\n")
            
            # Then use web scraper to get content
            scraper = WebScraperAgent()
            urls = [result.link for result in search_results]
            scraped_content = await scraper.scrape_multiple_urls(urls)
            
            # Print results in a structured format
            for i, content in enumerate(scraped_content, 1):
                print(f"\n📄 Article {i}: {content['url']}")
                print("-" * 80)
                
                if not content["success"]:
                    print(f"❌ Error: {content.get('error', 'Unknown error')}")
                    continue
                    
                if "title" in content and content["title"]:
                    print(f"📌 Title: {content['title']}")
                
                if "author" in content and content["author"]:
                    print(f"👤 Author: {content['author']}")
                    
                if "date" in content and content["date"]:
                    print(f"📅 Date: {content['date']}")
                    
                if "summary" in content and content["summary"]:
                    print(f"\n📋 Summary:\n{content['summary']}")
                
                if "content" in content and content["content"]:
                    # Show a preview of the content (first 200 chars)
                    content_preview = content["content"][:200] + "..." if len(content["content"]) > 200 else content["content"]
                    print(f"\n📝 Content (preview):\n{content_preview}")
                
                # Save full content to JSON file for reference
                filename = f"article_{i}_content.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(content, f, ensure_ascii=False, indent=4)
                print(f"\n💾 Full article data saved to {filename}")
                
                print("-" * 80)
        finally:
            # Make sure to close the browser when done
            if 'scraper' in locals() and scraper.web_surfer:
                await scraper.web_surfer.close()
    
    asyncio.run(main())
