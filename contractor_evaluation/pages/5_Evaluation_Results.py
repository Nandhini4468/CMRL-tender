import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
from utils.styling import apply_portal_styling

from utils.config import GROQ_MODEL, CHROMA_PERSIST_DIR, EMBEDDING_MODEL
from core.rag.retriever import BidderRetriever
from core.evaluation.criterion_evaluator import evaluate_all_criteria
from core.reporting.dataframe_builder import build_all_outputs

st.set_page_config(page_title="Step 5 — Evaluation Results", page_icon="🚇", layout="wide")
apply_portal_styling()
st.title("Step 5: Bidder Evaluation & Scoring")

if not st.session_state.get("eligibility_done"):
    st.warning("Please complete Step 4 — Eligibility Check first.")
    st.stop()

with st.sidebar:
    groq_key = st.text_input("Groq API Key", type="password",
                              placeholder="Enter your Groq API key",
                              value=st.session_state.get("groq_api_key", ""))
    if groq_key:
        st.session_state["groq_api_key"] = groq_key

eval_df: pd.DataFrame = st.session_state.get("evaluation_df", pd.DataFrame())
bidder_folders: list = st.session_state.get("bidder_folders", [])
all_bidders: list = [b["name"] for b in bidder_folders]
eligible_bidders: list = st.session_state.get("eligible_bidders", all_bidders)
model = st.session_state.get("groq_model", GROQ_MODEL)

if eval_df.empty:
    st.error("No evaluation criteria found. Return to Step 1.")
    st.stop()

if not all_bidders:
    st.warning("No bidders found. Complete Step 3 first.")
    st.stop()

st.markdown(f"**{len(all_bidders)} bidder(s)** will be evaluated against **{len(eval_df)} criteria** (all bidders evaluated regardless of eligibility).")
st.markdown("Criteria IDs: " + ", ".join(eval_df.get("criteria_id", pd.Series()).tolist()))

# Show eligibility status as reference
if eligible_bidders != all_bidders:
    ineligible = [b for b in all_bidders if b not in eligible_bidders]
    st.info(f"Note: {', '.join(ineligible)} did not pass eligibility but will still be scored.")

col1, col2 = st.columns(2)
with col1:
    st.metric("Criteria Count", len(eval_df))
with col2:
    st.metric("Total Max Score", eval_df["maximum_score"].sum())

st.markdown("---")

if st.button("Run Full Evaluation", type="primary"):
    api_key = st.session_state.get("groq_api_key", "")
    if not api_key:
        st.error("Groq API key required.")
        st.stop()

    all_bidder_results = {}
    progress = st.progress(0, text="Starting evaluation...")
    status_area = st.empty()
    rate_limit_area = st.empty()

    def on_rate_limit(msg: str):
        rate_limit_area.warning(f"⏳ {msg}")

    for i, bidder_name in enumerate(all_bidders):
        progress.progress(i / len(all_bidders), text=f"Evaluating {bidder_name}...")
        status_area.info(f"Evaluating **{bidder_name}** — {len(eval_df)} criteria... (rate limits are handled automatically)")
        rate_limit_area.empty()

        retriever = BidderRetriever(CHROMA_PERSIST_DIR, bidder_name, EMBEDDING_MODEL)
        results = evaluate_all_criteria(bidder_name, eval_df, retriever, api_key, model, on_rate_limit=on_rate_limit)
        all_bidder_results[bidder_name] = results

        scores = {r["criteria_id"]: r["awarded_score"] for r in results}
        total = sum(scores.values())
        status_area.success(f"**{bidder_name}** scored: {scores} → Total: {total}")

    progress.progress(1.0, text="Evaluation complete.")
    rate_limit_area.empty()

    outputs = build_all_outputs(eval_df, all_bidder_results)
    st.session_state["scoring_df"] = outputs["scoring"]
    st.session_state["ranking_df"] = outputs["ranking"]
    st.session_state["audit_df"] = outputs["audit"]
    st.session_state["low_conf_df"] = outputs["low_confidence"]
    st.session_state["all_bidder_results"] = all_bidder_results
    st.session_state["evaluation_done"] = True

    st.success("Evaluation complete!")

# ── Show results ──────────────────────────────────────────────────────────────
if st.session_state.get("evaluation_done"):
    scoring_df: pd.DataFrame = st.session_state.get("scoring_df", pd.DataFrame())
    ranking_df: pd.DataFrame = st.session_state.get("ranking_df", pd.DataFrame())
    audit_df: pd.DataFrame = st.session_state.get("audit_df", pd.DataFrame())
    low_conf_df: pd.DataFrame = st.session_state.get("low_conf_df", pd.DataFrame())

    tab1, tab2, tab3, tab4 = st.tabs(["Scoring Matrix", "Rankings", "Audit Trail", "Low Confidence Flags"])

    with tab1:
        st.markdown("### Bidder Scoring Matrix")
        if not scoring_df.empty:
            st.dataframe(scoring_df.style.highlight_max(axis=0, color="#C6EFCE").format(
                {c: "{:.1f}" for c in scoring_df.select_dtypes("number").columns}
            ), use_container_width=True)

    with tab2:
        st.markdown("### Final Rankings")
        if not ranking_df.empty:
            st.dataframe(ranking_df, use_container_width=True)
            winner = ranking_df.iloc[0]["Bidder"] if not ranking_df.empty else "N/A"
            st.success(f"Highest ranked bidder: **{winner}**")

    with tab3:
        st.markdown("### Audit Trail")
        st.caption("Complete evidence trail for every criterion × bidder evaluation.")
        if not audit_df.empty:
            bidder_filter = st.multiselect("Filter by bidder", options=audit_df["Bidder"].unique().tolist(),
                                           default=audit_df["Bidder"].unique().tolist())
            filtered = audit_df[audit_df["Bidder"].isin(bidder_filter)]
            st.dataframe(filtered, use_container_width=True)

    with tab4:
        st.markdown("### Low Confidence Evaluations (< 70%)")
        if low_conf_df.empty:
            st.success("No low-confidence evaluations. All scores are reliable.")
        else:
            st.warning(f"{len(low_conf_df)} evaluation(s) flagged for human review.")
            st.dataframe(low_conf_df, use_container_width=True)

    st.info("Go to Step 6 to download the full report.")
