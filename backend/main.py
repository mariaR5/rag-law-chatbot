from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import QueryRequest, QueryResponse, MultiHighlightRequest
from pdf_highlighter import highlight_pages, DATA_FOLDER
from pathlib import Path
from fastapi.responses import FileResponse

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
        output_file = highlight_pages(
            source_pdf=request.pdf_name,
            citations=[citation.dict() for citation in request.citations]
        )

        output_path = Path("highlighted_pdfs") / output_file

        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename=output_file
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
