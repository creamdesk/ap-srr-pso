from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]

def esc(x):
    return str(x).replace('_', r'\_').replace('%', r'\%')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', default='')
    ap.add_argument('--columns', default='')
    ap.add_argument('--caption', default='Experimental results.')
    ap.add_argument('--label', default='tab:results')
    a = ap.parse_args()
    inp = ROOT / a.input
    df = pd.read_csv(inp)
    cols = [c.strip() for c in a.columns.split(',') if c.strip()] or list(df.columns[:8])
    df = df[cols]
    out = ROOT / a.output if a.output else ROOT / 'paper' / 'tables' / (inp.stem + '.tex')
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append(r'\begin{table}[t]')
    lines.append(r'\centering')
    lines.append(r'\caption{' + esc(a.caption) + '}')
    lines.append(r'\label{' + esc(a.label) + '}')
    lines.append(r'\scriptsize')
    lines.append(r'\begin{tabular}{' + 'l' * len(cols) + '}')
    lines.append(r'\hline')
    lines.append(' & '.join(esc(c) for c in cols) + r' \\')
    lines.append(r'\hline')
    for _, row in df.iterrows():
        lines.append(' & '.join(esc(row[c]) for c in cols) + r' \\')
    lines.append(r'\hline')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table}')
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(out)

if __name__ == '__main__':
    main()
