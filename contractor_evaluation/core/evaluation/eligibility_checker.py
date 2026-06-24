import json
import re
from typing import List, Dict
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from core.rag.retriever import BidderRetriever


ELIGIBILITY_SYSTEM = """You are a procurement compliance officer.
Determine whether the bidder satisfies the given eligibility criterion based ONLY on the provided document evidence.

Respond with a valid JSON object only. No markdown. No explanation outside JSON.
Keys:
- eligible: true or false
- evidence_text: exact quote from the retrieved text that supports your decision (empty string if none)
- source_file: filename where evidence was found (empty string if none)
- page: page number (0 if unknown)
- reason: one-sentence explanation
- confidence: integer 0-100

RULES:
- If evidence is found and criterion is satisfied → eligible: true
- If no evidence found or criterion not met → eligible: false
- Never invent evidence
- Confidence < 70 means you are unsure
"""


def check_eligibility(
    bidder_name: str,
    eligibility_df: pd.DataFrame,
    retriever: BidderRetriever,
    groq_api_key: str,
    model: str,
) -> pd.DataFrame:
    """
    Check each eligibility criterion for a single bidder.
    Returns a DataFrame with eligibility results.
    """
    llm = ChatGroq(api_key=groq_api_key, model_name=model, temperature=0)
    rows = []

    for _, criterion in eligibility_df.iterrows():
        query = f"{criterion.get('criteria_name', '')} {criterion.get('criteria_description', '')}"
        chunks = retriever.retrieve(query, n_results=5)
        context = _format_context(chunks)

        user_msg = (
            f"CRITERION: {criterion.get('criteria_name', '')}\n"
            f"DESCRIPTION: {criterion.get('criteria_description', '')}\n"
            f"REQUIRED DOCUMENT: {criterion.get('document_required', '')}\n\n"
            f"RETRIEVED EVIDENCE:\n{context}"
        )

        result = _call_llm(llm, ELIGIBILITY_SYSTEM, user_msg)

        rows.append({
            "bidder": bidder_name,
            "sno": criterion.get("sno", ""),
            "criteria_name": criterion.get("criteria_name", ""),
            "criteria_description": criterion.get("criteria_description", ""),
            "eligible": result.get("eligible", False),
            "evidence_text": result.get("evidence_text", ""),
            "source_file": result.get("source_file", ""),
            "page": result.get("page", 0),
            "reason": result.get("reason", ""),
            "confidence": result.get("confidence", 0),
        })

    return pd.DataFrame(rows)


def build_eligibility_summary(all_results: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Combine per-bidder eligibility results into a summary table.
    Shows which criteria each bidder passes/fails.
    """
    if not all_results:
        return pd.DataFrame()

    combined = pd.concat(all_results, ignore_index=True)

    summary_rows = []
    for bidder, group in combined.groupby("bidder"):
        row = {"Bidder": bidder}
        all_eligible = True
        failed_criteria = []
        for _, r in group.iterrows():
            status = "PASS" if r["eligible"] else "FAIL"
            row[r["criteria_name"]] = status
            if not r["eligible"]:
                all_eligible = False
                failed_criteria.append(r["criteria_name"])
        row["Overall Status"] = "ELIGIBLE" if all_eligible else "NOT ELIGIBLE"
        row["Failed Criteria"] = ", ".join(failed_criteria) if failed_criteria else "None"
        summary_rows.append(row)

    return pd.DataFrame(summary_rows)


def _format_context(chunks: List[Dict]) -> str:
    if not chunks:
        return "No evidence retrieved."
    parts = []
    for c in chunks:
        parts.append(f"[File: {c['source_file']}, Page: {c['page']}, Similarity: {c['similarity']}%]\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def _call_llm(llm: ChatGroq, system: str, user: str) -> Dict:
    try:
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        response = llm.invoke(messages)
        raw = response.content.strip()
        raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return {"eligible": False, "evidence_text": "", "source_file": "", "page": 0,
            "reason": "LLM error", "confidence": 0}
