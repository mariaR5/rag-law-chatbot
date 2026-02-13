from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    question: str

class Citation(BaseModel):
    source: str
    page: int
    snippet: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]

class CitationItem(BaseModel):
    page: int
    snippet: str

class MultiHighlightRequest(BaseModel):
    pdf_name: str
    citations: List[CitationItem]