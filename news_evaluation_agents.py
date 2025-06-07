import autogen
from typing import Dict, Any, List
import json
import re
from pydantic import BaseModel
import asyncio
from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat.conversable_agent import ConversableAgent

# Pydantic models for structured output
class TechRelevanceScore(BaseModel):
    score: int
    justification: str

class MarketImpactScore(BaseModel):
    score: int
    justification: str

class TrendingScore(BaseModel):
    score: int
    justification: str

class FinalDecision(BaseModel):
    tech_relevance_score: int
    market_impact_score: int
    trending_score: int
    average_score: float
    recommendation: str
    summary: str

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

class NewsEvaluationTeam:
    def __init__(self):
        self.llm_config = llm_config
        
        # Initialize agents
        self.tech_relevance_agent = AssistantAgent(
            name="tech_relevance_agent",
            system_message="""You are a tech relevance evaluator. Analyze news items for:
            - Major tech company involvement
            - Emerging technology relevance
            - Significant product releases
            Score from 1-5 and justify briefly.
            Output in JSON format:
            {"score": <1-5>, "justification": "<brief explanation>"}
            """,
            llm_config=self.llm_config
        )

        self.market_impact_agent = AssistantAgent(
            name="market_impact_agent",
            system_message="""You are a market impact evaluator. Analyze news items for:
            - Market influence
            - User base impact
            - Developer community effects
            Score from 1-5 and justify briefly.
            Output in JSON format:
            {"score": <1-5>, "justification": "<brief explanation>"}
            """,
            llm_config=self.llm_config
        )

        self.trending_agent = AssistantAgent(
            name="trending_agent",
            system_message="""You are a trending topic evaluator. Analyze news items for:
            - Social media presence
            - Tech forum discussions
            - Overall buzz
            Score from 1-5 and justify briefly.
            Output in JSON format:
            {"score": <1-5>, "justification": "<brief explanation>"}
            """,
            llm_config=self.llm_config
        )

        self.final_decision_agent = AssistantAgent(
            name="final_decision_agent",
            system_message="""You are the final decision maker. Collect all agent scores and:
            1. Calculate average score
            2. Make recommendation (Write/Skip) based on 3.0 threshold
            3. Provide summary
            Output in JSON format:
            {
                "tech_relevance_score": <score>,
                "market_impact_score": <score>,
                "trending_score": <score>,
                "average_score": <avg>,
                "recommendation": "<Write/Skip>",
                "summary": "<brief summary>"
            }
            """,
            llm_config=self.llm_config
        )
        
        self.user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={"work_dir": "coding", "use_docker": False},
            llm_config=self.llm_config
        )

    def evaluate_news_item(self, news_item: Dict[str, Any]) -> FinalDecision:
        """
        Args:
            news_item: Dictionary containing news information (title, content, etc.)
            
        Returns:
            FinalDecision object containing the evaluation results
        """
        # Convert news item to string format for agents
        news_text = f"Title: {news_item.get('title', '')}\nContent: {news_item.get('content', '')}"
        
        print("\n===== TECH RELEVANCE EVALUATION =====\n")
        # Get tech relevance score
        tech_chat = self.user_proxy.initiate_chat(
            self.tech_relevance_agent,
            message=f"Please evaluate this news item for tech relevance:\n{news_text}\nRespond ONLY with a JSON object in this format: {{\"score\": <1-5>, \"justification\": \"<brief explanation>\"}}.",
            max_turns=2
        )
        
        # Extract the JSON response from the last message
        tech_response = tech_chat.chat_history[-1]["content"]
        print(f"Tech Relevance Response: {tech_response}")
        
        # Extract JSON from the response using regex - more flexible pattern
        json_match = re.search(r'\{\s*"score"\s*:\s*(\d+)\s*,\s*"justification"\s*:\s*"([^"]*)"\s*\}', tech_response)
        if json_match:
            score = int(json_match.group(1))
            justification = json_match.group(2)
            tech_score = TechRelevanceScore(score=score, justification=justification)
        else:
            # Fallback to creating a default object if JSON extraction fails
            print("Warning: Could not extract valid JSON from tech relevance response")
            tech_score = TechRelevanceScore(score=3, justification="JSON extraction failed")
        print(f"Tech Score: {tech_score.score}, Justification: {tech_score.justification}")
        
        print("\n===== MARKET IMPACT EVALUATION =====\n")
        # Get market impact score
        market_chat = self.user_proxy.initiate_chat(
            self.market_impact_agent,
            message=f"Please evaluate this news item for market impact:\n{news_text}\nRespond ONLY with a JSON object in this format: {{\"score\": <1-5>, \"justification\": \"<brief explanation>\"}}.",
            max_turns=2
        )
        
        # Extract the JSON response from the last message
        market_response = market_chat.chat_history[-1]["content"]
        print(f"Market Impact Response: {market_response}")
        
        # Extract JSON from the response using regex - more flexible pattern
        json_match = re.search(r'\{\s*"score"\s*:\s*(\d+)\s*,\s*"justification"\s*:\s*"([^"]*)"\s*\}', market_response)
        if json_match:
            score = int(json_match.group(1))
            justification = json_match.group(2)
            market_score = MarketImpactScore(score=score, justification=justification)
        else:
            # Fallback to creating a default object if JSON extraction fails
            print("Warning: Could not extract valid JSON from market impact response")
            market_score = MarketImpactScore(score=3, justification="JSON extraction failed")
        print(f"Market Score: {market_score.score}, Justification: {market_score.justification}")
        
        print("\n===== TRENDING EVALUATION =====\n")
        # Get trending score
        trending_chat = self.user_proxy.initiate_chat(
            self.trending_agent,
            message=f"Please evaluate this news item for trending potential:\n{news_text}\nRespond ONLY with a JSON object in this format: {{\"score\": <1-5>, \"justification\": \"<brief explanation>\"}}.",
            max_turns=2
        )
        
        # Extract the JSON response from the last message
        trending_response = trending_chat.chat_history[-1]["content"]
        print(f"Trending Response: {trending_response}")
        
        # Extract JSON from the response using regex - more flexible pattern
        json_match = re.search(r'\{\s*"score"\s*:\s*(\d+)\s*,\s*"justification"\s*:\s*"([^"]*)"\s*\}', trending_response)
        if json_match:
            score = int(json_match.group(1))
            justification = json_match.group(2)
            trending_score = TrendingScore(score=score, justification=justification)
        else:
            # Fallback to creating a default object if JSON extraction fails
            print("Warning: Could not extract valid JSON from trending response")
            trending_score = TrendingScore(score=3, justification="JSON extraction failed")
        print(f"Trending Score: {trending_score.score}, Justification: {trending_score.justification}")
        
        print("\n===== FINAL DECISION =====\n")
        # Get final decision
        final_input = {
            "tech_relevance": {"score": tech_score.score, "justification": tech_score.justification},
            "market_impact": {"score": market_score.score, "justification": market_score.justification},
            "trending": {"score": trending_score.score, "justification": trending_score.justification},
        }
        
        final_chat = self.user_proxy.initiate_chat(
            self.final_decision_agent,
            message=f"Please make a final decision based on these evaluations:\n{json.dumps(final_input, indent=2)}\nRespond ONLY with a JSON object in this format: {{\"tech_relevance_score\": <score>, \"market_impact_score\": <score>, \"trending_score\": <score>, \"average_score\": <avg>, \"recommendation\": \"<Write/Skip>\", \"summary\": \"<brief summary>\"}}.",
            max_turns=2
        )
        
        # Extract the JSON response from the last message
        final_response = final_chat.chat_history[-1]["content"]
        print(f"Final Decision Response: {final_response}")
        
        # For the final decision, we'll just calculate it ourselves since the JSON extraction is complex
        # and the agent responses are inconsistent
        print("Calculating final decision based on individual scores")
        avg_score = (tech_score.score + market_score.score + trending_score.score) / 3
        recommendation = "Write" if avg_score >= 3 else "Skip"
        final_decision = FinalDecision(
            tech_relevance_score=tech_score.score,
            market_impact_score=market_score.score,
            trending_score=trending_score.score,
            average_score=avg_score,
            recommendation=recommendation,
            summary=f"Average score: {avg_score:.1f}. Tech: {tech_score.score}, Market: {market_score.score}, Trending: {trending_score.score}"
        )
        print(f"Final Decision: {final_decision.recommendation}, Average Score: {final_decision.average_score}")
        
        return final_decision

def main():
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
    
    team = NewsEvaluationTeam()
    result = team.evaluate_news_item(sample_news)
    print("Final Evaluation:")
    print(result.model_dump_json(indent=2))
