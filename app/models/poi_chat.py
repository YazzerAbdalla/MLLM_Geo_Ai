from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class PoiChatRequest(BaseModel):
    analysis: Optional[dict] = None
    question: str = ""
    history: List[HistoryItem] = Field(default_factory=list)


class PoiChatResponse(BaseModel):
    summary: str
    answer: str
    model: str = "gemini-2.5-flash"
