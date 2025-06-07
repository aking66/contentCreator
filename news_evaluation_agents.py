import autogen
from typing import Dict, Any, List
import json

# Configure model settings
config_list = [{
    "model": "mistral:7b-instruct",
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
}]

# Base configuration for agents
llm_config = {
    "config_list": config_list,
    "temperature": 0.7,
}

# Agent configurations
tech_relevance_agent = autogen.AssistantAgent(
    name="tech_relevance_agent",
    system_message="""You are a tech relevance evaluator. Analyze news items for:
    - Major tech company involvement
    - Emerging technology relevance
    - Significant product releases
    Score from 1-5 and justify briefly. Output in JSON format:
    {"score": <1-5>, "justification": "<brief explanation>"}""",
    llm_config=llm_config
)

market_impact_agent = autogen.AssistantAgent(
    name="market_impact_agent",
    system_message="""You are a market impact evaluator. Analyze news items for:
    - Market influence
    - User base impact
    - Developer community effects
    Score from 1-5 and justify briefly. Output in JSON format:
    {"score": <1-5>, "justification": "<brief explanation>"}""",
    llm_config=llm_config
)

trending_agent = autogen.AssistantAgent(
    name="trending_agent",
    system_message="""You are a trending topic evaluator. Analyze news items for:
    - Social media presence
    - Tech forum discussions
    - Overall buzz
    Score from 1-5 and justify briefly. Output in JSON format:
    {"score": <1-5>, "justification": "<brief explanation>"}""",
    llm_config=llm_config
)

final_decision_agent = autogen.AssistantAgent(
    name="final_decision_agent",
    system_message="""You are the final decision maker. Collect all agent scores and:
    1. Calculate average score
    2. Make recommendation (Write/Skip) based on 3.0 threshold
    3. Provide summary
    Output in JSON format:
    {
        "scores": {
            "tech_relevance": <score>,
            "market_impact": <score>,
            "trending": <score>
        },
        "average_score": <avg>,
        "recommendation": "<Write/Skip>",
        "summary": "<brief summary>"
    }""",
    llm_config=llm_config
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={"work_dir": "coding", "use_docker": False},
    llm_config=llm_config
)

def evaluate_news_item(news_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a news item using the agent group.
    
    Args:
        news_item: Dictionary containing news information (title, content, etc.)
        
    Returns:
        Dictionary containing the final evaluation results
    """
    # Convert news item to string format for agents
    news_text = f"Title: {news_item.get('title', '')}\nContent: {news_item.get('content', '')}"
    
    # Initialize chat for tech relevance evaluation
    user_proxy.initiate_chat(
        tech_relevance_agent,
        message=f"Please evaluate this news item for tech relevance:\n{news_text}"
    )
    
    # Get tech relevance score
    tech_score = json.loads(user_proxy.last_message()["content"])
    
    # Evaluate market impact
    user_proxy.initiate_chat(
        market_impact_agent,
        message=f"Please evaluate this news item for market impact:\n{news_text}"
    )
    
    # Get market impact score
    market_score = json.loads(user_proxy.last_message()["content"])
    
    # Evaluate trending potential
    user_proxy.initiate_chat(
        trending_agent,
        message=f"Please evaluate this news item for trending potential:\n{news_text}"
    )
    
    # Get trending score
    trending_score = json.loads(user_proxy.last_message()["content"])
    
    # Make final decision
    final_input = {
        "tech_relevance": tech_score,
        "market_impact": market_score,
        "trending": trending_score,
    }
    
    user_proxy.initiate_chat(
        final_decision_agent,
        message=f"Please make a final decision based on these evaluations:\n{json.dumps(final_input, indent=2)}"
    )
    
    # Get final decision
    final_decision = json.loads(user_proxy.last_message()["content"])
    return final_decision

# Example usage
if __name__ == "__main__":
    # Example news item
    sample_news = {
        "title": "OpenAI Releases GPT-5 with Groundbreaking Capabilities",
        "content": "OpenAI has announced the release of GPT-5, featuring significant improvements in reasoning and multimodal capabilities. The new model shows unprecedented performance across various benchmarks."
    }
    
    result = evaluate_news_item(sample_news)
    print("Final Evaluation:")
    print(json.dumps(result, indent=2))
