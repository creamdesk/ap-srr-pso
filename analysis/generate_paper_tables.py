from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def latex_table(input_path: Path, output_path: Path, caption: str, label: str) -> None:
    run(
        [
            PY,
            "analysis/generate_latex_tables.py",
            "--input",
            str(input_path.relative_to(ROOT)),
            "--output",
            str(output_path.relative_to(ROOT)),
            "--caption",
            caption,
            "--label",
            label,
        ]
    )


def generate_stats_if_possible(experiment: str, target: str) -> None:
    raw = ROOT / "results" / "raw" / f"{experiment}_raw.csv"
    if not raw.exists():
        print(f"skip statistics: missing {raw}")
        return
    run([PY, "analysis/statistical_tests.py", "--input", str(raw.relative_to(ROOT)), "--target", target])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LaTeX paper tables from experiment outputs.")
    parser.add_argument("--experiment", default="cec2017_30d_probe")
    parser.add_argument("--target", default="ARPSO-SRR")
    args = parser.parse_args()

    results_tables = ROOT / "results" / "tables"
    paper_tables = ROOT / "paper" / "tables"
    results_tables.mkdir(parents=True, exist_ok=True)
    paper_tables.mkdir(parents=True, exist_ok=True)

    generate_stats_if_possible(args.experiment, args.target)

    summary = ROOT / "results" / "summary" / f"{args.experiment}_summary.csv"
    if summary.exists():
        for base in [results_tables, paper_tables]:
            latex_table(summary, base / f"{args.experiment}_summary.tex", "Summary results", f"tab:{args.experiment}-summary")
    else:
        print(f"skip summary table: missing {summary}")

    stats_dir = ROOT / "results" / "stats"
    for stats_csv in sorted(stats_dir.glob(f"{args.experiment}_raw*.csv")):
        caption = stats_csv.stem.replace("_", " ")
        label = "tab:" + stats_csv.stem.replace("_", "-")
        for base in [results_tables, paper_tables]:
            latex_table(stats_csv, base / f"{stats_csv.stem}.tex", caption, label)


if __name__ == "__main__":
    main()
