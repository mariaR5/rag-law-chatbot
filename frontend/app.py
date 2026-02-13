import streamlit as st
import requests

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
