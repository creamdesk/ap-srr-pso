from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

def run(cmd):
    print('$ ' + ' '.join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--experiment', default='cec2017_30d_probe')
    p.add_argument('--no-png', action='store_true')
    a = p.parse_args()
    extra = ['--no-png'] if a.no_png else []
    raw = ROOT/'results'/'raw'/f'{a.experiment}_raw.csv'
    summary = ROOT/'results'/'summary'/f'{a.experiment}_summary.csv'
    curves = ROOT/'results'/'curves'/f'{a.experiment}_curves.jsonl'
    rank = ROOT/'results'/'stats'/f'{a.experiment}_raw_average_rank.csv'
    if curves.exists(): run([PY,'analysis/plot_convergence.py','--input',str(curves.relative_to(ROOT)),'--output',f'results/figures/{a.experiment}_convergence',*extra])
    else: print('skip convergence')
    if rank.exists(): run([PY,'analysis/plot_rankings.py','--input',str(rank.relative_to(ROOT)),'--output',f'results/figures/{a.experiment}_ranking',*extra])
    else: print('skip ranking')
    if summary.exists():
        run([PY,'analysis/plot_runtime.py','--input',str(summary.relative_to(ROOT)),'--output',f'results/figures/{a.experiment}_runtime',*extra])
        run([PY,'analysis/plot_ablation.py','--input',str(summary.relative_to(ROOT)),'--output',f'results/figures/{a.experiment}_ablation',*extra])
    else: print('skip summary figures')
    if raw.exists(): run([PY,'analysis/plot_restart_behavior.py','--input',str(raw.relative_to(ROOT)),'--output',f'results/figures/{a.experiment}_restart',*extra])
    else: print('skip restart')

if __name__ == '__main__':
    main()
