import streamlit as st
import requests
import base64
from typing import Optional, List, Dict

API_BASE_URL = "http://localhost:8000"
API_TIMEOUT_SHORT = 10  # Timeout for simple queries
API_TIMEOUT_LONG = 20   # Timeout for PDF generation

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_loaded_laws() -> List[str]:
    """Get list of indexed law PDFs from backend."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/laws",
            timeout=API_TIMEOUT_SHORT
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception:
        # Return empty list if backend is unreachable
        return []

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


def fetch_highlighted_pdf(citations: List[Dict]) -> Optional[bytes]:
    """
    Fetch a highlighted PDF from the backend for given citations.
    
    Args:
        citations: List of citation dicts with 'source', 'page', and 'snippet' keys
        
    Returns:
        PDF content as bytes, or None if failed
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

        return response.content

    except Exception:
        st.error("Backend not reachable")
        return None


def show_pdf_inline(pdf_bytes: bytes) -> None:
    """
    Display a PDF inline in the Streamlit app using base64 encoding.
    
    Args:
        pdf_bytes: PDF file content as bytes
    """
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

st.sidebar.markdown("""
<style>
.pdf-link {
    text-decoration: none !important;
    color: inherit !important;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.pdf-link:hover {
    color: #1f77b4 !important;
}
.pdf-link::after {
    content: "🔗";
    margin-left: 8px;
    font-size: 0.9em;
}
</style>
""", unsafe_allow_html=True)

for law in get_loaded_laws():
    pdf_url = f"{API_BASE_URL}/pdf/{law}"
    display_name = law.replace("_", " ").replace(".pdf", "")
    st.sidebar.markdown(
        f'<a href="{pdf_url}" target="_blank" class="pdf-link">{display_name}</a>',
        unsafe_allow_html=True
    )

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

for idx, (role, message) in enumerate(st.session_state.messages):
    if role == "user":
        with st.chat_message("user"):
            st.write(message)

    else:
        with st.chat_message("assistant"):
            st.write(message["answer"])

            if message["citations"]:
                with st.expander("Evidence"):

                    if st.button(
                        "View citation",
                        key=f"multi_{idx}"
                    ):
                        with st.spinner("Generating highlighted PDF..."):
                            pdf_bytes = fetch_highlighted_pdf([message["citations"][0]])
                            if pdf_bytes:
                                show_pdf_inline(pdf_bytes)


                    # Display only the first citation
                    citation = message["citations"][0]
                    display_snippet = citation['snippet'][:200] + "..." if len(citation['snippet']) > 200 else citation['snippet']
                    
                    st.markdown(
                        f"""
                        **Source:** {citation['source']}  
                        **Page:** {citation['page']}  
                        """
                    )
            else:
                st.write("No evidence found.")
