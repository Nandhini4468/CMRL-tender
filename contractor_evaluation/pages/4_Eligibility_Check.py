import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
from utils.styling import apply_portal_styling

from utils.config import GROQ_MODEL, CHROMA_PERSIST_DIR, EMBEDDING_MODEL, OUTPUTS_DIR
from core.rag.retriever import BidderRetriever
from core.evaluation.eligibility_checker import check_eligibility, build_eligibility_summary

st.set_page_config(page_title="Step 4 — Eligibility Check", page_icon="🚇", layout="wide")
apply_portal_styling()
st.title("Step 4: Eligibility Check")
st.markdown("Check whether each bidder satisfies all eligibility criteria before full evaluation.")

if not st.session_state.get("bidders_processed"):
    st.warning("Bidder documents must be processed first. Complete Step 3.")
    st.stop()

with st.sidebar:
    groq_key = st.text_input("Groq API Key", type="password",
                              placeholder="Enter your Groq API key",
                              value=st.session_state.get("groq_api_key", ""))
    if groq_key:
        st.session_state["groq_api_key"] = groq_key

elig_df: pd.DataFrame = st.session_state.get("eligibility_df", pd.DataFrame())
bidders = st.session_state.get("bidder_folders", [])
model = st.session_state.get("groq_model", GROQ_MODEL)

if elig_df.empty:
    st.info("No eligibility criteria found. All bidders will proceed to evaluation.")
    eligible_bidders = [b["name"] for b in bidders]
    st.session_state["eligible_bidders"] = eligible_bidders
    st.session_state["eligibility_done"] = True
    st.success(f"All {len(eligible_bidders)} bidders are eligible (no eligibility criteria defined).")
    st.stop()

st.markdown(f"**{len(elig_df)} eligibility criteria** will be checked for **{len(bidders)} bidder(s)**.")

if st.button("Run Eligibility Check", type="primary"):
    api_key = st.session_state.get("groq_api_key", "")
    if not api_key:
        st.error("Groq API key required.")
        st.stop()

    all_elig_results = []
    progress = st.progress(0, text="Checking eligibility...")

    for i, bidder in enumerate(bidders):
        progress.progress(i / len(bidders), text=f"Checking {bidder['name']}...")
        retriever = BidderRetriever(CHROMA_PERSIST_DIR, bidder["name"], EMBEDDING_MODEL)
        result_df = check_eligibility(bidder["name"], elig_df, retriever, api_key, model)
        all_elig_results.append(result_df)

    progress.progress(1.0, text="Done.")

    combined = pd.concat(all_elig_results, ignore_index=True)
    summary = build_eligibility_summary(all_elig_results)

    st.session_state["eligibility_results"] = combined
    st.session_state["eligibility_summary"] = summary
    st.session_state["eligibility_done"] = True

    # Determine eligible bidders
    eligible_bidders = []
    for _, row in summary.iterrows():
        if row.get("Overall Status", "") == "ELIGIBLE":
            eligible_bidders.append(row["Bidder"])

    st.session_state["eligible_bidders"] = eligible_bidders

    st.success(f"Eligibility check complete. {len(eligible_bidders)} of {len(bidders)} bidder(s) are eligible.")

# ── Show results ──────────────────────────────────────────────────────────────
summary: pd.DataFrame = st.session_state.get("eligibility_summary", pd.DataFrame())
if not summary.empty:
    st.markdown("### Eligibility Summary")

    def color_status(val):
        if val == "ELIGIBLE":
            return "background-color: #C6EFCE; color: #276221; font-weight: bold"
        elif val == "NOT ELIGIBLE":
            return "background-color: #FFC7CE; color: #9C0006; font-weight: bold"
        return ""

    styled = summary.style.map(color_status, subset=["Overall Status"])
    st.dataframe(styled, use_container_width=True)

    eligible = st.session_state.get("eligible_bidders", [])
    not_eligible = [b["name"] for b in bidders if b["name"] not in eligible]

    if not_eligible:
        st.warning(f"The following bidders did NOT meet eligibility requirements and will be excluded from evaluation: **{', '.join(not_eligible)}**")

    if eligible:
        st.info(f"Eligible bidders proceeding to evaluation: **{', '.join(eligible)}**")
        st.success("Proceed to Step 5 — Evaluation Results.")

    # Detailed results
    detail = st.session_state.get("eligibility_results", pd.DataFrame())
    if not detail.empty:
        with st.expander("Detailed Eligibility Evidence"):
            st.dataframe(detail, use_container_width=True)

    # Download
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Eligibility Summary", index=False)
        if not detail.empty:
            detail.to_excel(writer, sheet_name="Detailed Results", index=False)
    st.download_button(
        "Download Eligibility Report",
        buffer.getvalue(),
        file_name="eligibility_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
