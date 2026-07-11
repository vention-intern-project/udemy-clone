import json

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

METADATA_PROMPT = """Given this lesson content, return a JSON object with:
- keywords: array of 3-5 relevant keywords (lowercase)
- description: 1-2 sentence summary of the lesson

Return ONLY the JSON object, no other text.

Content:
{content}"""


async def generate_metadata(content: str) -> dict:
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=settings.OPENROUTER_API_KEY,
        temperature=0,
    )

    prompt = METADATA_PROMPT.format(content=content[:3000])
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    text = response.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(text)
