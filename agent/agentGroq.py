# from google.adk.agents import Agent
# from google.adk.tools import google_Search

# # export GROQ_API_KEY="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"
# root_agent = Agent(
#     model=LiteLlm(model="groq/llama3-70b-8192"),
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
#     tools=[google_search], # Provide an instance of the tool
# )