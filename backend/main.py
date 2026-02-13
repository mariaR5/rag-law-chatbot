import os
from dotenv import load_dotenv
from fastapi import FastAPI
from schemas import QueryRequest, QueryResponse
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain


load_dotenv()
app = FastAPI()

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
            "snippet": d.page_content[:100] + "..."
        } for d in response["context"]
    ]

    return {
        "answer": answer_text,
        "citations": citations
    }

@app.get('/health')
def health_check():
    return {"status": "running"}