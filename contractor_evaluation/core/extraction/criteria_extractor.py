import json
import re
from typing import Dict, Tuple
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage


ELIGIBILITY_SYSTEM = """You are an expert procurement analyst specialising in Indian government tenders (NIT/RFP/EQC documents).
Your task is to extract ALL ELIGIBILITY CRITERIA from the document.

Eligibility criteria are PASS/FAIL requirements. Look for:
- Technical qualification requirements (registration, licenses, certifications)
- Financial requirements (annual turnover, net worth, EMD/bid security amounts)
- Experience requirements (years in business, past project values, similar work done)
- Legal/statutory requirements (PAN, GST, ESI, EPF registration)
- Any mandatory documents listed (e.g., "the bidder shall possess...", "minimum criteria...", "qualification criteria...")

Even if the document uses tables, numbered lists, or section headings like "Pre-Qualification Criteria",
"Eligibility Criteria", "Technical Bid Requirements", extract all such requirements.

Return a valid JSON array only. No explanation, no markdown, no preamble.
Each object must have exactly these keys:
- sno: serial number (integer starting at 1)
- criteria_name: short descriptive name (string, e.g. "Annual Turnover", "Similar Works Experience")
- criteria_description: full requirement text as stated in the document (string)
- document_required: documents/certificates needed to prove this criterion (string)

If no eligibility criteria are found at all, return [].
"""

EVALUATION_SYSTEM = """You are an expert procurement analyst specialising in Indian government tenders (NIT/RFP/EQC documents).
Your task is to extract ALL EVALUATION / TECHNICAL SCORING CRITERIA from the document.

Evaluation criteria have numeric marks/scores/weights and determine how bidders are ranked.
Look for sections titled: "Technical Evaluation", "Marking Scheme", "Scoring Criteria", "Quality and Cost Based Selection",
"Point System", "Evaluation Criteria", or tables with columns like "Criteria", "Marks", "Weightage", "Score".

Common scoring criteria in Indian government tenders:
- Financial capability / turnover (marks based on slab)
- Experience / past work (marks based on value or number of projects)
- Technical capacity / manpower / equipment
- Methodology / work plan
- Price / financial bid score

Return a valid JSON array only. No explanation, no markdown, no preamble.
Each object must have exactly these keys:
- sno: serial number (integer starting at 1)
- criterion_description: full description of what is evaluated (string)
- maximum_score: maximum marks/points for this criterion (number — use 0 if not specified)
- supporting_evidence: documents/certificates needed to prove this criterion (string)
- scoring_rules: how marks are awarded — tiers, slabs, or formula if stated (string)

If no scoring/evaluation criteria with marks are found, return [].
"""


def extract_criteria_from_text(
    ocr_text: str, groq_api_key: str, model: str
) -> Tuple[pd.DataFrame, pd.DataFrame, str, str]:
    """
    Use Groq LLM to extract eligibility and evaluation criteria from OCR text.
    Returns (eligibility_df, evaluation_df, raw_eligibility_response, raw_evaluation_response).
    """
    llm = ChatGroq(api_key=groq_api_key, model_name=model, temperature=0)

    # ~20 000 chars ≈ 5 000 tokens — keeps well within Groq free-tier daily limits
    text_chunk = ocr_text[:20000]

    eligibility_df, raw_elig = _extract_section(llm, ELIGIBILITY_SYSTEM, text_chunk, "eligibility")
    evaluation_df, raw_eval = _extract_section(llm, EVALUATION_SYSTEM, text_chunk, "evaluation")

    return eligibility_df, evaluation_df, raw_elig, raw_eval


def _extract_section(llm: ChatGroq, system_prompt: str, text: str, section: str) -> Tuple[pd.DataFrame, str]:
    user_msg = f"Extract the {section} criteria from the following document text:\n\n{text}"
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_msg)]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        raw_original = raw
        raw = _clean_json_response(raw)
        data = json.loads(raw)
        if not isinstance(data, list):
            data = []
    except Exception as e:
        msg = str(e)
        if "rate_limit_exceeded" in msg or "429" in msg:
            raise RuntimeError(
                f"Groq rate limit reached for this model. "
                f"In the sidebar, switch the Groq Model to 'mixtral-8x7b-32768' or 'llama-3.1-8b-instant' "
                f"(each model has its own separate daily quota). Original error: {e}"
            ) from e
        raise RuntimeError(f"LLM extraction failed for '{section}': {e}") from e

    if section == "eligibility":
        columns = ["sno", "criteria_name", "criteria_description", "document_required"]
        df = pd.DataFrame(data, columns=columns) if data else pd.DataFrame(columns=columns)
        if not df.empty:
            df["sno"] = range(1, len(df) + 1)
    else:
        columns = ["sno", "criterion_description", "maximum_score", "supporting_evidence", "scoring_rules"]
        df = pd.DataFrame(data, columns=columns) if data else pd.DataFrame(columns=columns)
        if not df.empty:
            df["sno"] = range(1, len(df) + 1)
            df["criteria_id"] = [f"C{i}" for i in range(1, len(df) + 1)]
            df["maximum_score"] = pd.to_numeric(df["maximum_score"], errors="coerce").fillna(0)

    return df, raw_original


def _clean_json_response(raw: str) -> str:
    """Strip markdown code fences and extract first JSON array."""
    raw = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        return match.group(0)
    return raw


def rebuild_evaluation_df_from_edited(edited_data: list) -> pd.DataFrame:
    """Reconstruct evaluation DataFrame after user edits in Streamlit data editor."""
    df = pd.DataFrame(edited_data)
    if "criteria_id" not in df.columns:
        df["criteria_id"] = [f"C{i}" for i in range(1, len(df) + 1)]
    df["sno"] = range(1, len(df) + 1)
    df["maximum_score"] = pd.to_numeric(df.get("maximum_score", 0), errors="coerce").fillna(0)
    return df
