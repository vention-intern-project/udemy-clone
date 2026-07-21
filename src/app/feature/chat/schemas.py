from pydantic import BaseModel


class ChatRequest(BaseModel):
    thread_id: str
    course_id: int | None = None
    lesson_id: int | None = None
    message: str


class ChatResponse(BaseModel):
    thread_id: str
    response: str
