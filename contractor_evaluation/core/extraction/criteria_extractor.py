import json
import re
from typing import Dict, Tuple
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage


ELIGIBILITY_SYSTEM = """You are an expert procurement analyst. Your task is to extract ELIGIBILITY CRITERIA
from a tender/evaluation document.

Eligibility criteria are PASS/FAIL requirements that bidders must satisfy to participate.
They are typically stated as mandatory requirements, qualifications, or minimum standards.

Return a valid JSON array only. No explanation. No markdown.
Each object must have exactly these keys:
- sno: serial number (integer)
- criteria_name: short name (string)
- criteria_description: full description (string)
- document_required: documents/evidence required (string)

If no clear eligibility criteria are found, return an empty array [].
"""

EVALUATION_SYSTEM = """You are an expert procurement analyst. Your task is to extract EVALUATION/SCORING CRITERIA
from a tender/evaluation document.

Evaluation criteria have associated point scores/weights. They determine how bidders are ranked.

Return a valid JSON array only. No explanation. No markdown.
Each object must have exactly these keys:
- sno: serial number (integer)
- criterion_description: full description of what is being evaluated (string)
- maximum_score: numeric maximum points for this criterion (number)
- supporting_evidence: what documents/evidence are needed to score (string)
- scoring_rules: describe how partial/tiered scoring works if applicable (string)

If no scoring criteria are found, return an empty array [].
"""


def extract_criteria_from_text(
    ocr_text: str, groq_api_key: str, model: str
) -> Tuple[pd.DataFrame, pd.DataFrame, str, str]:
    """
    Use Groq LLM to extract eligibility and evaluation criteria from OCR text.
    Returns (eligibility_df, evaluation_df, raw_eligibility_response, raw_evaluation_response).
    """
    llm = ChatGroq(api_key=groq_api_key, model_name=model, temperature=0)

    text_chunk = ocr_text[:30000]

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
