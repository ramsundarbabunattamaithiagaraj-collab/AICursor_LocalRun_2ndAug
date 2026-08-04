from __future__ import annotations

import streamlit as st

from utils.api_client import ApiError, api_get, api_post

st.set_page_config(page_title="RAG Assistant - RetailIQ", page_icon="🧠", layout="wide")

st.title("🧠 Retail Knowledge Assistant (RAG)")
st.caption(
    "Ingest retail PDFs (product catalogs, price lists, planograms, invoices, flyers) and ask "
    "questions in natural language. Text, tables, and images are all extracted and citable."
)

tab_ingest, tab_query, tab_docs = st.tabs(["📤 Ingest PDF", "💬 Ask a Question", "📚 Ingested Documents"])

with tab_ingest:
    uploaded_file = st.file_uploader("Upload a retail PDF", type=["pdf"])
    if uploaded_file and st.button("Ingest document"):
        with st.spinner("Extracting text, tables, and images, then indexing into the vector store..."):
            try:
                result = api_post(
                    "/api/v1/rag/ingest",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                )
                st.success(
                    f"Ingested '{result['file_name']}': {result['chunk_count']} chunks "
                    f"({', '.join(result['content_types'])}). Status: {result['status']}"
                )
            except ApiError as exc:
                st.error(f"Ingestion failed: {exc.detail}")

with tab_query:
    question = st.text_area("Ask a question about your ingested retail documents", height=100)
    top_k = st.slider("Number of source chunks to retrieve", 1, 10, 5)
    if st.button("Ask", disabled=not question.strip()):
        with st.spinner("Searching the knowledge base..."):
            try:
                response = api_post("/api/v1/rag/query", {"question": question, "top_k": top_k})
                st.markdown("### Answer")
                st.write(response["answer"])

                col1, col2 = st.columns(2)
                col1.metric("Confidence", f"{response['confidence']*100:.1f}%")
                col2.metric("Context Relevance", f"{response['context_relevance']*100:.1f}%")

                st.markdown("### Sources")
                for source in response["sources"]:
                    with st.expander(f"{source['document']} — page {source['page']} — {source['content_type']} (score {source['score']})"):
                        st.write(source["snippet"])
            except ApiError as exc:
                st.error(f"Query failed: {exc.detail}")

with tab_docs:
    try:
        documents = api_get("/api/v1/rag/documents")
    except ApiError as exc:
        st.error(f"Could not load documents: {exc.detail}")
        documents = []
    if documents:
        import pandas as pd

        st.dataframe(pd.DataFrame(documents), use_container_width=True, hide_index=True)
    else:
        st.info("No documents ingested yet.")
