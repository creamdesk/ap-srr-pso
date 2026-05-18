from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot average rank figure")
    parser.add_argument("--rank-csv", required=True)
    parser.add_argument("--output", default="results/figures/average_rank.pdf")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rank_path = PROJECT_ROOT / args.rank_csv
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(rank_path).sort_values("average_rank", ascending=True)
    plt.figure(figsize=(7.0, 4.0))
    plt.bar(df["algorithm"], df["average_rank"])
    plt.ylabel("Average Rank")
    plt.xlabel("Algorithm")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    svg_path = output_path.with_suffix(".svg")
    plt.savefig(svg_path, bbox_inches="tight")
    print(f"Figure saved: {output_path}")
    print(f"SVG saved: {svg_path}")


if __name__ == "__main__":
    main()
