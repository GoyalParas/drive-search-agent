import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_ENDPOINT = f"{BACKEND_URL}/api/chat"

st.set_page_config(page_title="Drive Search Agent", page_icon=":mag:", layout="wide")
st.title("Google Drive Conversational Search")
st.write("Ask the assistant to find files in your shared Google Drive folder.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_query" not in st.session_state:
    st.session_state.last_query = None

if "results" not in st.session_state:
    st.session_state.results = []

with st.form(key="search_form", clear_on_submit=True):
    user_input = st.text_input("Search files", placeholder="Example: Find the sales report PDF from June", key="user_input")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Searching Drive..."):
        try:
            response = requests.post(API_ENDPOINT, json={"user_message": user_input}, timeout=30)
            response.raise_for_status()
            data = response.json()
            assistant_text = data.get("response", "Sorry, I couldn't process that request.")
            st.session_state.last_query = data.get("query")
            st.session_state.results = data.get("results", [])
        except Exception as exc:
            assistant_text = f"Error: {exc}"
            st.session_state.results = []

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

if st.session_state.results:
    st.markdown("---")
    st.subheader("Search Results")
    if st.session_state.results:
        for result in st.session_state.results:
            with st.expander(f"📄 {result['name']}"):
                st.write(f"**Type:** {result['mimeType']}")
                if result.get('modifiedTime'):
                    st.write(f"**Modified:** {result['modifiedTime']}")
                if result.get('webViewLink'):
                    st.markdown(f"[Open in Drive]({result['webViewLink']})")
    else:
        st.info("No files found matching your search.")

