import logging
import os
import tempfile
from pathlib import Path

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

import streamlit as st

from src.graph import build_graph
from src.llm import get_llm
from src.observability import timed_invoke
from src.retrieval import RetrievalPipeline

STORAGE_PATH = Path("data/qdrant_streamlit")
LOG_PATH = Path("data/logs/streamlit.jsonl")


@st.cache_resource
def load_pipeline() -> RetrievalPipeline:
    return RetrievalPipeline(storage_path=STORAGE_PATH)


@st.cache_resource
def load_graph(_pipeline: RetrievalPipeline):
    llm = get_llm("openai")
    return build_graph(_pipeline, llm)


st.set_page_config(page_title="papermind", page_icon="📄")
st.title("papermind — ask your PDF")

pipeline = load_pipeline()
graph = load_graph(pipeline)

uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
if uploaded_file is not None and st.button("Ingest PDF"):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = Path(tmp_file.name)
    chunk_count = pipeline.ingest(tmp_path)
    st.session_state["ingested"] = True
    st.success(f"Ingested {chunk_count} chunks from {uploaded_file.name}")

question = st.text_input("Ask a question about the uploaded PDF")
if question:
    if not st.session_state.get("ingested"):
        st.warning("Upload and ingest a PDF first.")
    else:
        result = timed_invoke(graph, question, log_path=LOG_PATH)
        st.markdown(f"**Answer:** {result['answer']}")
        st.caption(f"Grounded: {result['grounded']}")
        if result["chunks"]:
            with st.expander("Retrieved pages"):
                for chunk in result["chunks"]:
                    st.write(f"Page {chunk['page_label']}: {chunk['text'][:200]}...")
