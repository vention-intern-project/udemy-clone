from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage

from app.feature.chat.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    try:
        agent = req.app.state.agent
        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": request.thread_id}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat agent error: {str(e)}",
        ) from None

    return ChatResponse(
        thread_id=request.thread_id,
        response=response["messages"][-1].text,
    )
