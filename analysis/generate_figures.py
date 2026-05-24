"""Generate vector and PGFPlots-compatible figures from experiment outputs."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def copy_to_paper(path: Path) -> None:
    paper = ROOT / "paper" / "figures"
    paper.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, paper / path.name)


def tikz_header() -> list[str]:
    return [
        r"\begin{tikzpicture}",
        r"\begin{axis}[",
        r"width=0.95\columnwidth,",
        r"height=0.58\columnwidth,",
        r"grid=major,",
        r"tick label style={font=\scriptsize},",
        r"label style={font=\scriptsize},",
        r"legend style={font=\scriptsize,draw=none},",
    ]


def write_rank_tikz(rank_csv: Path, output: Path) -> None:
    df = pd.read_csv(rank_csv).sort_values("average_rank")
    lines = tikz_header()
    lines += [
        r"ybar,",
        r"ylabel={Average Rank},",
        r"symbolic x coords={" + ",".join(map(str, df["algorithm"])) + r"},",
        r"xtick=data,",
        r"x tick label style={rotate=35,anchor=east},",
        r"]",
        r"\addplot coordinates {",
    ]
    for _, row in df.iterrows():
        lines.append(f"({row['algorithm']},{float(row['average_rank']):.6g})")
    lines += [r"};", r"\end{axis}", r"\end{tikzpicture}"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    copy_to_paper(output)


def write_restart_tikz(raw_csv: Path, output: Path) -> None:
    df = pd.read_csv(raw_csv)
    if "restart_count" not in df.columns:
        print("skip restart tikz: missing restart_count")
        return
    df["restart_count"] = pd.to_numeric(df["restart_count"], errors="coerce").fillna(0)
    grouped = df.groupby("algorithm", as_index=False)["restart_count"].mean().sort_values("restart_count", ascending=False)
    lines = tikz_header()
    lines += [
        r"ybar,",
        r"ylabel={Mean Restart Count},",
        r"symbolic x coords={" + ",".join(map(str, grouped["algorithm"])) + r"},",
        r"xtick=data,",
        r"x tick label style={rotate=35,anchor=east},",
        r"]",
        r"\addplot coordinates {",
    ]
    for _, row in grouped.iterrows():
        lines.append(f"({row['algorithm']},{float(row['restart_count']):.6g})")
    lines += [r"};", r"\end{axis}", r"\end{tikzpicture}"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    copy_to_paper(output)


def write_convergence_tikz(convergence_csv: Path, output: Path) -> None:
    df = pd.read_csv(convergence_csv)
    required = {"algorithm", "function_id", "run_id", "fe", "best_so_far"}
    if not required.issubset(df.columns):
        print(f"skip convergence tikz: missing {sorted(required - set(df.columns))}")
        return
    first_fid = sorted(df["function_id"].unique())[0]
    df = df[df["function_id"] == first_fid].copy()
    df["fe"] = pd.to_numeric(df["fe"], errors="coerce")
    df["best_so_far"] = pd.to_numeric(df["best_so_far"], errors="coerce")
    grouped = df.groupby(["algorithm", "fe"], as_index=False)["best_so_far"].mean()
    lines = tikz_header()
    lines += [
        r"ymode=log,",
        r"xlabel={Function Evaluations},",
        r"ylabel={Best-so-far},",
        r"]",
    ]
    for alg, sub in grouped.groupby("algorithm"):
        points = " ".join(f"({int(row.fe)},{float(row.best_so_far):.6g})" for row in sub.itertuples(index=False))
        lines.append(r"\addplot coordinates {" + points + r"};")
        lines.append(r"\addlegendentry{" + str(alg).replace("_", r"\_") + r"}")
    lines += [r"\end{axis}", r"\end{tikzpicture}"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    copy_to_paper(output)


def ensure_rank_stats(experiment: str, target: str) -> None:
    rank = ROOT / "results" / "stats" / f"{experiment}_raw_average_rank.csv"
    raw = ROOT / "results" / "raw" / f"{experiment}_raw.csv"
    if rank.exists() or not raw.exists():
        return
    run([PY, "analysis/statistical_tests.py", "--input", str(raw.relative_to(ROOT)), "--target", target])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paper figures from experiment outputs.")
    parser.add_argument("--experiment", default="cec2017_30d_probe")
    parser.add_argument("--target", default="ARPSO-SRR")
    parser.add_argument("--no-png", action="store_true")
    args = parser.parse_args()

    ensure_rank_stats(args.experiment, args.target)

    raw = ROOT / "results" / "raw" / f"{args.experiment}_raw.csv"
    summary = ROOT / "results" / "summary" / f"{args.experiment}_summary.csv"
    curves_jsonl = ROOT / "results" / "curves" / f"{args.experiment}_curves.jsonl"
    convergence_csv = ROOT / "results" / "raw" / f"{args.experiment}_convergence.csv"
    rank = ROOT / "results" / "stats" / f"{args.experiment}_raw_average_rank.csv"
    extra = ["--no-png"] if args.no_png else []

    if curves_jsonl.exists():
        run([PY, "analysis/plot_convergence.py", "--input", str(curves_jsonl.relative_to(ROOT)), "--output", f"results/figures/{args.experiment}_convergence", *extra])
    else:
        print(f"skip convergence pdf/svg: missing {curves_jsonl}")
    if rank.exists():
        run([PY, "analysis/plot_rankings.py", "--input", str(rank.relative_to(ROOT)), "--output", f"results/figures/{args.experiment}_ranking", *extra])
        write_rank_tikz(rank, ROOT / "results" / "figures" / f"{args.experiment}_ranking.tex")
    else:
        print(f"skip ranking: missing {rank}")
    if summary.exists():
        run([PY, "analysis/plot_runtime.py", "--input", str(summary.relative_to(ROOT)), "--output", f"results/figures/{args.experiment}_runtime", *extra])
        run([PY, "analysis/plot_ablation.py", "--input", str(summary.relative_to(ROOT)), "--output", f"results/figures/{args.experiment}_ablation", *extra])
    else:
        print(f"skip summary figures: missing {summary}")
    if raw.exists():
        run([PY, "analysis/plot_restart_behavior.py", "--input", str(raw.relative_to(ROOT)), "--output", f"results/figures/{args.experiment}_restart", *extra])
        write_restart_tikz(raw, ROOT / "results" / "figures" / f"{args.experiment}_restart.tex")
    else:
        print(f"skip restart: missing {raw}")
    if convergence_csv.exists():
        write_convergence_tikz(convergence_csv, ROOT / "results" / "figures" / f"{args.experiment}_convergence.tex")
    else:
        print(f"skip convergence tikz: missing {convergence_csv}")


if __name__ == "__main__":
    main()
