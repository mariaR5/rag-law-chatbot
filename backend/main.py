from fastapi import FastAPI
from schemas import QueryRequest, QueryResponse
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

app = FastAPI()

# Load the FAISS database
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

@app.get('/')
def root():
    return {"message": "Server is running"}


@app.post('/ask', response_model=QueryResponse)
def ask_bylaw(request: QueryRequest):
    # Search for the top 3 most relevant chunks
    docs = vector_db.similarity_search(request.question, k=3)

    context_text = "\n\n".join([d.page_content for d in docs])

    citations = [
        {
            "source": d.metadata.get("source", "Unknown"),
            "page": d.metadata.get("page", 0) + 1,
            "snippet": d.page_content[:100] + "..."
        } for d in docs
    ]

    return {
        "answer": f"I found this in the bylaws: {context_text}",
        "citations": citations
    }

@app.get('/health')
def health_check():
    return {"status": "running"}