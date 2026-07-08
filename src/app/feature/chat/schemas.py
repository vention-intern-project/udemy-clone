from pydantic import BaseModel


class ChatRequest(BaseModel):
    thread_id: str
    course_id: int
    lesson_id: int
    message: str


class ChatResponse(BaseModel):
    thread_id: str
    response: str
