import streamlit as st

API_BASE_URL = "http://localhost:8000"

def get_loaded_laws():
    # Temporary fallback until backend is ready
    return [
        "Environment_Protection_Act.pdf",
        "Motor_Vehicles_Act.pdf",
        "Consumer_Protection_Act.pdf"
    ]

st.set_page_config(
    page_title = 'ByLawBuddy',
    layout = "wide",
)

st.sidebar.header("Laws Loaded")

for law in get_loaded_laws():
    st.sidebar.write(f" -> {law}")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_question = st.chat_input(
    "Ask a legal question (e.g. Is wearing helmet compulsory?)"
)

if user_question:
    st.session_state.messages.append(("user", user_question))

for role, message in st.session_state.messages:
    if role == "user":
        with st.chat_message("user"):
            st.write(message)