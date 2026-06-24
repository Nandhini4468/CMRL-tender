import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.styling import apply_portal_styling

from utils.config import TESSERACT_CMD, CHROMA_PERSIST_DIR, EMBEDDING_MODEL, BIDDERS_DIR
from utils.file_utils import get_bidder_folders, save_uploaded_folder
from core.ocr.ocr_pipeline import extract_all_bidder_docs
from core.rag.retriever import BidderRetriever

st.set_page_config(page_title="Step 3 — Bidder Processing", page_icon="🚇", layout="wide")
apply_portal_styling()
st.title("Step 3: Bidder Document Processing")

if not st.session_state.get("criteria_approved"):
    st.warning("Criteria must be approved before processing bidders. Complete Steps 1 & 2 first.")
    st.stop()

with st.sidebar:
    groq_key = st.text_input("Groq API Key", type="password",
                              placeholder="Enter your Groq API key",
                              value=st.session_state.get("groq_api_key", ""))
    if groq_key:
        st.session_state["groq_api_key"] = groq_key

    st.markdown("### OCR Settings")
    max_workers = st.slider("Parallel file threads", 1, 8, 4,
                            help="Higher = faster for many files, but uses more CPU/RAM")
    use_cache = st.checkbox("Use OCR cache", value=True,
                            help="Skip re-processing files that were already OCR'd")
    engines = st.multiselect(
        "OCR Engines",
        ["pymupdf", "tesseract", "unlimited_ocr"],
        default=["pymupdf", "tesseract"],
        help="unlimited_ocr = Baidu Unlimited-OCR (AI model, slower but more accurate on complex scans)",
    )
    if "unlimited_ocr" in engines:
        try:
            import torch  # noqa: F401
            st.info("Baidu Unlimited-OCR will download the model on first use (~1–2 GB). This may take a few minutes.")
        except ImportError:
            st.warning("Unlimited-OCR requires torch/transformers which are not available in this environment. It will be skipped automatically.")

# ── Input method ─────────────────────────────────────────────────────────────
input_method = st.radio("How would you like to provide bidder documents?", [
    "Use default bidder folder (data/bidders/)",
    "Upload bidder files manually",
])

bidders = []

if input_method == "Use default bidder folder (data/bidders/)":
    st.info(f"Place bidder sub-folders inside: `{BIDDERS_DIR}`")
    if st.button("Scan Bidder Folders"):
        bidders = get_bidder_folders(str(BIDDERS_DIR))
        st.session_state["bidder_folders"] = bidders
        if not bidders:
            st.warning("No bidder folders found.")
        else:
            st.success(f"Found {len(bidders)} bidder(s): {', '.join(b['name'] for b in bidders)}")
    bidders = st.session_state.get("bidder_folders", [])
else:
    bidder_name_input = st.text_input("Bidder Name")
    uploaded_files = st.file_uploader(
        "Upload bidder documents (PDF, DOCX, images)",
        type=["pdf", "docx", "png", "jpg", "jpeg", "tiff"],
        accept_multiple_files=True,
    )
    if st.button("Add Bidder") and bidder_name_input and uploaded_files:
        folder_path = save_uploaded_folder(uploaded_files, bidder_name_input, str(BIDDERS_DIR))
        existing = st.session_state.get("bidder_folders", [])
        existing = [b for b in existing if b["name"] != bidder_name_input]
        existing.append({
            "name": bidder_name_input,
            "path": folder_path,
            "files": [{"name": f.name, "path": os.path.join(folder_path, f.name),
                        "ext": os.path.splitext(f.name)[1].lower()} for f in uploaded_files],
        })
        st.session_state["bidder_folders"] = existing
        st.success(f"Added {len(uploaded_files)} file(s) for '{bidder_name_input}'.")
    bidders = st.session_state.get("bidder_folders", [])

# ── Show detected bidders ─────────────────────────────────────────────────────
if bidders:
    st.markdown(f"### {len(bidders)} Bidder(s) Detected")
    total_files = sum(len(b["files"]) for b in bidders)
    st.caption(f"Total files to process: {total_files} across {len(bidders)} bidder(s)")

    for b in bidders:
        with st.expander(f"{b['name']} — {len(b['files'])} file(s)"):
            for f in b["files"]:
                st.write(f"• {f['name']}")

    st.info(
        "**Speed tip:** Digital PDFs process in seconds via PyMuPDF. "
        "Tesseract only runs on scanned/image pages. "
        "Previously processed files are served from cache instantly."
    )

    if st.button("Process All Bidder Documents (OCR + Index)", type="primary"):
        bidder_index_status = {}
        outer_progress = st.progress(0, text="Processing bidders...")

        for bidder_idx, bidder in enumerate(bidders):
            st.markdown(f"#### {bidder['name']}")
            file_log = st.empty()
            file_lines = []

            def on_file_done(file_name, status, _lines=file_lines, _log=file_log):
                _lines.append(f"✓ {status}")
                _log.text("\n".join(_lines))

            with st.spinner(f"OCR: {bidder['name']} ({len(bidder['files'])} files, {max_workers} threads)..."):
                pages = extract_all_bidder_docs(
                    bidder["files"],
                    TESSERACT_CMD,
                    max_workers=4,
                    use_engines=engines,
                    progress_callback=on_file_done,
                )

            total_chars = sum(len(p["text"]) for p in pages)
            st.write(f"**Pages extracted:** {len(pages)} | **Characters:** ~{total_chars:,}")

            with st.spinner(f"Indexing {bidder['name']} into ChromaDB..."):
                retriever = BidderRetriever(CHROMA_PERSIST_DIR, bidder["name"], EMBEDDING_MODEL)
                retriever.delete()
                retriever = BidderRetriever(CHROMA_PERSIST_DIR, bidder["name"], EMBEDDING_MODEL)
                retriever.index_pages(pages)
                chunk_count = retriever.count()

            st.write(f"**Chunks indexed:** {chunk_count}")
            bidder_index_status[bidder["name"]] = {
                "pages": len(pages),
                "chunks": chunk_count,
                "chars": total_chars,
            }

            outer_progress.progress(
                (bidder_idx + 1) / len(bidders),
                text=f"Done: {bidder['name']} ({bidder_idx+1}/{len(bidders)})"
            )

        st.session_state["bidder_index_status"] = bidder_index_status
        st.session_state["bidders_processed"] = True
        st.session_state["bidders_evaluated_count"] = len(bidders)

        st.success("All bidder documents processed and indexed. Proceed to Step 4.")
        import pandas as pd
        st.dataframe(
            pd.DataFrame([
                {"Bidder": k, "Pages": v["pages"], "Chunks Indexed": v["chunks"], "Characters": v["chars"]}
                for k, v in bidder_index_status.items()
            ]),
            use_container_width=True,
        )
