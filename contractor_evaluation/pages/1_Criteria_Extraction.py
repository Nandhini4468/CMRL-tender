import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.styling import apply_portal_styling

from utils.config import GROQ_API_KEY, GROQ_MODEL, TESSERACT_CMD, OUTPUTS_DIR
from utils.file_utils import save_uploaded_file
from core.ocr.ocr_pipeline import run_ocr_pipeline
from core.extraction.criteria_extractor import extract_criteria_from_text

st.set_page_config(page_title="Step 1 — Criteria Extraction", page_icon="🚇", layout="wide")
apply_portal_styling()
st.title("Step 1: Criteria Extraction")
st.markdown("Upload the tender/EQC criteria document. The system will OCR and extract all eligibility and evaluation criteria.")

# ── Sidebar config ──────────────────────────────────────────────────────────
with st.sidebar:
    groq_key = st.text_input("Groq API Key", type="password",
                              placeholder="Enter your Groq API key",
                              value=st.session_state.get("groq_api_key", GROQ_API_KEY))
    if groq_key:
        st.session_state["groq_api_key"] = groq_key
    model = st.selectbox("Groq Model", [
        "llama-3.3-70b-versatile", "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768", "llama-3.1-8b-instant",
    ], index=0)
    st.session_state["groq_model"] = model

    engines = st.multiselect("OCR Engines", ["pymupdf", "tesseract"],
                              default=["pymupdf", "tesseract"])
    dpi = st.slider("OCR DPI (for scanned PDFs)", 150, 600, 300, step=50)

# ── Upload ───────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Upload Criteria PDF", type=["pdf", "png", "jpg", "jpeg", "tiff"])

if uploaded:
    api_key = st.session_state.get("groq_api_key", "")
    if not api_key:
        st.error("Please enter your Groq API key in the sidebar.")
        st.stop()

    with st.spinner("Saving file..."):
        file_path = save_uploaded_file(uploaded, str(OUTPUTS_DIR))

    st.success(f"File saved: {uploaded.name}")
    st.session_state["criteria_pdf_path"] = file_path

    if st.button("Run OCR + Extract Criteria", type="primary"):
        # ── OCR ─────────────────────────────────────────────────────────────
        with st.spinner("Running multi-engine OCR... this may take a minute for scanned PDFs."):
            ocr_result = run_ocr_pipeline(file_path, TESSERACT_CMD, use_engines=engines)

        total_chars = len(ocr_result["full_text"])
        st.info(f"OCR complete: {ocr_result['total_pages']} pages, ~{total_chars} characters extracted. "
                f"Average confidence: {ocr_result['avg_confidence']}%")

        if total_chars < 100:
            st.warning("Very little text extracted. Try enabling more OCR engines or use a higher DPI.")

        with st.expander("Preview extracted raw text"):
            st.text(ocr_result["full_text"][:3000] + ("..." if total_chars > 3000 else ""))

        st.session_state["ocr_full_text"] = ocr_result["full_text"]
        st.session_state["ocr_result"] = ocr_result

        # ── LLM Extraction ───────────────────────────────────────────────────
        with st.spinner("AI is structuring eligibility and evaluation criteria..."):
            try:
                elig_df, eval_df, raw_elig, raw_eval = extract_criteria_from_text(
                    ocr_result["full_text"], api_key, model
                )
            except Exception as e:
                st.error(f"Criteria extraction failed: {e}")
                st.stop()

        st.session_state["eligibility_df"] = elig_df
        st.session_state["evaluation_df"] = eval_df
        st.session_state["criteria_approved"] = False

        st.success("Extraction complete! Proceed to Step 2 to verify and approve.")

        # ── Preview ──────────────────────────────────────────────────────────
        st.markdown("### Eligibility Criteria (Preview)")
        st.dataframe(elig_df, use_container_width=True)

        st.markdown(f"### Evaluation Criteria (Preview) — {len(eval_df)} criteria found")
        st.dataframe(eval_df, use_container_width=True)

        total_score = eval_df["maximum_score"].sum() if not eval_df.empty else 0
        st.metric("Total Maximum Score", total_score)

        with st.expander("Debug: Raw LLM responses"):
            st.markdown("**Eligibility response:**")
            st.code(raw_elig, language="json")
            st.markdown("**Evaluation response:**")
            st.code(raw_eval, language="json")

        st.info("Go to **Step 2 — Criteria Verification** to review, edit, and approve.")
