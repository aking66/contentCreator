from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.messages import StopMessage
from autogen_agentchat.base import TerminatedException, TerminationCondition, TaskResult
from autogen_core import Component
from pydantic import BaseModel
import asyncio

# Feedback models
class ContentFeedback(BaseModel):
    grammar_score: int
    clarity_score: int
    style_score: int
    to_do: str

class SEOFeedback(BaseModel):
    seo_score: int
    to_do: str

class ScoreTerminationConfig(BaseModel):
    min_score_thresh: int

class ScoreTerminationCondition(TerminationCondition, Component[ScoreTerminationConfig]):
    def __init__(self, min_score_thresh: int = 8):
        self.min_score_thresh = min_score_thresh
        self._terminated = False
        self.min_content_score = 0
        self.seo_score = 0

    @property
    def terminated(self) -> bool:
        return self._terminated
    
    async def __call__(self, messages) -> StopMessage | None:
        if self._terminated:
            raise TerminatedException("Termination condition has already been reached")
        
        # Check for explicit TERMINATE message from writer_agent
        for message in messages:
            if message.source == "writer_agent" and isinstance(message.content, str) and "TERMINATE" in message.content:
                self._terminated = True
                return StopMessage(
                    content=f"Writer agent has indicated content is complete with satisfactory scores.",
                    source="ScoreTermination",
                )
                
            if message.source == "content_critic_agent":
                self.min_content_score = min(
                    message.content.grammar_score,
                    message.content.clarity_score,
                    message.content.style_score
                )
            
            elif message.source == "seo_critic_agent":
                self.seo_score = message.content.seo_score
        
        # For automatic termination if both scores are high enough    
        if self.min_content_score >= self.min_score_thresh and self.seo_score >= self.min_score_thresh:
            self._terminated = True
            return StopMessage(
                content=f"The minimum scores are greater than or equal to the threshold {self.min_score_thresh}!",
                source="ScoreTermination",
            )
        return None

    async def reset(self) -> None:
        self._terminated = False

    def _to_config(self) -> ScoreTerminationConfig:
        return ScoreTerminationConfig(min_score_thresh=self.min_score_thresh)

    @classmethod
    def _from_config(cls, config: ScoreTerminationConfig):
        return cls(
            min_score_thresh=config.min_score_thresh,
        )

def teamConfig(min_score_thresh: int = 8):
    model = OllamaChatCompletionClient(
        model="mistral:7b-instruct",  # Must match the model name you pulled in ollama
        base_url="http://localhost:11434/v1",  # Ollama's endpoint
    )

    writer_agent = AssistantAgent(
        name="writer_agent",
        description="A writer agent that writes full articles based on a given topic.",
        system_message=(
            "You are a writer agent. You will be given a topic and you need to write a complete article in markdown format about it. "
            "Your article should be comprehensive, well-structured with introduction, body paragraphs, and conclusion. "
            "Include headings, subheadings, and proper formatting to make it engaging and professional. "
            "You will be collaborating with a content-critic agent and an SEO-critic agent. These agents "
            "will provide feedbacks and scores on your content. You should address their feedbacks and improve your content. "
            "IMPORTANT: Do NOT say 'TERMINATE' on your own. Wait for both the content-critic and SEO-critic agents to evaluate your content first. "
            f"Only if both critics have evaluated your content AND given you a minimum score of {min_score_thresh} in all categories, "
            "then (and ONLY then) should you exactly say 'TERMINATE' to indicate that the content is satisfactory. "
            f"If either critic has not given feedback or any score is below {min_score_thresh}, continue to improve the content based on their feedback."
        ),
        model_client=model
    )

    content_critic_agent = AssistantAgent(
        name="content_critic_agent",
        description="A content-critic agent that provides feedback on the article written by the writer agent.",
        system_message=(
            "You are a content-critic agent. You will be given an article and you need to provide scores from 0 to 10 on "
            "the grammar, clarity, and style of the article. You should also provide a to-do list of improvements for the writer agent, "
            "focusing on article structure, paragraph development, transitions between sections, and overall readability. "
            "You should never write the article yourself. Be as specific as possible. "
            f"If the minimum score of the text is {min_score_thresh} or above {min_score_thresh}, leave the to-do list empty. "
        ),
        model_client=model,
        output_content_type=ContentFeedback
    )

    seo_critic_agent = AssistantAgent(
        name="seo_critic_agent",
        description="An SEO-critic agent that provides feedback on the SEO of the article written by the writer agent.",
        system_message=(
            "You are an SEO-critic agent. You will be given an article and you need to provide a single score from 0 to 10 "
            "on the SEO of the article. You should evaluate keyword usage, meta descriptions, headings structure, content length, "
            "and internal linking opportunities. You should also provide a to-do list of improvements for the writer agent. "
            "You should never write the article yourself. Be as specific as possible. "
            f"If the score of the text is {min_score_thresh} or above {min_score_thresh}, leave the to-do list empty. "
        ),
        model_client=model,
        output_content_type=SEOFeedback
    )

    selector_prompt = """You are in a team of content generation agents. The following roles are available:
{roles}.
Read the following conversation. Then select the next role from {participants} to speak. Only return the role.

{history}

Follow these specific rules for role selection:
1. The first message should always be from the writer_agent.
2. After the writer_agent produces content, the content_critic_agent should evaluate it first.
3. After the content_critic_agent evaluates, the seo_critic_agent should evaluate next.
4. If any critic agent provides feedback with a to-do list, the writer_agent should address it next.
5. After the writer_agent addresses feedback, the same critic who provided the feedback should review the changes.
6. Both critics must evaluate the content before the writer_agent can terminate the conversation.
7. If the writer_agent says 'TERMINATE', the conversation should end.

Read the above conversation. Then select the next role from {participants} to speak. Only return the role.
"""
    termination = ScoreTerminationCondition(min_score_thresh) | MaxMessageTermination(15)

    team = SelectorGroupChat(
        participants=[writer_agent, content_critic_agent, seo_critic_agent],
        model_client=model,
        selector_prompt=selector_prompt,
        termination_condition=termination
    )
    return team

async def orchestrate(team, task):
    async for message in team.run_stream(task=task):
        if isinstance(message, TaskResult):
            print(msg:=f'**Termination**: {message.stop_reason}')
            yield msg
        else:
            print('--'*20)
            if message.source == "writer_agent":
                print(msg:=f'**Writer**: {message.content}')
                yield msg
            elif message.source == "content_critic_agent":
                print(msg:=f'**Content Critic**:\n\n **Grammar Score**: {message.content.grammar_score},\n\n**Clarity Score**: {message.content.clarity_score},\n\n **Style Score**: {message.content.style_score},\n\n **To Do**: {message.content.to_do}')
                yield msg
            elif message.source == "seo_critic_agent":
                print(msg:=f'**SEO Critic**:\n\n **SEO Score**: {message.content.seo_score},\n\n **To Do**: {message.content.to_do}')
                yield msg
            elif message.source == "user":
                print(msg:=f'**User**:\n\n{message.content}')
                yield msg

async def main():
    task = "Write a complete article about the role of artificial intelligence in transforming healthcare industry."
    team = teamConfig(min_score_thresh=8)
    async for message in orchestrate(team, task):
        pass

if __name__ == "__main__":
    asyncio.run(main())
