from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.feature.chat.service import checkpointer
from app.feature.chat.system_prompt import SYSTEM_PROMPT
from app.feature.knowledge.tools import KNOWLEDGE_TOOLS


def create_chat_agent():
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=1,
    )

    agent = create_agent(
        model=llm,
        tools=KNOWLEDGE_TOOLS,
        system_prompt=SystemMessage(content=SYSTEM_PROMPT),
        checkpointer=checkpointer,
    )

    return agent
