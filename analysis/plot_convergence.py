from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from analysis.plot_utils import apply_ieee_style, resolve, save_vector_figure

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--function', default='')
    ap.add_argument('--output', default='results/figures/convergence')
    ap.add_argument('--no-png', action='store_true')
    a = ap.parse_args()
    target = a.function.upper()
    if target and not target.startswith('F'):
        target = 'F' + target
    rows = []
    with resolve(a.input).open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    if target:
        rows = [r for r in rows if str(r.get('function','')).upper() == target or ('F' + str(r.get('function_id'))) == target]
    if not rows:
        raise ValueError('no convergence curves matched')
    data = defaultdict(list)
    for r in rows:
        curve = [float(x) for x in r.get('convergence_curve', [])]
        if curve:
            data[str(r.get('algorithm'))].append(curve)
    apply_ieee_style()
    plt.figure(figsize=(3.45, 2.35))
    for alg, curves in sorted(data.items()):
        m = min(len(c) for c in curves)
        y = np.mean(np.array([c[:m] for c in curves]), axis=0)
        plt.plot(np.arange(m), y, label=alg)
    plt.yscale('log')
    plt.xlabel('Recorded Iteration')
    plt.ylabel('Best Fitness')
    plt.legend(frameon=False)
    plt.grid(linewidth=0.3, alpha=0.35)
    suffix = '_' + target.lower() if target else ''
    for p in save_vector_figure(a.output + suffix, png=not a.no_png):
        print(p)

if __name__ == '__main__':
    main()
