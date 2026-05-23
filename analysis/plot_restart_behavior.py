from __future__ import annotations
import argparse, sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from analysis.plot_utils import apply_ieee_style, resolve, save_vector_figure
p=argparse.ArgumentParser(); p.add_argument('--input', required=True); p.add_argument('--output', default='results/figures/restart_behavior'); p.add_argument('--no-png', action='store_true'); a=p.parse_args()
df=pd.read_csv(resolve(a.input)); df['restart_count']=pd.to_numeric(df.get('restart_count',0), errors='coerce').fillna(0)
g=df.groupby('algorithm', as_index=False)['restart_count'].mean().sort_values('restart_count', ascending=False)
apply_ieee_style(); plt.figure(figsize=(3.45,2.20)); plt.bar(g['algorithm'], g['restart_count'])
plt.ylabel('Mean Restart Count'); plt.xlabel('Algorithm'); plt.xticks(rotation=30, ha='right')
for x in save_vector_figure(a.output, png=not a.no_png): print(x)
