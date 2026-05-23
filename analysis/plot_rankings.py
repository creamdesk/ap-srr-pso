"""Plot average ranking as PDF/SVG vector figures."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0, str(PROJECT_ROOT))
from analysis.plot_utils import apply_ieee_style, resolve, save_vector_figure

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--input", required=True); p.add_argument("--output", default="results/figures/average_rank"); p.add_argument("--no-png", action="store_true"); a=p.parse_args()
    df=pd.read_csv(resolve(a.input)).sort_values("average_rank", ascending=True)
    apply_ieee_style(); plt.figure(figsize=(3.45,2.20)); plt.bar(df["algorithm"], df["average_rank"], edgecolor="black", linewidth=0.4)
    plt.ylabel("Average Rank"); plt.xlabel("Algorithm"); plt.xticks(rotation=30, ha="right"); plt.grid(axis="y", linewidth=0.3, alpha=0.35)
    for x in save_vector_figure(a.output, png=not a.no_png): print(x)
if __name__ == "__main__": main()
