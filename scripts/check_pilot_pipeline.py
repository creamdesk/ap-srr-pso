"""Manual reproducibility check for the ablation6 pilot pipeline.

This script is intentionally not part of the default CI workflow because it runs
real CEC2017 pilot optimization tasks. It moves existing ablation6 pilot
artifacts into results/tmp/, regenerates raw/summary/table/figure outputs, and
checks that the paper-facing artifacts are non-empty.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = "ablation6_pilot"


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def pilot_paths() -> list[Path]:
    paths: list[Path] = []
    for pattern in [
        f"results/raw/{EXPERIMENT}_*.csv",
        f"results/summary/{EXPERIMENT}_summary.csv",
        f"results/stats/{EXPERIMENT}_raw*.csv",
        f"results/tables/{EXPERIMENT}_*.tex",
        f"results/figures/{EXPERIMENT}_*",
        f"results/curves/{EXPERIMENT}_curves.jsonl",
        f"paper/tables/{EXPERIMENT}_*.tex",
        f"paper/figures/{EXPERIMENT}_*",
    ]:
        paths.extend(ROOT.glob(pattern))
    return sorted({path for path in paths if path.is_file()})


def move_existing_artifacts() -> Path | None:
    existing = pilot_paths()
    if not existing:
        print("No existing pilot artifacts found.")
        return None

    backup_root = ROOT / "results" / "tmp" / "pilot_pipeline_backup" / time.strftime("%Y%m%d-%H%M%S")
    for path in existing:
        relative = path.relative_to(ROOT)
        target = backup_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
    print(f"Moved {len(existing)} existing pilot artifact(s) to {backup_root}")
    return backup_root


def require_nonempty(paths: list[Path]) -> None:
    missing: list[str] = []
    for path in paths:
        if not path.exists() or path.stat().st_size <= 0:
            missing.append(str(path.relative_to(ROOT)))
    if missing:
        raise RuntimeError("Missing or empty generated artifact(s): " + ", ".join(missing))


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate ablation6 pilot outputs from an empty pilot artifact set.")
    parser.add_argument("--keep-existing", action="store_true", help="Do not move existing pilot artifacts before running.")
    args = parser.parse_args()

    if not args.keep_existing:
        move_existing_artifacts()

    py = sys.executable
    run([py, "-m", "experiments.run_ablation6", "--config", "configs/ablation6_pilot.yaml"])
    run([py, "-m", "analysis.generate_tables", "--experiment", EXPERIMENT])
    run([py, "-m", "analysis.generate_figures", "--experiment", EXPERIMENT, "--no-png"])

    require_nonempty(
        [
            ROOT / "results" / "raw" / f"{EXPERIMENT}_raw.csv",
            ROOT / "results" / "raw" / f"{EXPERIMENT}_convergence.csv",
            ROOT / "results" / "summary" / f"{EXPERIMENT}_summary.csv",
            ROOT / "results" / "tables" / f"{EXPERIMENT}_summary.tex",
            ROOT / "results" / "figures" / f"{EXPERIMENT}_ranking.tex",
            ROOT / "results" / "figures" / f"{EXPERIMENT}_convergence.pdf",
            ROOT / "results" / "figures" / f"{EXPERIMENT}_restart.pdf",
            ROOT / "paper" / "tables" / f"{EXPERIMENT}_summary.tex",
            ROOT / "paper" / "figures" / f"{EXPERIMENT}_ranking.tex",
        ]
    )
    print("pilot pipeline reproducibility check passed")


if __name__ == "__main__":
    main()
