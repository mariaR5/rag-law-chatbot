from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from schemas import QueryRequest, QueryResponse, MultiHighlightRequest
from pdf_highlighter import highlight_pages, DATA_FOLDER

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/health')
def health_check():
    return {"status": "running"}

@app.post('/ask', response_model=QueryResponse)
def ask_bylaw(request: QueryRequest):
    return {
        "answer": f"You asked {request.question}. This is a mock response while the backend is being built",
        "citations": [
            {"source": "demo.pdf", "page": 1, "snippet": "Mock citation text"}
        ]
    }

@app.get('/')
def root():
    return {"message": "Server is running"}

@app.post("/highlight")
def generate_highlighted_pdf(request: MultiHighlightRequest):
    # Validate citations list is not empty
    if not request.citations:
        raise HTTPException(
            status_code=400,
            detail="Citations list cannot be empty"
        )
    
    # Validate PDF exists
    pdf_path = DATA_FOLDER / request.pdf_name
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"PDF '{request.pdf_name}' not found"
        )
    
    try:
        pdf_bytes = highlight_pages(
            source_pdf=request.pdf_name,
            citations=[citation.dict() for citation in request.citations]
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=highlighted_citations.pdf"
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
