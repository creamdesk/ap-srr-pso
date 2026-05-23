from __future__ import annotations

import argparse
import shutil
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
    parser.add_argument("--png", action="store_true", help="同时输出 PNG 预览图。")
    parser.add_argument("--paper-dir", default="paper/figures", help="同步论文用矢量图的目录。")
    return parser.parse_args()


def apply_ieee_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "legend.fontsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.2,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def save_vector_figure(output_path: Path, paper_dir: Path, save_png: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    paper_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_path.with_suffix(".pdf")
    svg_path = output_path.with_suffix(".svg")
    plt.savefig(pdf_path, bbox_inches="tight", pad_inches=0.03)
    plt.savefig(svg_path, bbox_inches="tight", pad_inches=0.03)
    shutil.copy2(pdf_path, paper_dir / pdf_path.name)
    shutil.copy2(svg_path, paper_dir / svg_path.name)
    print(f"PDF saved: {pdf_path}")
    print(f"SVG saved: {svg_path}")
    print(f"Paper figures synced to: {paper_dir}")
    if save_png:
        png_path = output_path.with_suffix(".png")
        plt.savefig(png_path, dpi=300, bbox_inches="tight", pad_inches=0.03)
        print(f"PNG preview saved: {png_path}")


def main() -> None:
    args = parse_args()
    rank_path = PROJECT_ROOT / args.rank_csv
    output_path = PROJECT_ROOT / args.output
    paper_dir = PROJECT_ROOT / args.paper_dir
    df = pd.read_csv(rank_path).sort_values("average_rank", ascending=True)
    apply_ieee_style()
    plt.figure(figsize=(3.45, 2.15))
    plt.bar(df["algorithm"], df["average_rank"], color="#4C78A8", edgecolor="black", linewidth=0.4)
    plt.ylabel("Average Rank")
    plt.xlabel("Algorithm")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    save_vector_figure(output_path, paper_dir=paper_dir, save_png=args.png)


if __name__ == "__main__":
    main()
