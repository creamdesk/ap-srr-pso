"""Shared helpers for paper-quality vector figures."""
from __future__ import annotations

import shutil
from pathlib import Path
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def apply_ieee_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8,
        "legend.fontsize": 7,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.1,
        "lines.markersize": 3.0,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
    })


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def save_vector_figure(output_base: str | Path, *, paper_dir: str | Path = "paper/figures", png: bool = True) -> list[Path]:
    base = resolve(output_base)
    if base.suffix:
        base = base.with_suffix("")
    base.parent.mkdir(parents=True, exist_ok=True)
    paper_path = resolve(paper_dir)
    paper_path.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for suffix in [".pdf", ".svg"]:
        path = base.with_suffix(suffix)
        plt.savefig(path, bbox_inches="tight", pad_inches=0.03)
        shutil.copy2(path, paper_path / path.name)
        saved.append(path)
    if png:
        path = base.with_suffix(".png")
        plt.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.03)
        saved.append(path)
    return saved
