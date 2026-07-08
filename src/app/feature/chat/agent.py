from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.feature.chat.service import checkpointer

SYSTEM_PROMPT = """You are a helpful course assistant for students.

Your role:
- Answer questions about the current lesson's content
- Explain concepts in clear, student-friendly language
- Generate practice quizzes when asked
- Summarize lessons when requested
- Define terms used in the course

Rules:
- Always base your answers on the actual lesson content
- If you don't know something from the lesson, say so honestly
- Use tools to fetch lesson content before answering content-specific questions
- Keep responses concise but thorough"""


def create_chat_agent():
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=settings.OPENROUTER_API_KEY,
    )

    agent = create_agent(
        model=llm,
        system_prompt=SystemMessage(content=SYSTEM_PROMPT),
        checkpointer=checkpointer,
    )

    return agent
