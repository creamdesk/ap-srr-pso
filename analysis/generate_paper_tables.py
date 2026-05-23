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
    a = p.parse_args()
    summary = ROOT/'results'/'summary'/f'{a.experiment}_summary.csv'
    stats = ROOT/'results'/'stats'
    if summary.exists():
        run([PY,'analysis/generate_latex_tables.py','--input',str(summary.relative_to(ROOT)),'--output',f'paper/tables/{a.experiment}_summary.tex','--caption','Summary results','--label',f'tab:{a.experiment}_summary'])
    else: print('skip summary table')
    for name, cap in [('average_rank','Average ranking'),('friedman','Friedman ranking'),('win_tie_loss','Win tie loss'),('holm_posthoc','Holm post-hoc')]:
        files = list(stats.glob(f'{a.experiment}_raw*{name}.csv'))
        for f in files:
            out = ROOT/'paper'/'tables'/(f.stem + '.tex')
            run([PY,'analysis/generate_latex_tables.py','--input',str(f.relative_to(ROOT)),'--output',str(out.relative_to(ROOT)),'--caption',cap,'--label','tab:'+f.stem.replace('_','-')])

if __name__ == '__main__':
    main()
