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
    required = {"benchmark", "function", "algorithm", "dimension", "best_fitness"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"缺少字段: {sorted(missing)}")
    summary = (
        df.groupby(["benchmark", "function", "algorithm", "dimension"], as_index=False)["best_fitness"]
        .agg(mean="mean", std="std", median="median", best="min", worst="max")
        .sort_values(["benchmark", "function", "dimension", "mean"])
    )
    summary["rank"] = summary.groupby(["benchmark", "function", "dimension"])["mean"].rank(method="average", ascending=True)
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
