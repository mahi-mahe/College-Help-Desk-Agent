"""Streamlit frontend for the College Help Desk. Run: streamlit run app.py"""
import os

import streamlit as st

from agent import DB_PATH, answer

st.set_page_config(page_title="College Help Desk", page_icon=":mortar_board:")
st.title("College Help Desk")
st.caption("Ask about exams, the timetable, fees or billing problems.")

if not os.getenv("GROQ_API_KEY"):
    st.error("GROQ_API_KEY is missing. Add it to the .env file and restart.")
    st.stop()
if not os.path.exists(DB_PATH):
    st.error("college.db not found. Run `python setup_db.py` and restart.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

SAMPLES = [
    "When are the semester 1 exams?",
    "What is Monday's timetable?",
    "What is the pending fee for S1001?",
    "Raise a ticket for S1001: hostel fee charged twice",
]
with st.sidebar:
    st.subheader("Try a question")
    for q in SAMPLES:
        if st.button(q, use_container_width=True):
            st.session_state.pending = q
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("agent"):
            st.caption(f"Answered by: {m['agent']}")

prompt = st.chat_input("Type your question...") or st.session_state.pop("pending", None)

if prompt:
    history = "".join(
        f"{'Student' if m['role'] == 'user' else 'Help Desk'}: {m['content']}\n"
        for m in st.session_state.messages[-6:]
    )
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent_name, reply = answer(prompt, history)
            except Exception as exc:
                agent_name, reply = None, f"Sorry, something went wrong: {exc}"
        st.markdown(reply)
        if agent_name:
            st.caption(f"Answered by: {agent_name}")
    st.session_state.messages.append({"role": "assistant", "content": reply, "agent": agent_name})