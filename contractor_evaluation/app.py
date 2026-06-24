import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils.styling import apply_portal_styling

st.set_page_config(
    page_title="Contractor Evaluation System",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_portal_styling()

st.title("Contractor Evaluation Automation System")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Workflow")
    st.markdown("""
    **Phase 1 — Criteria Extraction**
    1. Upload the tender/EQC criteria PDF
    2. Multi-engine OCR extracts text
    3. AI structures eligibility + evaluation criteria
    4. Review, edit, and approve criteria

    **Phase 2 — Bidder Evaluation**
    5. Upload bidder document folders
    6. OCR + RAG indexes all documents
    7. Eligibility gate checks each bidder
    8. Approved criteria scored against evidence
    9. Rankings, audit trail, and reports generated
    """)

with col2:
    st.markdown("### Status")
    eligibility_approved = st.session_state.get("criteria_approved", False)
    evaluation_done = st.session_state.get("evaluation_done", False)

    st.metric("Criteria Approved", "Yes" if eligibility_approved else "Pending")
    st.metric("Bidders Evaluated", st.session_state.get("bidders_evaluated_count", 0))
    st.metric("Evaluation Complete", "Yes" if evaluation_done else "Pending")

st.markdown("---")
st.info("Use the sidebar to navigate through each step.")

# Sidebar navigation hint
with st.sidebar:
    st.markdown("### Navigation")
    st.markdown("""
    1. Criteria Extraction
    2. Criteria Verification
    3. Bidder Processing
    4. Eligibility Check
    5. Evaluation Results
    6. Reports & Downloads
    """)
    st.markdown("---")
    groq_key = st.text_input("Groq API Key", type="password",
                              value=st.session_state.get("groq_api_key", ""),
                              help="Enter your Groq API key. Stored in session only.")
    if groq_key:
        st.session_state["groq_api_key"] = groq_key
        st.success("API key set.")
