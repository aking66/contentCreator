# create a virtual env e.g conda create -n autogen python=3.12
# pip install -U autogen-agentchat autogen-ext[web-surfer] 
# pip install -U "autogen-agentchat" "autogen-ext[web-surfer]"
# playwright install 

import asyncio
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_core.models import ModelInfo


async def main() -> None:

   # model_client = OpenAIChatCompletionClient(model="gpt-4o-2024-11-20")
   
    model_info = ModelInfo(
        id="mistral:7b-instruct",
        name="mistral:7b-instruct",
        provider="ollama",
        version="latest",
        json_output=True,
        function_calling=True,
        family="mistral",
        vision=True,
    )

    model_client = OllamaChatCompletionClient(
        model="mistral:7b-instruct",
        host="http://localhost:11434",
        model_info=model_info,
    )
  
    termination = MaxMessageTermination(
        max_messages=20) | TextMentionTermination("TERMINATE")
    websurfer_agent = MultimodalWebSurfer(
        name="websurfer_agent",
        description="an agent that solves tasks by browsing the web",
        model_client=model_client,
        headless=False,
        start_page="https://www.google.com/",
    )
    assistant_agent = AssistantAgent(
        name="assistant_agent",
        description="an agent that verifies and summarizes information",
        system_message="You are a task verification assistant who is working with a web surfer agent to solve tasks. At each point, check if the task has been completed as requested by the user. If the websurfer_agent responds and the task has not yet been completed, respond with what is left to do and then say 'keep going'. If and only when the task has been completed, summarize and present a final answer that directly addresses the user task in detail and then respond with  TERMINATE.",
        model_client=model_client)

    selector_prompt = """You are the cordinator of role play game. The following roles are available:
    {roles}. Given a task, the websurfer_agent will be tasked to address it by browsing the web and providing information.  The assistant_agent will be tasked with verifying the information provided by the websurfer_agent and summarizing the information to present a final answer to the user. 
    If the task  needs assistance from a human user (e.g., providing feedback, preferences, or the task is stalled), you should select the user_proxy role to provide the necessary information.

    Read the following conversation. Then select the next role from {participants} to play. Only return the role.

    {history}

    Read the above conversation. Then select the next role from {participants} to play. Only return the role.
    """
    user_proxy = UserProxyAgent(name="user_proxy", description="a human user that should be consulted only when the assistant_agent is unable to verify the information provided by the websurfer_agent")
    team = SelectorGroupChat(
        [websurfer_agent, assistant_agent, user_proxy],
        selector_prompt=selector_prompt,
        model_client=model_client, termination_condition=termination)

    await Console(team.run_stream(task="Could you please from google collect and share first 5 article links related to the latest Manus update?"))

    await websurfer_agent.close()

asyncio.run(main())
