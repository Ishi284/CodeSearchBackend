from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.db.models import MongoBaseModel, PyObjectId
from app.core.config import settings

class CodeSearchResult(BaseModel):
    code: str
    similarity: float
    distance: float

class ChatMessage(BaseModel):
    message: str
    language: str
    timestamp: datetime = Field(default_factory=settings.get_current_time())
    results: Optional[List[CodeSearchResult]] = None

class ChatSession(MongoBaseModel):
    user_id: PyObjectId
    title: str = "Untitled Chat"
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=settings.get_current_time())
    updated_at: datetime = Field(default_factory=settings.get_current_time())

class ChatSessionCreate(BaseModel):
    title: str = "Untitled Chat"

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None

class ChatMessageCreate(BaseModel):
    message: str
    language: str

class SearchQuery(BaseModel):
    query: str
    language: str
    top_k: int = 3