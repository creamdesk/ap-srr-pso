# -*- coding: utf-8 -*-
"""
Fix Fig. 2 for the ARPSO-SRR paper.

Purpose:
1. Ensure Fig. 2 uses the same average-rank values as Table III.
2. Regenerate:
   arpso_curated_workspace/paper/figures/ablation6_average_rank.pdf
3. Keep main.tex unchanged.

Run from project root:
python code/fix_fig2_ablation_rank.py
"""

from pathlib import Path
import shutil
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# 1. Paths
# ============================================================

ROOT = Path.cwd()

CSV_PATH = (
    ROOT
    / "arpso_curated_workspace"
    / "analysis_data"
    / "ablation6"
    / "ablation6_average_rank.csv"
)

FIG_DIR = ROOT / "arpso_curated_workspace" / "paper" / "figures"
OUT_PDF = FIG_DIR / "ablation6_average_rank.pdf"
OUT_PNG = FIG_DIR / "ablation6_average_rank.png"

FIG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. Correct Table III values
# ============================================================

# Source of truth: current Table III in main.pdf / main.tex
TABLE_III_RANKS = {
    "ARPSO-Local": 2.71,
    "ARPSO-SRR": 2.71,
    "ARPSO-EIS": 3.46,
    "ARPSO-Fixed": 3.46,
    "ARPSO-Global": 4.25,
    "PSO-RS": 4.39,
}

ORDER = [
    "ARPSO-Local",
    "ARPSO-SRR",
    "ARPSO-EIS",
    "ARPSO-Fixed",
    "ARPSO-Global",
    "PSO-RS",
]


# ============================================================
# 3. Back up and rewrite CSV
# ============================================================

df_fixed = pd.DataFrame(
    {
        "Variant": ORDER,
        "AverageRank": [TABLE_III_RANKS[v] for v in ORDER],
    }
)

if CSV_PATH.exists():
    backup_path = CSV_PATH.with_suffix(".backup_before_fig2_fix.csv")
    shutil.copy2(CSV_PATH, backup_path)
    print(f"[Backup] Old CSV saved to: {backup_path}")
else:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("[Warning] Original CSV not found. A new corrected CSV will be created.")

df_fixed.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
print(f"[OK] Corrected CSV written to: {CSV_PATH}")


# ============================================================
# 4. Publication-style vector figure
# ============================================================

plt.rcParams.update(
    {
        "font.family": "Times New Roman",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.linewidth": 0.8,
    }
)

variants = df_fixed["Variant"].tolist()
ranks = df_fixed["AverageRank"].to_numpy()

# Reverse order for horizontal bar plot: best appears at top
variants_plot = variants[::-1]
ranks_plot = ranks[::-1]

fig, ax = plt.subplots(figsize=(3.45, 2.35))

bars = ax.barh(
    variants_plot,
    ranks_plot,
    height=0.58,
    edgecolor="black",
    linewidth=0.7,
)

# Highlight the two best variants
for bar, name in zip(bars, variants_plot):
    if name in ["ARPSO-Local", "ARPSO-SRR"]:
        bar.set_hatch("///")
        bar.set_linewidth(0.9)

# Value labels
for y, value in enumerate(ranks_plot):
    ax.text(
        value + 0.035,
        y,
        f"{value:.2f}",
        va="center",
        ha="left",
        fontsize=8,
    )

ax.set_xlabel("Average rank (lower is better)")
ax.set_xlim(0, max(ranks_plot) + 0.55)

# Subtle guide lines
ax.grid(axis="x", linestyle="--", linewidth=0.45, alpha=0.45)
ax.set_axisbelow(True)

# Remove unnecessary borders
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Add note for tied best result
ax.text(
    0.02,
    1.04,
    "ARPSO-Local and ARPSO-SRR obtain the best average rank.",
    transform=ax.transAxes,
    ha="left",
    va="bottom",
    fontsize=8,
)

plt.tight_layout(pad=0.5)

fig.savefig(OUT_PDF, bbox_inches="tight")
fig.savefig(OUT_PNG, dpi=600, bbox_inches="tight")

plt.close(fig)

print(f"[OK] Fig. 2 PDF regenerated: {OUT_PDF}")
print(f"[OK] Fig. 2 PNG regenerated: {OUT_PNG}")

print("\nDone. Now recompile main.tex.")
