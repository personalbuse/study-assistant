from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    file_hash: Optional[str] = None
    file_type: Optional[str] = None
    status: str
    page_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FolderRequest(BaseModel):
    path: str

class FolderResponse(BaseModel):
    folder_path: str
    created_at: datetime

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]

class SummaryResponse(BaseModel):
    id: int
    document_id: int
    summary: Optional[str] = None
    key_concepts: Optional[list] = None
    main_topics: Optional[list] = None
    study_questions: Optional[list] = None
    created_at: datetime

class FlashcardResponse(BaseModel):
    id: int
    document_id: int
    question: str
    answer: str
    topic: Optional[str] = None
    created_at: datetime

class QuizResponse(BaseModel):
    id: int
    document_id: int
    title: Optional[str] = None
    questions: Optional[list] = None
    created_at: datetime
