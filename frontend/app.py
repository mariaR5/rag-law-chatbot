import streamlit as st
import requests
import base64
from typing import Optional, List, Dict

# Configurations
API_BASE_URL = "http://localhost:8000"


# API Functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_loaded_laws() -> List[str]:
    """Get list of indexed law PDFs from backend."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/laws",
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception:
        # Return empty list if backend is unreachable
        return []

# Ask backend for an answer
def ask_backend(question: str) -> Dict[str, any]:
    try:
        response = requests.post(
            f"{API_BASE_URL}/ask",
            json={"question": question},
        )
        return response.json()
    except Exception:
        return {
            "answer": "Sorry, I could not answer your question. Please try again later.",
            "citations": []
        }

# Fetch highlighted PDF from backend
def fetch_highlighted_pdf(citations: List[Dict]) -> Optional[bytes]:
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

        )

        if response.status_code != 200:
            st.error("Failed to generate highlighted PDF")
            return None

        return response.content

    except Exception:
        st.error("Backend not reachable")
        return None

# Display PDF inline
def show_pdf_inline(pdf_bytes: bytes) -> None:
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

# Page Configuration
st.set_page_config(
    page_title='Bylaw Buddy',
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS Styles
st.markdown("""
<style>
/* Title and Subtitle Styling */
h1 {
    text-align: center;
    font-size: 4rem !important;
}

.subtitle {
    font-size: 1.4em;
    font-weight: 600;
    margin-bottom: 10px;
    text-align: center;
}

/* Disclaimer Card */
.disclaimer-card {
    background: linear-gradient(135deg, #FFF4E6 0%, #FFE8CC 100%);
    border-left: 4px solid #FF9800;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 20px auto;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    max-width: 70%;
}

.disclaimer-card .icon {
    font-size: 1.5em;
    margin-right: 10px;
    vertical-align: middle;
}

.disclaimer-card .title {
    font-weight: 600;
    font-size: 1.1em;
    color: #E65100;
    margin-bottom: 8px;
}

.disclaimer-card .content {
    color: #5D4037;
    line-height: 1.6;
    font-size: 0.95em;
}

/* Chat Input Field Styling */
.stChatInput:focus-within {
    border-color: #2B8DFF !important;
    border-width: 1px !important;
    border-style: solid !important;
    border-radius: 0.5rem !important;
}

.stChatInput textarea:focus,
.stChatInput textarea:focus-visible,
textarea[data-testid="stChatInput"]:focus,
textarea[data-testid="stChatInput"]:focus-visible {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

.stChatInput textarea {
    outline: none !important;
    border: none !important;
    box-shadow: none !important;
}

.stChatInput > div,
.stChatInput > div > div {
    border: none !important;
    box-shadow: none !important;
}

.stChatInput button {
    background-color: #D2EAFF !important;
    color: #2B8DFF !important;
}

.stChatInput button:hover,
.stChatInput:focus-within button {
    background-color: #2B8DFF !important;
    color: white !important;
}

/* PDF Link Styling */
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

# Header Section
st.title("Bylaw Buddy")

st.markdown('<div class="subtitle">Your AI assistant for Indian laws</div>', unsafe_allow_html=True)

# Disclaimer card
st.markdown("""
<div class="disclaimer-card">
    <div class="title">
        <span class="icon">⚠️</span>
        Important Disclaimer
    </div>
    <div class="content">
        This tool is for <strong>educational and informational purposes only</strong>. 
        It does <strong>not</strong> constitute legal advice. 
        For legal decisions, please consult a qualified legal professional.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Sidebar
st.sidebar.header("Laws Indexed")

for law in get_loaded_laws():
    pdf_url = f"{API_BASE_URL}/pdf/{law}"
    display_name = law.replace("_", " ").replace(".pdf", "")
    st.sidebar.markdown(
        f'<a href="{pdf_url}" target="_blank" class="pdf-link">{display_name}</a>',
        unsafe_allow_html=True
    )

# CHAT INTERFACE
# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat input
user_question = st.chat_input(
    "Ask a legal question (e.g. Is wearing helmet compulsory?)"
)

# Handle new question
if user_question:
    st.session_state.messages.append(("user", user_question))
    with st.spinner("Thinking..."):
        response = ask_backend(user_question)
    st.session_state.messages.append(("assistant", response))

# Display chat history
for idx, (role, message) in enumerate(st.session_state.messages):
    if role == "user":
        with st.chat_message("user"):
            st.write(message)
    else:
        with st.chat_message("assistant"):
            st.write(message["answer"])

            if message["citations"]:
                with st.expander("Evidence"):

                    if st.button("View citation", key=f"multi_{idx}"):
                        with st.spinner("Generating highlighted PDF..."):
                            pdf_bytes = fetch_highlighted_pdf([message["citations"][0]])
                            if pdf_bytes:
                                show_pdf_inline(pdf_bytes)

                    citation = message["citations"][0]
                    st.markdown(
                        f"""
                        **Source:** {citation['source']}  
                        **Page:** {citation['page']}  
                        """
                    )
            else:
                st.write("No evidence found.")