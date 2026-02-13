import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def build_vector_store():
    data_path = 'data/'
    all_chunks = []

    for file in os.listdir(data_path):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(data_path, file))
            docs = loader.load()

            # Text chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=100
            )
            chunks = text_splitter.split_documents(docs)
            all_chunks.extend(chunks)
    
    # Save to FAISS
    vector_db = FAISS.from_documents(all_chunks, embeddings)
    vector_db.save_local("faiss_index")
    print(f"Indexed {len(all_chunks)} chunks from PDFs")
    return vector_db

if __name__ == "__main__":
    build_vector_store()