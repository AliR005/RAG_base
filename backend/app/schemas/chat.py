from pydantic import BaseModel


class Message(BaseModel):
    role: str  # "user" или "assistant"
    content: str


class ChatRequest(BaseModel):
    query: str
    history: list[Message] = []


class ChatResponse(BaseModel):
    answer: str
