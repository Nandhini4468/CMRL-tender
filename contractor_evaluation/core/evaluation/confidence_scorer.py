from typing import List, Dict
import pandas as pd

LOW_CONFIDENCE_THRESHOLD = 70


def compute_overall_confidence(result: Dict) -> float:
    """Compute overall confidence as weighted average of retrieval + evaluation confidence."""
    ret_conf = float(result.get("retrieval_confidence", 0))
    eval_conf = float(result.get("evaluation_confidence", 0))
    ocr_conf = float(result.get("ocr_confidence", 95))
    return round((ret_conf * 0.35 + eval_conf * 0.45 + ocr_conf * 0.20), 2)


def flag_low_confidence(results: List[Dict]) -> List[Dict]:
    """Add 'low_confidence' flag to each result dict."""
    flagged = []
    for r in results:
        r = dict(r)
        overall = compute_overall_confidence(r)
        r["overall_confidence"] = overall
        r["low_confidence"] = overall < LOW_CONFIDENCE_THRESHOLD
        flagged.append(r)
    return flagged


def build_low_confidence_report(all_results: List[Dict]) -> pd.DataFrame:
    """Build a DataFrame of all low-confidence evaluations for human review."""
    flagged = [r for r in all_results if r.get("low_confidence", False)]
    if not flagged:
        return pd.DataFrame(columns=[
            "bidder", "criteria_id", "criterion_description",
            "awarded_score", "overall_confidence", "reasoning",
        ])
    return pd.DataFrame(flagged)[[
        "bidder", "criteria_id", "criterion_description",
        "awarded_score", "overall_confidence", "reasoning",
        "source_file", "page", "evidence_text",
    ]]
