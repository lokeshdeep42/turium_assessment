from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime

class IngestRequest(BaseModel):
    """Request model for ingesting content."""
    content: str = Field(..., min_length=1, description="Text content or URL to ingest")
    source_type: Literal["note", "url"] = Field(..., description="Type of content: note or url")
    
    @validator('content')
    def validate_content(cls, v, values):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        
        # Basic URL validation if source_type is url
        if values.get('source_type') == 'url':
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError("URL must start with http:// or https://")
        
        return v.strip()

class QueryRequest(BaseModel):
    """Request model for querying the knowledge base."""
    question: str = Field(..., min_length=1, description="Question to ask")
    max_results: Optional[int] = Field(5, ge=1, le=10, description="Maximum number of results")
    
    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

class SourceSnippet(BaseModel):
    """Model for source snippets in query responses."""
    item_id: int
    content: str
    source_type: str
    url: Optional[str] = None
    relevance_score: float

class QueryResponse(BaseModel):
    """Response model for queries."""
    answer: str
    sources: list[SourceSnippet]
    question: str

class Item(BaseModel):
    """Model for saved items."""
    id: int
    content: str
    source_type: str
    url: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True

class IngestResponse(BaseModel):
    """Response model for ingestion."""
    success: bool
    message: str
    item_id: Optional[int] = None

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
