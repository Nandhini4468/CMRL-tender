"""
Re-extraction agent: runs when the user reports missing criteria.
Uses higher OCR sensitivity + multi-pass + page-wise extraction,
then merges new findings with the existing DataFrames.
"""
import json
import re
from typing import Dict, Tuple
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from core.ocr.ocr_pipeline import run_ocr_pipeline
from core.extraction.criteria_extractor import (
    ELIGIBILITY_SYSTEM,
    EVALUATION_SYSTEM,
    _extract_section,
    _clean_json_response,
    _remove_parent_criteria,
)


def reextract_criteria(
    file_path: str,
    existing_eligibility_df: pd.DataFrame,
    existing_evaluation_df: pd.DataFrame,
    groq_api_key: str,
    model: str,
    tesseract_cmd: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    High-sensitivity re-extraction agent.
    1. Re-run OCR with higher DPI and table-detection passes.
    2. Extract criteria page-by-page for granularity.
    3. Merge new criteria with existing, deduplicating.
    """
    # High-sensitivity OCR
    result = run_ocr_pipeline(
        file_path, tesseract_cmd,
        use_engines=["pymupdf", "tesseract"],
        high_sensitivity=True,
    )

    llm = ChatGroq(api_key=groq_api_key, model_name=model, temperature=0)

    new_eligibility_rows = []
    new_evaluation_rows = []

    for page_info in result["pages"]:
        page_text = page_info["text"]
        if len(page_text.strip()) < 30:
            continue

        elig_df, _ = _extract_section(llm, ELIGIBILITY_SYSTEM, page_text, "eligibility")
        eval_df, _ = _extract_section(llm, EVALUATION_SYSTEM, page_text, "evaluation")

        new_eligibility_rows.extend(elig_df.to_dict("records"))
        new_evaluation_rows.extend(eval_df.to_dict("records"))

    merged_eligibility = _merge_criteria(
        existing_eligibility_df,
        pd.DataFrame(new_eligibility_rows) if new_eligibility_rows else pd.DataFrame(),
        key_col="criteria_name",
    )
    merged_evaluation = _merge_criteria(
        existing_evaluation_df,
        pd.DataFrame(new_evaluation_rows) if new_evaluation_rows else pd.DataFrame(),
        key_col="criterion_description",
    )

    # Remove parent criteria superseded by sub-criteria after merge
    if "criterion_number" in merged_evaluation.columns:
        merged_evaluation["criterion_number"] = merged_evaluation["criterion_number"].fillna("").astype(str).str.strip()
        merged_evaluation = _remove_parent_criteria(merged_evaluation)

    merged_evaluation["sno"] = range(1, len(merged_evaluation) + 1)
    merged_evaluation["criteria_id"] = [f"C{i}" for i in range(1, len(merged_evaluation) + 1)]
    merged_eligibility["sno"] = range(1, len(merged_eligibility) + 1)

    return merged_eligibility, merged_evaluation


def _merge_criteria(existing: pd.DataFrame, new: pd.DataFrame, key_col: str) -> pd.DataFrame:
    """Merge new criteria into existing, skipping duplicates by key column."""
    if new.empty or key_col not in new.columns:
        return existing

    if existing.empty:
        # Deduplicate within the new batch itself before returning
        deduped = new.copy()
        deduped["_key"] = deduped[key_col].str.lower().str.strip()
        deduped = deduped.drop_duplicates(subset="_key").drop(columns=["_key"])
        return deduped.reset_index(drop=True)

    existing_keys = set(existing[key_col].str.lower().str.strip()) if key_col in existing.columns else set()

    truly_new = []
    for _, row in new.iterrows():
        val = str(row.get(key_col, "")).lower().strip()
        if val and val not in existing_keys:
            truly_new.append(row)
            existing_keys.add(val)  # prevent within-batch duplicates too

    if not truly_new:
        return existing

    combined = pd.concat([existing, pd.DataFrame(truly_new)], ignore_index=True)
    return combined
