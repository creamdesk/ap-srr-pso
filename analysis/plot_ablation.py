from __future__ import annotations
import argparse, sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from analysis.plot_utils import apply_ieee_style, resolve, save_vector_figure

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--metric', default='mean_best')
    ap.add_argument('--output', default='results/figures/ablation')
    ap.add_argument('--no-png', action='store_true')
    a = ap.parse_args()
    df = pd.read_csv(resolve(a.input))
    if a.metric not in df.columns:
        raise ValueError('metric not found: ' + a.metric)
    g = df.groupby('algorithm', as_index=False)[a.metric].mean().sort_values(a.metric)
    apply_ieee_style()
    plt.figure(figsize=(3.45, 2.25))
    plt.bar(g['algorithm'], g[a.metric])
    plt.ylabel(a.metric)
    plt.xlabel('Algorithm')
    plt.xticks(rotation=30, ha='right')
    for p in save_vector_figure(a.output, png=not a.no_png):
        print(p)

if __name__ == '__main__':
    main()
