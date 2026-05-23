from __future__ import annotations
import argparse, sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0, str(PROJECT_ROOT))
from analysis.plot_utils import apply_ieee_style, resolve, save_vector_figure
p=argparse.ArgumentParser(); p.add_argument('--input', required=True); p.add_argument('--output', default='results/figures/runtime'); p.add_argument('--no-png', action='store_true'); a=p.parse_args()
df=pd.read_csv(resolve(a.input)); metric='mean_runtime_seconds' if 'mean_runtime_seconds' in df.columns else 'runtime_seconds'
g=df.groupby('algorithm', as_index=False)[metric].mean().sort_values(metric)
apply_ieee_style(); plt.figure(figsize=(3.45,2.20)); plt.bar(g['algorithm'], g[metric], edgecolor='black', linewidth=0.4)
plt.ylabel('Runtime (s)'); plt.xlabel('Algorithm'); plt.xticks(rotation=30, ha='right'); plt.grid(axis='y', linewidth=0.3, alpha=0.35)
for x in save_vector_figure(a.output, png=not a.no_png): print(x)
