import asyncio
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_agentchat.agents import AssistantAgent

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
    # Define the web surfer agent
    web_surfer_agent = MultimodalWebSurfer(
        name="WebSurfer",
        model_client=model_client,
        headless=False,
        start_page="https://www.msn.com/en-us/news/technology/the-illusion-of-thinking-apple-research-finds-ai-models-collapse-and-give-up-with-hard-puzzles/ar-AA1GnC2a",
    )

    # Define the summarizer agent
    summarizer_agent = AssistantAgent(
        name="Summarizer",
        model_client=model_client,
        system_message="You are a skilled content summarizer. When you receive web content from the WebSurfer agent, analyze it and provide a clear, concise summary of the main points and key information."
    )

    # Define a team with both agents
    agent_team = RoundRobinGroupChat([web_surfer_agent, summarizer_agent], max_turns=4)

    # Run the team and stream messages to the console
    stream = agent_team.run_stream(
        task="Please read and provide a detailed summary of the article about AI models and hard puzzles."
    )
    await Console(stream)
    # Close the browser controlled by the agent
    await web_surfer_agent.close()

asyncio.run(main())

