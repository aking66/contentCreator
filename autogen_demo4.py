import asyncio
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from pydantic import BaseModel

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
    # Define an agent
    web_surfer_agent = MultimodalWebSurfer(
        name="MultimodalWebSurfer",
        model_client=model_client,
        headless=False,
        start_page="https://github.com/microsoft/autogen",
    )

    # Define a team
    agent_team = RoundRobinGroupChat([web_surfer_agent], max_turns=3)

    # Run the team and stream messages to the console
    stream = agent_team.run_stream(
        task="Retrieve the current number of forks for the AutoGen repository on GitHub. Please provide only the number, without any additional explanation."
    )
    await Console(stream)
    # Close the browser controlled by the agent
    await web_surfer_agent.close()

asyncio.run(main())

