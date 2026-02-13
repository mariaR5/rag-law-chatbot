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

class HighlightRequest(BaseModel):
    pdf_name: str
    page: int
    snippet: str