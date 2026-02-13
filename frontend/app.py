import streamlit as st
import requests
import uuid
from pathlib import Path

HIGHLIGHT_DIR = Path("highlighted_pdfs_frontend")
HIGHLIGHT_DIR.mkdir(exist_ok=True)

API_BASE_URL = "http://localhost:8000"

def get_loaded_laws():
    # Temporary fallback until backend is ready
    return [
        "Environment_Protection_Act.pdf",
        "Motor_Vehicles_Act.pdf",
        "Consumer_Protection_Act.pdf"
    ]

def ask_backend(question: str):
    try:
        response = requests.post(
            f"{API_BASE_URL}/ask",
            json = {"question": question},
            timeout = 10
        )
        return response.json()
    except Exception as e:
        return{
            "answer": "Sorry, I could not answer your question. Please try again later.",
            "citations": []
        }


def fetch_highlighted_pdf(citation: dict):
    try:
        response = requests.post(
            f"{API_BASE_URL}/highlight",
            json = {
                "pdf_name": citation["source"],
                "page": citation["page"],
                "snippet": citation["snippet"]
            },
            timeout = 10
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


st.set_page_config(
    page_title = 'ByLawBuddy',
    layout = "wide",
)

st.title("ByLawBuddy")

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
                    for i, citation in enumerate(message["citations"]):
                        st.markdown(
                            f"""
                            **Source:** {citation['source']}  
                            **Page:** {citation['page']}  

                            > {citation['snippet']}
                            """
                        )
                        
                        if st.button(
                            f"View citation ({i+1})",
                            key=f"highlight_{len(st.session_state.messages)}_{i}"
                        ):
                            with st.spinner("Opening highlighted page..."):
                                pdf_path = fetch_highlighted_pdf(citation)
                                
                                if pdf_path:
                                    with open(pdf_path, "rb") as pdf_file:
                                        st.download_button(
                                            label="Open highlighted PDF",
                                            data=pdf_file,
                                            file_name=pdf_path.name,
                                            mime="application/pdf"
                                        )
            else:
                st.write("No evidence found.")
