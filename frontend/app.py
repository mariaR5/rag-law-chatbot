import streamlit as st
import requests
import uuid
import base64
from pathlib import Path
from typing import Optional, List, Dict

HIGHLIGHT_DIR = Path("highlighted_pdfs_frontend")
HIGHLIGHT_DIR.mkdir(exist_ok=True)

API_BASE_URL = "http://localhost:8000"
API_TIMEOUT_SHORT = 10  # Timeout for simple queries
API_TIMEOUT_LONG = 20   # Timeout for PDF generation

def get_loaded_laws() -> List[str]:
    """Get list of indexed law PDFs."""
    # Temporary fallback until backend is ready
    return [
        "Environment_Protection_Act.pdf",
        "Motor_Vehicles_Act.pdf",
        "Consumer_Protection_Act.pdf"
    ]

def ask_backend(question: str) -> Dict[str, any]:
    """
    Send a question to the backend API.
    
    Args:
        question: Legal question to ask
        
    Returns:
        Dictionary with 'answer' and 'citations' keys
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/ask",
            json={"question": question},
            timeout=API_TIMEOUT_SHORT
        )
        return response.json()
    except Exception:
        return {
            "answer": "Sorry, I could not answer your question. Please try again later.",
            "citations": []
        }


def fetch_highlighted_pdf(citations: List[Dict]) -> Optional[Path]:
    """
    Fetch a highlighted PDF from the backend for given citations.
    
    Args:
        citations: List of citation dicts with 'source', 'page', and 'snippet' keys
        
    Returns:
        Path to the saved PDF file, or None if failed
    """
    if not citations:
        st.error("No citations to highlight")
        return None
        
    try:
        response = requests.post(
            f"{API_BASE_URL}/highlight",
            json={
                "pdf_name": citations[0]["source"],
                "citations": [
                    {
                        "page": c["page"],
                        "snippet": c["snippet"]
                    }
                    for c in citations
                ]
            },
            timeout=API_TIMEOUT_LONG
        )

        if response.status_code != 200:
            st.error("Failed to generate highlighted PDF")
            return None

        file_name = f"{uuid.uuid4()}.pdf"
        file_path = HIGHLIGHT_DIR / file_name

        with open(file_path, "wb") as f:
            f.write(response.content)

        return file_path

    except Exception:
        st.error("Backend not reachable")
        return None


def show_pdf_inline(pdf_path: Path) -> None:
    """
    Display a PDF inline in the Streamlit app using base64 encoding.
    
    Args:
        pdf_path: Path to the PDF file to display
    """
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="600px"
            style="border: none;"
        ></iframe>
    """

    st.markdown(pdf_display, unsafe_allow_html=True)


st.set_page_config(
    page_title='Bylaw Buddy',
    layout="wide",
)

st.title("Bylaw Buddy")

st.markdown(
    """
    **Your AI assistant for Indian laws** 🇮🇳  

    Ask questions based on official Acts like the Environment Protection Act,  
    Motor Vehicles Act, and Consumer Protection Act.

    ---
    ⚠️ **Disclaimer:**  
    This tool is for **educational and informational purposes only**.  
    It does **not** constitute legal advice.  
    For legal decisions, consult a qualified legal professional.
    """
)


st.sidebar.header("Laws Indexed")

for law in get_loaded_laws():
    st.sidebar.write(f" -> {law}")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_question = st.chat_input(
    "Ask a legal question (e.g. Is wearing helmet compulsory?)"
)

if user_question:
    st.session_state.messages.append(("user", user_question))
    with st.spinner("Thinking..."):
        response = ask_backend(user_question)
    
    st.session_state.messages.append(("assistant", response))

for role, message in st.session_state.messages:
    if role == "user":
        with st.chat_message("user"):
            st.write(message)

    else:
        with st.chat_message("assistant"):
            st.write(message["answer"])

            if message["citations"]:
                with st.expander("Evidence"):

                    if st.button(
                        "View all citations",
                        key=f"multi_{len(st.session_state.messages)}"
                    ):
                        with st.spinner("Generating highlighted PDF..."):
                            pdf_path = fetch_highlighted_pdf(message["citations"])
                            if pdf_path:
                                show_pdf_inline(pdf_path)


                    for citation in message["citations"]:
                        st.markdown(
                            f"""
                            **Source:** {citation['source']}  
                            **Page:** {citation['page']}  

                            > {citation['snippet']}
                            """
                        )
            else:
                st.write("No evidence found.")
