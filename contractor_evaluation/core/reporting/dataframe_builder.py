from typing import List, Dict
import pandas as pd

from core.evaluation.confidence_scorer import flag_low_confidence, build_low_confidence_report


def build_scoring_dataframe(all_bidder_results: Dict[str, List[Dict]], evaluation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the bidder × criterion scoring matrix.

    | Bidder | C1 | C2 | C3 | Total |
    """
    criteria_ids = evaluation_df["criteria_id"].tolist()
    rows = []
    for bidder, results in all_bidder_results.items():
        row = {"Bidder": bidder}
        total = 0.0
        for result in results:
            cid = result.get("criteria_id", "")
            score = float(result.get("awarded_score", 0))
            row[cid] = score
            total += score
        row["Total"] = round(total, 2)
        rows.append(row)

    df = pd.DataFrame(rows)
    col_order = ["Bidder"] + criteria_ids + ["Total"]
    existing_cols = [c for c in col_order if c in df.columns]
    return df[existing_cols].fillna(0)


def build_ranking_dataframe(scoring_df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort bidders by Total score descending, assign ranks, handle ties.

    | Rank | Bidder | Total Score |
    """
    if scoring_df.empty:
        return pd.DataFrame(columns=["Rank", "Bidder", "Total Score"])

    sorted_df = scoring_df[["Bidder", "Total"]].sort_values("Total", ascending=False).reset_index(drop=True)
    sorted_df = sorted_df.rename(columns={"Total": "Total Score"})

    # Dense ranking (ties share same rank)
    sorted_df["Rank"] = sorted_df["Total Score"].rank(method="dense", ascending=False).astype(int)
    return sorted_df[["Rank", "Bidder", "Total Score"]]


def build_audit_dataframe(all_bidder_results: Dict[str, List[Dict]]) -> pd.DataFrame:
    """
    Detailed audit trail for every criterion × bidder evaluation.

    | Bidder | Criterion | Max Score | Awarded Score | Evidence | Source File | Page |
    """
    rows = []
    for bidder, results in all_bidder_results.items():
        for r in results:
            rows.append({
                "Bidder": bidder,
                "Criterion ID": r.get("criteria_id", ""),
                "Criterion Description": r.get("criterion_description", ""),
                "Max Score": r.get("maximum_score", 0),
                "Awarded Score": r.get("awarded_score", 0),
                "Evidence Text": r.get("evidence_text", "Evidence Not Found"),
                "Source File": r.get("source_file", ""),
                "Page": r.get("page", 0),
                "Reasoning": r.get("reasoning", ""),
                "Retrieval Confidence": r.get("retrieval_confidence", 0),
                "Evaluation Confidence": r.get("evaluation_confidence", 0),
                "Overall Confidence": r.get("overall_confidence", 0),
                "Low Confidence Flag": r.get("low_confidence", False),
            })
    return pd.DataFrame(rows)


def build_all_outputs(
    evaluation_df: pd.DataFrame,
    all_bidder_results: Dict[str, List[Dict]],
) -> Dict[str, pd.DataFrame]:
    """
    Build and return all output DataFrames in one call.
    Applies confidence flagging before building audit DF.
    """
    flagged_results: Dict[str, List[Dict]] = {}
    for bidder, results in all_bidder_results.items():
        flagged_results[bidder] = flag_low_confidence(results)

    scoring_df = build_scoring_dataframe(flagged_results, evaluation_df)
    ranking_df = build_ranking_dataframe(scoring_df)
    audit_df = build_audit_dataframe(flagged_results)

    all_flat = [r for results in flagged_results.values() for r in results]
    low_conf_df = build_low_confidence_report(all_flat)

    return {
        "scoring": scoring_df,
        "ranking": ranking_df,
        "audit": audit_df,
        "low_confidence": low_conf_df,
    }
