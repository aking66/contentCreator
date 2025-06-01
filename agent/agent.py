# from google.adk.agents import Agent
# from google.adk.models.lite_llm import LiteLlm
# # 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
# root_agent = Agent(
#     model=LiteLlm(model="ollama_chat/mistral"),
#     name="article_agent",
#     description="وكيل يكتب مقالات تقنية عربية كاملة عند الطلب.",
#     instruction=(
#         "عندما يطلب المستخدم كتابة مقالة:\n"
#         "1. أنشئ عنوانًا جذابًا.\n"
#         "2. اكتب مقدّمة قصيرة توضِّح الفكرة.\n"
#         "3. قسِّم المتن إلى 3-4 فقرات مرتَّبة، تتضمَّن أمثلة أو أحدث الاتجاهات.\n"
#         "4. اختم بخلاصة أو دعوة للتفاعل.\n"
#         "اكتب باللغة العربية الفصحى، واستخدم Markdown للعناوين والفقرات."
#     ),
#     tools=[]
# )

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
# from agent.tools.google_news_rss_tools import google_news_search
from google.adk.tools import google_search

# export GROQ_API_KEY="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"
root_agent = Agent(
    model=LiteLlm(model="groq/gemini-2.0-flash"),
    name="article_agent",
    description="Agent that fetches recent articles from Google News and summarizes them.",
    instruction=(
        "اجمع أحدث مقالات التقنية من google_news_search ثم أعِد JSON بالموضوعات."
    ),
    tools=[google_search],
)