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

from web_scraper import scrape_with_brightdata

# App and env setup
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
rag_chain = create_retrieval_chain(
    vector_db.as_retriever(), 
    question_answer_chain
)

# Root and Health endpoint
@app.get('/')
def root():
    return {"message": "Server is running"}

@app.get('/health')
def health_check():
    return {"status": "running"}



# Input: User question | Output: Answer with citations
@app.post('/ask', response_model=QueryResponse)
def ask_bylaw(request: QueryRequest):

    # Invoke RAG pipeline ( if we have relevant docs )
    response = rag_chain.invoke({"input": request.question})

    # Extract text answer
    answer_text = response["answer"]

    # Search for negative answers from LLM
    negative_phrases = ["i don't know", "not mentioned in the context", "i'm sorry"]

    if any(phrase in answer_text.lower() for phrase in negative_phrases):
        scraped_answer = scrape_with_brightdata(request.question, os.getenv("BRIGHTDATA_API_TOKEN"))
        
        # Check if scraper actually returned useful text (and not an error/empty)
        if scraped_answer and "Error" not in scraped_answer:
            return {
                "answer": f"**General Legal Info (Not from local PDFs):**\n\n{scraped_answer}",
                "citations": []  # No citations because it's from the web
            }
        else:

            return {
                "answer": "I'm sorry, I couldn't find relevant information in the local bylaws or through our extended search.",
                "citations": []
            }

    # Success case -> Return answer and citations from context
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



# Get a list of all PDF files in the data folder
@app.get('/laws')
def get_loaded_laws():
    try:
        if not DATA_FOLDER.exists():
            return []
        
        pdf_files = [f.name for f in DATA_FOLDER.glob("*.pdf")]
        return sorted(pdf_files)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading data folder: {str(e)}"
        )

# Serves the PDF file from the data folder
@app.get('/pdf/{pdf_name}')
def serve_pdf(pdf_name: str):
    pdf_path = DATA_FOLDER / pdf_name
    
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"PDF '{pdf_name}' not found"
        )
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={pdf_name}"
        }
    )

# Generate a highlighted PDF and returns a downloadable file
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
        # Generate a new hilighted PDF
        pdf_bytes = highlight_pages(
            source_pdf=request.pdf_name,
            citations=[citation.dict() for citation in request.citations]
        )

        # Return as downloadable file
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