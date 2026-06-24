from pathlib import Path
from typing import Dict
import pandas as pd
from datetime import datetime


def export_all_to_excel(
    outputs_dir: str,
    eligibility_df: pd.DataFrame,
    evaluation_df: pd.DataFrame,
    eligibility_summary_df: pd.DataFrame,
    scoring_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    audit_df: pd.DataFrame,
    low_conf_df: pd.DataFrame,
) -> str:
    """
    Write evaluation-only results into a single timestamped Excel workbook.
    Eligibility sheets are excluded — report covers scoring and rankings only.
    Returns the file path.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = Path(outputs_dir) / f"evaluation_report_{timestamp}.xlsx"

    with pd.ExcelWriter(str(file_path), engine="xlsxwriter") as writer:
        wb = writer.book

        header_fmt = wb.add_format({"bold": True, "bg_color": "#1F4E79", "font_color": "white",
                                     "border": 1, "align": "center", "valign": "vcenter", "text_wrap": True})
        low_conf_fmt = wb.add_format({"bg_color": "#FFEB9C", "font_color": "#9C5700", "border": 1})
        num_fmt = wb.add_format({"num_format": "0.00", "border": 1, "align": "center"})
        cell_fmt = wb.add_format({"border": 1, "text_wrap": True, "valign": "top"})

        _write_sheet(writer, evaluation_df, "Evaluation Criteria", header_fmt, cell_fmt)
        _write_sheet(writer, scoring_df, "Scoring Matrix", header_fmt, num_fmt)
        _write_sheet(writer, ranking_df, "Rankings", header_fmt, cell_fmt)
        _write_sheet(writer, audit_df, "Audit Trail", header_fmt, cell_fmt,
                     flag_col="Low Confidence Flag", low_conf_fmt=low_conf_fmt)
        _write_sheet(writer, low_conf_df, "Low Confidence Flags", header_fmt, low_conf_fmt)

    return str(file_path)


def _write_sheet(writer, df: pd.DataFrame, sheet_name: str, header_fmt, cell_fmt,
                 conditional_cols=None, pass_fmt=None, fail_fmt=None,
                 flag_col: str = None, low_conf_fmt=None):
    if df.empty:
        df = pd.DataFrame({"No Data": ["No records found"]})

    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
    ws = writer.sheets[sheet_name]

    # Write headers
    for col_num, value in enumerate(df.columns):
        ws.write(0, col_num, value, header_fmt)

    # Auto column width
    for col_num, col_name in enumerate(df.columns):
        max_len = max(len(str(col_name)), df[col_name].astype(str).str.len().max() if not df.empty else 0)
        ws.set_column(col_num, col_num, min(max_len + 4, 50))

    # Conditional formatting for status columns
    if conditional_cols and pass_fmt and fail_fmt:
        for col_name in conditional_cols:
            if col_name in df.columns:
                col_idx = df.columns.get_loc(col_name)
                for row_num, val in enumerate(df[col_name], start=1):
                    fmt = pass_fmt if str(val).upper() in {"ELIGIBLE", "PASS"} else fail_fmt
                    ws.write(row_num, col_idx, val, fmt)

    # Flag low-confidence rows
    if flag_col and low_conf_fmt and flag_col in df.columns:
        for row_num, val in enumerate(df[flag_col], start=1):
            if val is True or str(val).lower() == "true":
                for col_idx in range(len(df.columns)):
                    ws.write(row_num, col_idx, df.iloc[row_num - 1, col_idx], low_conf_fmt)


def export_criteria_to_excel(outputs_dir: str, eligibility_df: pd.DataFrame, evaluation_df: pd.DataFrame) -> str:
    """Export just the criteria sheets (used after Phase 1 approval)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = Path(outputs_dir) / f"criteria_{timestamp}.xlsx"
    with pd.ExcelWriter(str(file_path), engine="openpyxl") as writer:
        eligibility_df.to_excel(writer, sheet_name="Eligibility Criteria", index=False)
        evaluation_df.to_excel(writer, sheet_name="Evaluation Criteria", index=False)
    return str(file_path)
