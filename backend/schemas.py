from pydantic import BaseModel
from typing import List

# User's question
class QueryRequest(BaseModel):
    question: str

# Structure of a single reference found in a document
class Citation(BaseModel):
    source: str
    page: int
    snippet: str

# Response returned to the user
class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]

# Structure of a single reference used to generate the highlighted PDF
class CitationItem(BaseModel):
    page: int
    snippet: str

# Request to generate the highlighted PDF
class HighlightRequest(BaseModel):
    pdf_name: str
    citations: List[CitationItem]