import os   
from autogen import AssistantAgent

config_list = [{
    "model": "qwen3:4b",  # Must match the model name you pulled in ollama
    "base_url": "http://localhost:11434/v1",  # Ollama's endpoint
    "api_key": "ollama",  # dummy, not used but required
}]

llm_config = {
    "config_list": config_list,
}

writer = AssistantAgent(
    name="Writer",
    system_message="You are a writer. You write engaging and concise "
    "blogpost (with title) on given topics. You must polish your "
    "writing based on the feedback you receive and give a refined "
    "version. Only return your final work without additional comments.",
    llm_config=llm_config,
)


task = '''Write a blogpost about the latest advancements in AI in 2024. Focus on new models, applications, and ethical considerations. 
The post should be engaging and informative, 
suitable for a technical audience. Include a catchy title and structure the content with clear sections.
'''

# reply = writer.generate_reply(messages=[{"content": task, "role": "user"}])

# print(reply)


reviewer = AssistantAgent(
    name="Reviewer",
    is_termination_msg = lambda x: x.get("content", "").find("TERMINATE") >= 0,
    system_message="You are a reviewer. You review the blogpost and provide feedback on its content, style, and structure. You must provide a refined version of the blogpost based on the feedback you receive.",
    llm_config=llm_config,
)

# reviewer.initiate_chat(
#     recipient=writer,   
#     message=task,
#     max_turns=2,
#     summary_method="last_msg"
# )

SEO_reviewer = AssistantAgent(
    name="SEO_Reviewer",
    llm_config=llm_config,
    system_message=(
        "As an SEO expert, your role is to analyze and enhance content for optimal search engine performance. "
        "Focus on providing actionable recommendations that boost rankings and drive organic traffic. "
        "Limit your feedback to 3 key points, ensuring they are specific and directly applicable. "
        "Start each review by introducing yourself as an SEO Reviewer."
    ),
)

grammatical_error_reviewer = AssistantAgent(
    name="Grammatical_Error_Reviewer",
    llm_config=llm_config,
    system_message=(
        "As a grammar specialist, your task is to meticulously examine content "
        "for grammatical errors, punctuation mistakes, and style inconsistencies. "
        "Provide up to 3 key points addressing the most significant grammatical issues. "
        "Ensure your feedback is specific, actionable, and includes examples where appropriate. "
        "Begin each review by introducing yourself as a Grammatical Error Reviewer."
    ),
)

ethics_reviewer = AssistantAgent(
    name="Ethics_Reviewer",
    llm_config=llm_config,
    system_message=(
        "As an ethics specialist, your role is to evaluate content for ethical integrity "
        "and identify any potential moral concerns. "
        "Provide up to 3 specific, actionable recommendations to address ethical issues. "
        "Ensure your feedback is concise and directly applicable. "
        "Start each review by introducing yourself as an Ethics Reviewer."
    ),
)

meta_reviewer = AssistantAgent(
    name="Meta_Reviewer",
    llm_config=llm_config,
    system_message=(
        "You are a meta reviewer, you aggregate and review "
        "the work of other reviewers and give a final suggestion on the content."
    ),
)

def reflection_message(recipient, messages, sender, config):
    return f'''Review the following content.
    
{recipient.chat_messages_for_summary(sender)[-1]['content']}'''

review_chats = [
    {
        "recipient": SEO_reviewer,
        "message": reflection_message,
        "summary_method": "reflection_with_llm",
        "summary_args": {
            "summary_prompt": (
                "Return review into as JSON object only:\n"
                "{'Reviewer': '', 'Review': ''}. Here Reviewer should be your role"
            )
        },
        "max_turns": 1,
    },
    {
        "recipient": grammatical_error_reviewer,
        "message": reflection_message,
        "summary_method": "reflection_with_llm",
        "summary_args": {
            "summary_prompt": (
                "Return review into as JSON object only:\n"
                "{'Reviewer': '', 'Review': ''}"
            )
        },
        "max_turns": 1,
    },
    {
        "recipient": ethics_reviewer,
        "message": reflection_message,
        "summary_method": "reflection_with_llm",
        "summary_args": {
            "summary_prompt": (
                "Return review into as JSON object only:\n"
                "{'reviewer': '', 'review': ''}"
            )
        },
        "max_turns": 1,
    },
    {
        "recipient": meta_reviewer,
        "message": "Aggregate feedback from all reviewers and give final suggestions on the writing.",
        "max_turns": 1,
    }
]


# Register nested review flows triggered by the writer
reviewer.register_nested_chats(
    review_chats,
    trigger=writer,
)

# Start the main review process by sending the task to the writer
res = reviewer.initiate_chat(
    recipient=writer,
    message=task,
    max_turns=2,
    summary_method="last_msg"
)

# Print the final summary from the meta reviewer
print(res.summary)