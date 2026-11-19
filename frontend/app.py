from __future__ import annotations

import os
import uuid

import requests
import streamlit as st

st.set_page_config(page_title="eCommSupport AI", page_icon=":material/support_agent:", layout="centered")
st.title("eCommSupport AI")
st.caption("Ask about products, orders, delivery, returns, and store policies.")

with st.sidebar:
    st.subheader("Support session")
    customer_id = st.text_input("Customer ID", value="demo-customer", max_chars=40)
    retrieval_strategy = st.selectbox(
        "Policy retrieval strategy",
        options=["simple", "hyde", "multi_query"],
        help="HyDE and multi-query require OpenAI; all modes use the configured Pinecone index.",
    )
    api_url = st.text_input(
        "Backend API URL",
        value=os.getenv("ECOMM_API_URL", "http://127.0.0.1:8017"),
    ).rstrip("/")
    st.caption("Demo customer IDs are not authentication. Use an identity provider before production.")
    if st.button("Clear conversation", width="stretch"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state or not st.session_state.session_id:
    st.session_state.session_id = str(uuid.uuid4())

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.write(f"{source['title'] or source['source']} — {source['source']}")
        if message.get("tools"):
            st.caption("Tools used: " + ", ".join(message["tools"]))

if question := st.chat_input("How can I help with your order or product?", max_chars=2000):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        try:
            result = requests.post(
                f"{api_url}/chat",
                json={
                    "question": question,
                    "session_id": st.session_state.session_id,
                    "customer_id": customer_id,
                    "retrieval_strategy": retrieval_strategy,
                },
                timeout=120,
            )
            result.raise_for_status()
            result = result.json()
            st.markdown(result["answer"])
            if result["sources"]:
                with st.expander("Sources"):
                    for source in result["sources"]:
                        st.write(f"{source['title'] or source['source']} — {source['source']}")
            st.caption(
                f"Model: {result['model'] or 'guardrail'} · "
                f"Latency: {result['latency_ms']} ms"
                + (f" · Tools: {', '.join(result['tools'])}" if result["tools"] else "")
            )
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                    "tools": result["tools"],
                }
            )
        except Exception as exc:
            st.error(f"The support request could not be completed: {exc}")
