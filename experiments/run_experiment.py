"""Backward-compatible experiment CLI wrapper.

This file used to contain a separate experiment runner. It now delegates to
``experiments.experiment_runner`` so the repository has one canonical pipeline
for raw CSV, summary CSV, logs, curves, resume, and dry-run behavior.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.experiment_runner import run_experiment


@dataclass(frozen=True)
class LegacyTask:
    benchmark: str
    function_id: int
    dimension: int
    algorithm: str
    run: int
    seed: int
    population_size: int
    max_fes: int
    record_interval: int


def build_tasks(args: argparse.Namespace) -> list[LegacyTask]:
    """Build deterministic legacy task objects for old contract tests/scripts."""
    tasks: list[LegacyTask] = []
    for function_id in args.functions:
        for algorithm_index, algorithm in enumerate(args.algorithms):
            for run in range(1, args.runs + 1):
                seed = int(args.base_seed) + int(function_id) * 100000 + int(algorithm_index) * 1000 + int(run)
                tasks.append(
                    LegacyTask(
                        benchmark=args.benchmark,
                        function_id=int(function_id),
                        dimension=int(args.dimension),
                        algorithm=str(algorithm),
                        run=int(run),
                        seed=seed,
                        population_size=int(args.population_size),
                        max_fes=int(args.max_fes),
                        record_interval=int(args.record_interval),
                    )
                )
    return tasks


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backward-compatible AP-SRR-PSO experiment wrapper")
    p.add_argument("--benchmark", required=True)
    p.add_argument("--dimension", type=int, required=True)
    p.add_argument("--functions", nargs="+", type=int, required=True)
    p.add_argument("--algorithms", nargs="+", required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--max-fes", type=int, default=10000)
    p.add_argument("--population-size", type=int, default=50)
    p.add_argument("--base-seed", type=int, default=2026)
    p.add_argument("--record-interval", type=int, default=10)
    p.add_argument("--output", default="results/raw/experiment_results.csv", help="Used only to derive experiment_name for the new runner.")
    p.add_argument("--n-jobs", type=int, default=1)
    p.add_argument("--save-curves", action="store_true", help="Kept for compatibility. Curves are saved by the canonical runner.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--resume", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    output_stem = Path(args.output).stem
    if output_stem.endswith("_raw"):
        output_stem = output_stem[:-4]
    cfg = {
        "experiment_name": output_stem or "experiment_results",
        "benchmark": args.benchmark,
        "dimension": args.dimension,
        "functions": args.functions,
        "algorithms": args.algorithms,
        "runs": args.runs,
        "max_fes": args.max_fes,
        "population_size": args.population_size,
        "base_seed": args.base_seed,
        "record_interval": args.record_interval,
        "n_jobs": args.n_jobs,
    }
    run_experiment(cfg, dry_run=args.dry_run, resume=args.resume)


if __name__ == "__main__":
    main()
