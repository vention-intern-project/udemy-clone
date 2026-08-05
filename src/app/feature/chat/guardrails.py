import re
import uuid
from difflib import SequenceMatcher
from typing import Any

from langchain.agents.middleware import AgentState, after_agent, before_agent
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.runtime import Runtime

from app.feature.chat.system_prompt import SYSTEM_PROMPT

INJECTION_REFUSAL = (
    "I can't follow instructions that try to change how I work. "
    "I'm happy to help with your course questions though!"
)

LEAK_REFUSAL = (
    "I can't share my internal instructions, but I'm happy to help with "
    "your course questions!"
)

INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"ignore (all|any|the)?\s*(previous|prior|above)\s*instructions",
        r"disregard (all|any|the)?\s*(previous|prior|above)\s*instructions",
        r"reveal (your )?(system )?prompt",
        r"(show|print|repeat) (me )?(your )?(system )?(prompt|instructions)",
        r"you are now\b",
        r"developer mode",
        r"jailbreak",
        r"pretend you have no (restrictions|rules)",
    ]
]

# Matches internal DB identifiers like "course_id: 5" or "lesson_id=12", but not
# the student-facing "Lesson 3: Intro" style listings the tools intentionally return.
INTERNAL_ID_PATTERN = re.compile(r"\b(course|lesson)_id\b\s*[:=]?\s*\d*", re.IGNORECASE)

SYSTEM_PROMPT_LEAK_THRESHOLD = 40


def _last_human_message(messages: list[AnyMessage]) -> HumanMessage | None:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message
    return None


def _last_ai_message_index(messages: list[AnyMessage]) -> int | None:
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], AIMessage):
            return i
    return None


def _looks_like_system_prompt_leak(text: str) -> bool:
    match = SequenceMatcher(None, text, SYSTEM_PROMPT).find_longest_match()
    return match.size >= SYSTEM_PROMPT_LEAK_THRESHOLD


@before_agent(can_jump_to=["end"])
async def block_prompt_injection(
    state: AgentState[Any], runtime: Runtime[None]
) -> dict[str, Any] | None:
    """Refuse the turn before the model runs if the user message looks like a
    prompt-injection or jailbreak attempt."""
    human_message = _last_human_message(state["messages"])
    if human_message is None or not human_message.content:
        return None

    content = str(human_message.content)
    if not any(pattern.search(content) for pattern in INJECTION_PATTERNS):
        return None

    return {
        "jump_to": "end",
        "messages": [AIMessage(content=INJECTION_REFUSAL, id=str(uuid.uuid4()))],
    }


@after_agent
async def enforce_output_guardrails(
    state: AgentState[Any], runtime: Runtime[None]
) -> dict[str, Any] | None:
    """Redact internal DB identifiers and block system-prompt leakage in the
    model's final response before it reaches the student."""
    messages = state["messages"]
    ai_idx = _last_ai_message_index(messages)
    if ai_idx is None:
        return None

    ai_message = messages[ai_idx]
    content = str(ai_message.content)
    if not content:
        return None

    if _looks_like_system_prompt_leak(content):
        new_content = LEAK_REFUSAL
    else:
        new_content = INTERNAL_ID_PATTERN.sub("[redacted]", content)

    if new_content == content:
        return None

    updated_message = AIMessage(content=new_content, id=ai_message.id)
    new_messages = list(messages)
    new_messages[ai_idx] = updated_message
    return {"messages": new_messages}
