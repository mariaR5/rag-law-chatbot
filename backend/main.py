from fastapi import FastAPI
from schemas import QueryRequest, QueryResponse

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