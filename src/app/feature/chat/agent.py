from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.feature.chat.service import checkpointer
from app.feature.chat.system_prompt import SYSTEM_PROMPT
from app.feature.knowledge.tools import KNOWLEDGE_TOOLS


def create_chat_agent():
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=settings.OPENROUTER_API_KEY,
    )

    agent = create_agent(
        model=llm,
        tools=KNOWLEDGE_TOOLS,
        system_prompt=SystemMessage(content=SYSTEM_PROMPT),
        checkpointer=checkpointer,
    )

    return agent
