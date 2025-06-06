# Tech News Content Creator Agent
# Prerequisites:
# conda create -n autogen python=3.12
# pip install -U autogen-agentchat autogen-ext[web-surfer] 
# playwright install 

import asyncio
import os
from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer


def save_article_to_markdown(article_content, timestamp=None):
    """Save the generated article to a markdown file with timestamp."""
    # Ensure we have content to save
    if not article_content or not article_content.strip():
        print("WARNING: Empty content provided to save_article_to_markdown!")
        return None
        
    print(f"Saving article with length: {len(article_content)} characters")
    
    # Create output directory if it doesn't exist
    os.makedirs("articles", exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"articles/tech_article_{timestamp}.md"
    
    # Write content to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(article_content)
        print(f"Successfully wrote {len(article_content)} characters to {filename}")
        return filename
    except Exception as e:
        print(f"ERROR saving file: {e}")
        
        # Emergency save to current directory
        emergency_file = f"tech_article_emergency_{timestamp}.md"
        try:
            with open(emergency_file, 'w', encoding='utf-8') as f:
                f.write(article_content)
            print(f"Emergency save to {emergency_file}")
            return emergency_file
        except Exception as e2:
            print(f"Emergency save also failed: {e2}")
            return None


async def main() -> None:
    # Using Llama 4 Scout model via Groq
    model_client = OpenAIChatCompletionClient(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        model_info={
            "vision": False,  # Disable vision to avoid image processing issues
            "function_calling": True,
            "json_output": False,
            "family": "unknown",
            "structured_output": True,
            "temperature": 0.7,  # Add some creativity
            "max_tokens": 2000,  # Increase max tokens for longer responses
        },
        base_url="https://api.groq.com/openai/v1",
        api_key="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",
    )
  
    # Set up termination conditions
    termination = MaxMessageTermination(
        max_messages=50) | TextMentionTermination("TERMINATE")  # Increase max messages
    
    # Web surfer agent to find tech news articles
    # Define the news sources to search
    news_sources = [
        "https://techcrunch.com/latest/",
        # "https://www.youtube.com/@Fireship",
        # "https://www.theverge.com/tech",
        # "https://arxiv.org/list/cs.AI/recent"
    ]

    # Create web surfer agent for direct source browsing
    websurfer_agent = MultimodalWebSurfer(
        name="websurfer_agent",
        description="an agent that directly browses multiple tech news sources to find relevant articles",
        model_client=model_client,
        headless=False,  # Set to True to hide the browser window
        start_page=news_sources[0],  # Start with TechCrunch
    )
    
    # Content creator agent that creates engaging content based on tech articles
    content_creator_agent = AssistantAgent(
        name="content_creator_agent",
        description="an agent that creates engaging content based on tech news articles",
        system_message="""You are a tech content creator who specializes in creating engaging articles based on the latest tech news from multiple sources.
        
When presented with tech news articles by the web surfer agent, follow these steps:

1. Analyze content from each source (TechCrunch, The Verge, Arxiv, etc.)
2. Compare and cross-validate information across sources
3. Identify consistent facts and any discrepancies
4. Note the publication date and source credibility for each piece of information
5. Create a well-structured article with:
   - A headline that captures the main story
   - Introduction with key findings and why they matter
   - Body that integrates information from all sources
   - Clear attribution of information to original sources
   - A conclusion with potential implications

Structure your article with proper sections and use markdown formatting for better readability.

When you have created a complete, well-researched article, end with TERMINATE.

Your goal is to synthesize information from multiple sources into a single, coherent, and insightful article that provides more value than any single source alone.""",
        model_client=model_client)

    # Modified coordinator prompt for multi-source research
    selector_prompt = """You are the coordinator of a tech content creation system that researches from multiple sources. The following roles are available:
    {roles}
    
    Given a task:
    1. The websurfer_agent will research the topic from multiple sources including:
       - TechCrunch (for startup and tech industry news)
       - The Verge (for consumer tech and culture)
       - Arxiv (for latest research papers)
       - Other relevant tech news sources
    2. The content_creator_agent will analyze information from all sources and create a comprehensive article
    
    The system must:
    - Gather information from at least 3 different sources
    - Cross-validate facts across sources
    - Present a balanced view when sources disagree
    - Attribute information to original sources
    
    Read the following conversation. Then select the next role from {participants} to play. Only return the role.

    {history}

    Select the next role from {participants} to play. Only return the role.
    """
    
    # Run the task and collect all messages
    all_articles_content = []

    # Process each source
    for source in news_sources:
        print(f"\nSearching {source}...")
        
        # Create a new browser instance for each source
        websurfer_agent = MultimodalWebSurfer(
            name="websurfer_agent",
            description="an agent that directly browses multiple tech news sources to find relevant articles",
            model_client=model_client,
            headless=False,
            start_page=source
        )
        
        # Create a new team for each source
        source_team = SelectorGroupChat(
            [websurfer_agent, content_creator_agent],
            selector_prompt=selector_prompt,
            model_client=model_client, 
            termination_condition=termination
        )
        
        source_task = f"""Visit {source} and find the latest AI-related articles.
        For each article:
        1. Extract the title, date, and main content
        2. Focus on key innovations and developments
        3. Note any industry impact or implications
        
        Format the findings in markdown with proper citations."""

        source_content = []
        collected_message = ""
        
        async for message in source_team.run_stream(task=source_task):
            if message and hasattr(message, 'content'):
                # Handle message.content whether it's a string or a list
                if isinstance(message.content, str):
                    msg_content = message.content
                    collected_message += msg_content
                else:
                    # If it's a list or another type, convert to string
                    msg_content = str(message.content)
                    collected_message += msg_content
                    
                if 'TERMINATE' in str(message.content):
                    if isinstance(message.content, str):
                        content = message.content.split('TERMINATE')[0].strip()
                    else:
                        content = str(message.content)
                    
                    if content:
                        source_content.append(content)
                        print(f"Content collected from {source}")
                    break
        
        # If we didn't get a TERMINATE but collected some messages, save what we have
        if not source_content and collected_message:
            print(f"No TERMINATE found, but saving collected content from {source}")
            source_content.append(collected_message)
        
        # Save each source content directly to a file
        if source_content:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_name = source.split('//')[1].split('/')[0].replace('.', '_')
            filename = save_article_to_markdown(source_content[0], f"{source_name}_{timestamp}")
            if filename:
                print(f"Saved content from {source} to {filename}")
            
            all_articles_content.extend(source_content)
    
    # Create final article from all sources
    print(f"\nCollected {len(all_articles_content)} articles")
    for i, content in enumerate(all_articles_content):
        print(f"\nArticle {i+1} preview: {content[:200]}...")
        
    if all_articles_content:
        # Create a new team for final synthesis with both agents
        synthesis_team = SelectorGroupChat(
            [websurfer_agent, content_creator_agent],
            selector_prompt=selector_prompt,
            model_client=model_client, 
            termination_condition=termination
        )
        
        synthesis_task = """Create a comprehensive article that synthesizes the following content:
        
        {}
        
        Format as a well-structured markdown article with:
        1. Clear sections and headlines
        2. Proper source attribution
        3. Balanced perspective from all sources
        
        When you have finished creating the article, end with 'TERMINATE'.""".format('\n\n'.join(all_articles_content))
        
        print("\nStarting final synthesis...")
        collected_content = ""
        message_count = 0
        max_wait_messages = 10
        
        async for message in synthesis_team.run_stream(task=synthesis_task):
            if message and hasattr(message, 'content'):
                message_count += 1
                print(f"\nReceived message {message_count}: {message.content[:100]}...")
                
                # Append this message's content to our collected content
                collected_content += message.content
                
                # Check for termination keyword
                if 'TERMINATE' in message.content:
                    final_article = message.content.split('TERMINATE')[0].strip()
                    if final_article:
                        print("\nSaving final article with TERMINATE signal...")
                        filename = save_article_to_markdown(final_article)
                        print(f"\nFinal article saved successfully to: {filename}")
                    else:
                        print("\nNo content to save in final article")
                    break
                
                # Force save after waiting for several messages
                if message_count >= max_wait_messages:
                    print("\nForce saving content after waiting for multiple messages...")
                    if collected_content:
                        filename = save_article_to_markdown(collected_content)
                        print(f"\nForce-saved article to: {filename}")
                    else:
                        print("\nNo content to force-save")
                    break

    # Close the web surfer browser when done
    await websurfer_agent.close()

if __name__ == "__main__":
    asyncio.run(main())
