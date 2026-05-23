"""Summarize AP-SRR-PSO raw experiment CSV files using the canonical schema."""
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
    return rows


def main() -> None:
    args = parse_args()
    input_path = PROJECT_ROOT / args.input
    df = pd.read_csv(input_path)
    rows = dataframe_to_rows(df)
    summary = summarize_rows(rows)
    output_path = PROJECT_ROOT / args.output if args.output else PROJECT_ROOT / "results" / "summary" / f"{input_path.stem}_summary.csv"
    write_csv(output_path, summary, SUMMARY_FIELDS)
    print(f"summary saved: {output_path}")
    with output_path.open("r", encoding="utf-8-sig", newline="") as f:
        preview = list(csv.DictReader(f))[:20]
    if preview:
        print(pd.DataFrame(preview).to_string(index=False))


if __name__ == "__main__":
    main()
