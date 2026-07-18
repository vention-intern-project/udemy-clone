import json

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

METADATA_PROMPT = """Given this lesson content, return a JSON object with:
- keywords: array of 3-5 relevant keywords (lowercase)
- description: 1-2 sentence summary of the lesson

Return ONLY the JSON object, no other text.

Content:
{content}"""

QUIZ_PROMPT = """Given this lesson content, generate exactly 3
multiple-choice questions. Each question has 4 options (A-D), one correct.
Return ONLY a JSON array of objects with: question,
options (array of 4), correct_answer (letter A-D).

Content:
{content}"""

SUMMARY_PROMPT = """Given this lesson content, return a JSON object with:
- paragraph: 2-3 sentence summary
- bullets: array of 3-5 key takeaways

Return ONLY the JSON object, no other text.

Content:
{content}"""


async def generate_metadata(content: str) -> dict:
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
    )

    prompt = METADATA_PROMPT.format(content=content[:3000])
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(text)


async def generate_quiz(content: str) -> list[dict]:
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
    )

    prompt = QUIZ_PROMPT.format(content=content[:3000])
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(text)


async def generate_summary(content: str) -> dict:
    llm = ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,
    )

    prompt = SUMMARY_PROMPT.format(content=content[:3000])
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(text)
