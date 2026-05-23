"""汇总实验结果。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="汇总实验结果")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="")
    return parser.parse_args()


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "function" not in df.columns and "function_id" in df.columns:
        df["function"] = df["function_id"].apply(lambda x: f"F{int(x)}")
    required = {"benchmark", "function", "algorithm", "dimension", "best_fitness"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"缺少字段: {sorted(missing)}")
    if "status" in df.columns:
        ok_df = df[df["status"] == "ok"].copy()
    else:
        ok_df = df.copy()
    ok_df["best_fitness"] = pd.to_numeric(ok_df["best_fitness"], errors="coerce")
    ok_df = ok_df.dropna(subset=["best_fitness"])
    group_cols = ["benchmark", "function", "algorithm", "dimension"]
    summary = (
        ok_df.groupby(group_cols, as_index=False)
        .agg(
            runs=("best_fitness", "count"),
            mean=("best_fitness", "mean"),
            std=("best_fitness", "std"),
            median=("best_fitness", "median"),
            best=("best_fitness", "min"),
            worst=("best_fitness", "max"),
            mean_runtime_seconds=("runtime_seconds", "mean") if "runtime_seconds" in ok_df.columns else ("best_fitness", "size"),
        )
        .sort_values(["benchmark", "function", "dimension", "mean"])
    )
    summary["rank"] = summary.groupby(["benchmark", "function", "dimension"])["mean"].rank(method="average", ascending=True)
    if "status" in df.columns:
        status_counts = df.groupby(group_cols + ["status"]).size().unstack(fill_value=0).reset_index()
        summary = summary.merge(status_counts, on=group_cols, how="left")
        summary["success_count"] = summary.get("ok", 0)
        summary["failure_count"] = summary.drop(columns=group_cols, errors="ignore").get("failed", 0)
    return summary


def main() -> None:
    args = parse_args()
    input_path = PROJECT_ROOT / args.input
    df = pd.read_csv(input_path)
    summary = summarize(df)
    output_path = PROJECT_ROOT / args.output if args.output else PROJECT_ROOT / "results" / "summary" / f"{input_path.stem}_summary.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"汇总完成: {output_path}")
    print(summary.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
