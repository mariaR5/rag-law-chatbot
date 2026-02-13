import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from schemas import QueryRequest, QueryResponse, MultiHighlightRequest
from pdf_highlighter import highlight_pages, DATA_FOLDER
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain


load_dotenv()
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the embeddings and FAISS vector DB
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

# Initialise LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0, 
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Create prompt template
system_prompt = (
    "You are 'Bylaw Buddy', a helpful civic assistant. "
    "Use the following pieces of retrieved context to answer the user's question. "
    "If you don't know the answer based on the context, say that you don't know. "
    "Keep the answer concise and professional."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

# Create the chains
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vector_db.as_retriever(), question_answer_chain)

@app.get('/')
def root():
    return {"message": "Server is running"}

@app.post('/ask', response_model=QueryResponse)
def ask_bylaw(request: QueryRequest):
    # Invoke RAG pipeline
    response = rag_chain.invoke({"input": request.question})

    # Extract text answer
    answer_text = response["answer"]

    citations = [
        {
            "source": d.metadata.get("source", "Unknown"),
            "page": d.metadata.get("page", 0) + 1,
            "snippet": d.page_content  # Store full content for accurate highlighting
        } for d in response["context"]
    ]

    return {
        "answer": answer_text,
        "citations": citations
    }

@app.get('/health')
def health_check():
    return {"status": "running"}

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
            detail=f"PDF '{request.pdf_name}' not found at {pdf_path}"
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

