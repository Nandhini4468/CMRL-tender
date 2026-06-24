import streamlit as st
import sys, os, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
from utils.styling import apply_portal_styling

from utils.config import OUTPUTS_DIR
from core.reporting.excel_exporter import export_all_to_excel

st.set_page_config(page_title="Step 6 — Reports", page_icon="🚇", layout="wide")
apply_portal_styling()
st.title("Step 6: Reports & Downloads")

if not st.session_state.get("evaluation_done"):
    st.warning("Evaluation not complete. Please finish Steps 1–5 first.")
    st.stop()

eligibility_df = st.session_state.get("eligibility_df", pd.DataFrame())
evaluation_df = st.session_state.get("evaluation_df", pd.DataFrame())
eligibility_summary_df = st.session_state.get("eligibility_summary", pd.DataFrame())
scoring_df = st.session_state.get("scoring_df", pd.DataFrame())
ranking_df = st.session_state.get("ranking_df", pd.DataFrame())
audit_df = st.session_state.get("audit_df", pd.DataFrame())
low_conf_df = st.session_state.get("low_conf_df", pd.DataFrame())

# ── Summary metrics ───────────────────────────────────────────────────────────
st.markdown("### Evaluation Summary")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Bidders Evaluated", len(scoring_df) if not scoring_df.empty else 0)
with col2:
    st.metric("Criteria Evaluated", len(evaluation_df))
with col3:
    winner_row = ranking_df.iloc[0] if not ranking_df.empty else None
    st.metric("Top Ranked Bidder", winner_row["Bidder"] if winner_row is not None else "N/A")
with col4:
    st.metric("Low Confidence Flags", len(low_conf_df))

# ── Rankings ──────────────────────────────────────────────────────────────────
st.markdown("### Final Rankings")
if not ranking_df.empty:
    st.dataframe(ranking_df, use_container_width=True)

# ── Download full Excel report ────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Download Full Excel Report")
st.markdown("One workbook with all sheets: Eligibility Criteria, Evaluation Criteria, Eligibility Summary, Scoring Matrix, Rankings, Audit Trail, Low Confidence Flags.")

if st.button("Generate & Download Full Report", type="primary"):
    with st.spinner("Generating Excel workbook..."):
        excel_path = export_all_to_excel(
            str(OUTPUTS_DIR),
            eligibility_df,
            evaluation_df,
            eligibility_summary_df,
            scoring_df,
            ranking_df,
            audit_df,
            low_conf_df,
        )
        st.session_state["full_report_path"] = excel_path

    with open(excel_path, "rb") as f:
        st.download_button(
            label="Download Full Evaluation Report (Excel)",
            data=f,
            file_name=os.path.basename(excel_path),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    st.success(f"Report saved to: {excel_path}")

# ── Individual sheet downloads ────────────────────────────────────────────────
st.markdown("### Download Individual Sheets")
col1, col2, col3 = st.columns(3)

def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, sheet_name=sheet_name, index=False)
    return buf.getvalue()

with col1:
    if not scoring_df.empty:
        st.download_button("Scoring Matrix", df_to_excel_bytes(scoring_df, "Scoring"),
                           file_name="scoring_matrix.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if not ranking_df.empty:
        st.download_button("Rankings", df_to_excel_bytes(ranking_df, "Rankings"),
                           file_name="rankings.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with col2:
    if not audit_df.empty:
        st.download_button("Audit Trail", df_to_excel_bytes(audit_df, "Audit"),
                           file_name="audit_trail.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with col3:
    if not low_conf_df.empty:
        st.download_button("Low Confidence Flags", df_to_excel_bytes(low_conf_df, "LowConf"),
                           file_name="low_confidence.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if not eligibility_summary_df.empty:
        st.download_button("Eligibility Summary", df_to_excel_bytes(eligibility_summary_df, "Eligibility"),
                           file_name="eligibility_summary.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ── Audit preview ─────────────────────────────────────────────────────────────
if not audit_df.empty:
    st.markdown("---")
    st.markdown("### Full Audit Trail Preview")
    st.dataframe(audit_df, use_container_width=True)
