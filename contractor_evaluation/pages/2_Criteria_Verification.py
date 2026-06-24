import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
from utils.styling import apply_portal_styling

from utils.config import GROQ_MODEL, TESSERACT_CMD, OUTPUTS_DIR
from core.extraction.reextractor import reextract_criteria
from core.reporting.excel_exporter import export_criteria_to_excel

st.set_page_config(page_title="Step 2 — Criteria Verification", page_icon="🚇", layout="wide")
apply_portal_styling()
st.title("Step 2: Criteria Verification & Approval")

elig_df: pd.DataFrame = st.session_state.get("eligibility_df", pd.DataFrame())
eval_df: pd.DataFrame = st.session_state.get("evaluation_df", pd.DataFrame())

if elig_df.empty and eval_df.empty:
    st.warning("No criteria extracted yet. Please complete Step 1 first.")
    st.stop()

with st.sidebar:
    groq_key = st.text_input("Groq API Key", type="password",
                              placeholder="Enter your Groq API key",
                              value=st.session_state.get("groq_api_key", ""))
    if groq_key:
        st.session_state["groq_api_key"] = groq_key

st.markdown("### Please verify whether all criteria have been extracted correctly.")
st.markdown("You can **edit**, **add**, or **delete** rows in the tables below before approving.")

# ── Eligibility Criteria Editor ───────────────────────────────────────────────
st.markdown("#### Eligibility Criteria")
edited_elig = st.data_editor(
    elig_df,
    num_rows="dynamic",
    use_container_width=True,
    key="elig_editor",
)

# ── Evaluation Criteria Editor ────────────────────────────────────────────────
st.markdown("#### Evaluation Criteria")
st.caption("Double-click any cell to edit. Add rows with the + button. Delete rows by selecting and pressing Delete.")
edited_eval = st.data_editor(
    eval_df,
    num_rows="dynamic",
    use_container_width=True,
    key="eval_editor",
)
if not edited_eval.empty:
    total_score = pd.to_numeric(edited_eval.get("maximum_score", pd.Series([0])), errors="coerce").sum()
    st.metric("Total Maximum Score", f"{total_score:.0f}")

st.markdown("---")
st.markdown("### Are all criteria correctly extracted?")

col1, col2 = st.columns(2)

with col1:
    if st.button("YES — APPROVE CRITERIA", type="primary", use_container_width=True):
        # Save edited DataFrames
        edited_elig["sno"] = range(1, len(edited_elig) + 1)
        edited_eval["sno"] = range(1, len(edited_eval) + 1)
        if "criteria_id" not in edited_eval.columns:
            edited_eval["criteria_id"] = [f"C{i}" for i in range(1, len(edited_eval) + 1)]
        edited_eval["maximum_score"] = pd.to_numeric(
            edited_eval.get("maximum_score", 0), errors="coerce"
        ).fillna(0)

        st.session_state["eligibility_df"] = edited_elig.reset_index(drop=True)
        st.session_state["evaluation_df"] = edited_eval.reset_index(drop=True)
        st.session_state["criteria_approved"] = True

        # Export to Excel
        excel_path = export_criteria_to_excel(
            str(OUTPUTS_DIR),
            st.session_state["eligibility_df"],
            st.session_state["evaluation_df"],
        )
        st.session_state["criteria_excel_path"] = excel_path

        st.success("Criteria APPROVED. You may now proceed to Step 3 — Bidder Processing.")
        st.balloons()

with col2:
    if st.button("NO — MISSING CRITERIA (Re-extract)", use_container_width=True):
        api_key = st.session_state.get("groq_api_key", "")
        pdf_path = st.session_state.get("criteria_pdf_path", "")
        model = st.session_state.get("groq_model", GROQ_MODEL)

        if not pdf_path:
            st.error("Original PDF not found. Please re-upload in Step 1.")
        elif not api_key:
            st.error("Groq API key required.")
        else:
            with st.spinner("Re-extracting with higher sensitivity — analysing page by page..."):
                new_elig, new_eval = reextract_criteria(
                    pdf_path,
                    edited_elig,
                    edited_eval,
                    api_key,
                    model,
                    TESSERACT_CMD,
                )
            st.session_state["eligibility_df"] = new_elig
            st.session_state["evaluation_df"] = new_eval
            elig_delta = len(new_elig) - len(edited_elig)
            eval_delta = len(new_eval) - len(edited_eval)
            st.success(
                f"Re-extraction complete. "
                f"Added {elig_delta} new eligibility criteria and {eval_delta} new evaluation criteria."
            )
            st.rerun()

# ── Download extracted criteria Excel ────────────────────────────────────────
if st.session_state.get("criteria_excel_path"):
    with open(st.session_state["criteria_excel_path"], "rb") as f:
        st.download_button(
            "Download Criteria Excel",
            f,
            file_name="criteria.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

if st.session_state.get("criteria_approved"):
    st.success("Criteria are APPROVED. Proceed to Step 3.")
