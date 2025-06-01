from autogen import AssistantAgent, UserProxyAgent
from autogen.oai.openai_utils import config_list_from_dotenv
from autogen import ConversableAgent
# Manually define your local endpoint config
config_list = [{
    "model": "qwen3:4b",  # Must match the model name you pulled in ollama
    "base_url": "http://localhost:11434/v1",  # Ollama's endpoint
    "api_key": "ollama",  # dummy, not used but required
}]

assistant = AssistantAgent("assistant", llm_config={"config_list": config_list, "seed": None})

    # Create a UserProxyAgent that can execute code
user_proxy = UserProxyAgent(
        "user_proxy",
        is_termination_msg = lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        max_consecutive_auto_reply=10,
        code_execution_config={"work_dir": "coding", "use_docker": False},
        human_input_mode="NEVER"
        )

# Initiate a chat between the user proxy and the assistant
response = user_proxy.initiate_chat(assistant, message="Hello!")
summary = response.summary if hasattr(response, 'summary') else "No summary available."
    
print(summary)

iface = gr.Interface(fn=run_assistant, inputs="text", outputs="text", title="AutoGen Assistant")
iface.launch()
