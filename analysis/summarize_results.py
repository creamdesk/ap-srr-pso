"""Summarize AP-SRR-PSO raw experiment CSV files using the canonical schema.

This module keeps a small backward-compatible ``summarize`` function because
older contract tests and scripts import it directly. The command-line entry
uses the canonical result schema from ``experiments.result_writer``.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.result_writer import SUMMARY_FIELDS, summarize_rows, write_csv


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize raw experiment results")
    p.add_argument("--input", required=True)
    p.add_argument("--output", default="")
    return p.parse_args()


def dataframe_to_rows(df: pd.DataFrame) -> list[dict]:
    rows = df.to_dict(orient="records")
    for row in rows:
        if "function" not in row and "function_id" in row:
            row["function"] = f"F{int(row['function_id'])}"
        if "experiment_name" not in row:
            row["experiment_name"] = "legacy_summary"
        if "status" not in row:
            row["status"] = "ok"
        if "runtime_seconds" not in row:
            row["runtime_seconds"] = ""
    return rows


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Return a summary DataFrame for raw result rows.

    The canonical columns include ``mean_best`` and ``std_best``. Legacy aliases
    ``mean`` and ``std`` are also provided so old tests/scripts do not break.
    """
    summary = pd.DataFrame(summarize_rows(dataframe_to_rows(df)))
    if summary.empty:
        return summary
    if "mean_best" in summary.columns:
        summary["mean"] = summary["mean_best"]
    if "std_best" in summary.columns:
        summary["std"] = summary["std_best"]
    if "median_best" in summary.columns:
        summary["median"] = summary["median_best"]
    return summary


def main() -> None:
    args = parse_args()
    input_path = PROJECT_ROOT / args.input
    df = pd.read_csv(input_path)
    summary_df = summarize(df)
    output_path = PROJECT_ROOT / args.output if args.output else PROJECT_ROOT / "results" / "summary" / f"{input_path.stem}_summary.csv"
    rows = summary_df.to_dict(orient="records")
    write_csv(output_path, rows, SUMMARY_FIELDS)
    print(f"summary saved: {output_path}")
    with output_path.open("r", encoding="utf-8-sig", newline="") as f:
        preview = list(csv.DictReader(f))[:20]
    if preview:
        print(pd.DataFrame(preview).to_string(index=False))


if __name__ == "__main__":
    main()
