from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_chat_agent, get_current_user_id
from app.db.database import get_db
from app.feature.chat.schemas import ChatRequest, ChatResponse
from app.feature.course.repository import get_course_by_id, get_lesson_by_id
from app.feature.enrollment.repository import get_active_enrollment_by_course

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent=Depends(get_chat_agent),
    user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    context = []

    if request.course_id is not None:
        course = await get_course_by_id(session, request.course_id)
        if course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found",
            )

        enrollment = await get_active_enrollment_by_course(
            session, user_id, request.course_id
        )
        if enrollment is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this course",
            )

        context.append(f"Course {request.course_id}")

    if request.lesson_id is not None:
        lesson = await get_lesson_by_id(session, request.lesson_id)
        if lesson is None or lesson.course_id != request.course_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found",
            )

        context.append(f"Lesson {request.lesson_id}")

    prefix = f"[{', '.join(context)}] " if context else ""
    message = f"{prefix}{request.message}"

    try:
        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": request.thread_id}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat agent error: {str(e)}",
        ) from None

    return ChatResponse(
        thread_id=request.thread_id,
        response=response["messages"][-1].text,
    )
