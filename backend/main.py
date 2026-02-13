from fastapi import FastAPI
from schemas import QueryRequest, QueryResponse, HighlightRequest
from pdf_highlighter import highlight_pdf
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI()

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

@app.post('/highlight')
def generate_highlighted_pdf(citation: HighlightRequest):
    try:
        output_file = highlight_pdf(
            source_pdf = citation.pdf_name,
            page_number = citation.page,
            snippet = citation.snippet
        )
    
        output_path = Path("highlighted_pdfs") / output_file
        return FileResponse(
            path = output_path,
            media_type = "application/pdf",
            filename = output_file
        )
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": "An unexpected error occurred"}