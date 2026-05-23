"""CEC2017 30D probe for pipeline and runtime validation.

This is not a formal paper experiment. It uses a small 30D budget only to
check stability, runtime, CSV output, and summary generation.
"""

from __future__ import annotations

import csv
import argparse
import json
import logging
import statistics
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.factory import build_optimizer
from benchmarks.problem_factory import build_problem

BENCHMARK = "CEC2017"
FUNCTION_IDS = [1, 3, 10]
DIMENSION = 30
ALGORITHMS = ["PSO", "PSO-RS", "ARPSO-SRR", "AP-SRR-PSO", "DE"]
RUNS = 2
POPULATION_SIZE = 30
MAX_FES = 10000
RECORD_INTERVAL = 20
BASE_SEED = 20260523

RAW_DIR = PROJECT_ROOT / "results" / "raw"
SUMMARY_DIR = PROJECT_ROOT / "results" / "summary"
LOG_DIR = PROJECT_ROOT / "results" / "logs"
RAW_FILE = RAW_DIR / "cec2017_30d_probe_raw.csv"
SUMMARY_FILE = SUMMARY_DIR / "cec2017_30d_probe_summary.csv"
LOG_FILE = LOG_DIR / "cec2017_30d_probe.log"

RAW_FIELDS = [
    "benchmark",
    "function_id",
    "dimension",
    "algorithm",
    "run",
    "seed",
    "population_size",
    "max_fes",
    "best_fitness",
    "function_evaluations",
    "runtime_seconds",
    "restart_count",
    "operator_usage",
    "operator_success",
    "status",
    "error",
]

SUMMARY_FIELDS = [
    "benchmark",
    "function_id",
    "dimension",
    "algorithm",
    "runs",
    "mean_best",
    "std_best",
    "best",
    "worst",
    "mean_runtime_seconds",
    "total_runtime_seconds",
    "success_count",
    "failure_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CEC2017 30D probe")
    parser.add_argument("--dry-run", action="store_true", help="只打印任务计划，不执行优化、不写结果文件。")
    return parser.parse_args()


def make_seed(function_id: int, algorithm_index: int, run_index: int) -> int:
    return BASE_SEED + function_id * 10000 + algorithm_index * 100 + run_index


def ensure_output_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging() -> None:
    logging.basicConfig(
        filename=LOG_FILE,
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )


def to_json(value: Any) -> str:
    if value in (None, ""):
        return "{}"
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def run_one(function_id: int, algorithm: str, algorithm_index: int, run_index: int) -> dict[str, Any]:
    seed = make_seed(function_id, algorithm_index, run_index)
    start = time.perf_counter()
    base_row: dict[str, Any] = {
        "benchmark": BENCHMARK,
        "function_id": function_id,
        "dimension": DIMENSION,
        "algorithm": algorithm,
        "run": run_index,
        "seed": seed,
        "population_size": POPULATION_SIZE,
        "max_fes": MAX_FES,
        "best_fitness": "",
        "function_evaluations": "",
        "runtime_seconds": "",
        "restart_count": "",
        "operator_usage": "{}",
        "operator_success": "{}",
        "status": "failed",
        "error": "",
    }

    try:
        problem = build_problem(BENCHMARK, function_id=function_id, dimension=DIMENSION)
        optimizer = build_optimizer(algorithm, population_size=POPULATION_SIZE, seed=seed)
        result = optimizer.optimize(
            objective=problem.objective,
            dimension=problem.dimension,
            lower_bound=problem.lower_bound,
            upper_bound=problem.upper_bound,
            max_fes=MAX_FES,
            record_interval=RECORD_INTERVAL,
        )
        runtime = time.perf_counter() - start
        metadata = dict(result.metadata)
        row = {
            **base_row,
            "algorithm": result.algorithm,
            "best_fitness": result.best_fitness,
            "function_evaluations": result.function_evaluations,
            "runtime_seconds": runtime,
            "restart_count": metadata.get("restart_count", 0),
            "operator_usage": to_json(metadata.get("operator_usage", {})),
            "operator_success": to_json(metadata.get("operator_success", {})),
            "status": "ok",
            "error": "",
        }
        message = (
            f"[CEC2017 F{function_id}][{DIMENSION}D][{algorithm}][run {run_index}/{RUNS}] "
            f"best={result.best_fitness:.6e} fes={result.function_evaluations} "
            f"time={runtime:.3f}s status=ok"
        )
        print(message, flush=True)
        logging.info(message)
        return row
    except Exception as exc:  # noqa: BLE001 - keep the probe running.
        runtime = time.perf_counter() - start
        row = {**base_row, "runtime_seconds": runtime, "error": repr(exc)}
        message = (
            f"[CEC2017 F{function_id}][{DIMENSION}D][{algorithm}][run {run_index}/{RUNS}] "
            f"best=nan fes=0 time={runtime:.3f}s status=failed error={exc!r}"
        )
        print(message, flush=True)
        logging.error(message)
        logging.error(traceback.format_exc())
        return row


def write_raw(rows: list[dict[str, Any]]) -> None:
    with RAW_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (str(row["benchmark"]), int(row["function_id"]), int(row["dimension"]), str(row["algorithm"]))
        groups[key].append(row)

    summary_rows: list[dict[str, Any]] = []
    for (benchmark, function_id, dimension, algorithm), group_rows in sorted(groups.items()):
        successes = [row for row in group_rows if row["status"] == "ok"]
        failures = [row for row in group_rows if row["status"] != "ok"]
        best_values = [float(row["best_fitness"]) for row in successes]
        runtime_values = [float(row["runtime_seconds"]) for row in successes]

        summary_rows.append(
            {
                "benchmark": benchmark,
                "function_id": function_id,
                "dimension": dimension,
                "algorithm": algorithm,
                "runs": len(group_rows),
                "mean_best": statistics.fmean(best_values) if best_values else "",
                "std_best": statistics.stdev(best_values) if len(best_values) > 1 else (0.0 if best_values else ""),
                "best": min(best_values) if best_values else "",
                "worst": max(best_values) if best_values else "",
                "mean_runtime_seconds": statistics.fmean(runtime_values) if runtime_values else "",
                "total_runtime_seconds": sum(runtime_values) if runtime_values else "",
                "success_count": len(successes),
                "failure_count": len(failures),
            }
        )
    return summary_rows


def write_summary(rows: list[dict[str, Any]]) -> None:
    with SUMMARY_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    planned = [
        (function_id, algorithm, run_index, make_seed(function_id, algorithm_index, run_index))
        for function_id in FUNCTION_IDS
        for algorithm_index, algorithm in enumerate(ALGORITHMS)
        for run_index in range(1, RUNS + 1)
    ]
    if args.dry_run:
        print("模式: DRY RUN")
        print(f"benchmark={BENCHMARK} dimension={DIMENSION} functions={FUNCTION_IDS}")
        print(f"algorithms={ALGORITHMS} runs={RUNS} max_fes={MAX_FES} population_size={POPULATION_SIZE}")
        print(f"任务数: {len(planned)}")
        for function_id, algorithm, run_index, seed in planned[:10]:
            print(f"task F{function_id} algorithm={algorithm} run={run_index} seed={seed}")
        if len(planned) > 10:
            print(f"... 其余 {len(planned) - 10} 个任务省略")
        print("dry-run 完成：未执行优化，未写结果文件。")
        return

    ensure_output_dirs()
    configure_logging()
    overall_start = time.perf_counter()
    logging.info(
        "Starting 30D probe: functions=%s algorithms=%s runs=%s dimension=%s max_fes=%s population_size=%s",
        FUNCTION_IDS,
        ALGORITHMS,
        RUNS,
        DIMENSION,
        MAX_FES,
        POPULATION_SIZE,
    )

    rows: list[dict[str, Any]] = []
    for function_id in FUNCTION_IDS:
        for algorithm_index, algorithm in enumerate(ALGORITHMS):
            for run_index in range(1, RUNS + 1):
                rows.append(run_one(function_id, algorithm, algorithm_index, run_index))

    write_raw(rows)
    summary_rows = summarize(rows)
    write_summary(summary_rows)

    elapsed = time.perf_counter() - overall_start
    success_count = sum(1 for row in rows if row["status"] == "ok")
    failure_count = len(rows) - success_count
    logging.info("30D probe finished: success=%s failure=%s elapsed=%.3fs", success_count, failure_count, elapsed)
    logging.info("Raw file: %s", RAW_FILE)
    logging.info("Summary file: %s", SUMMARY_FILE)
    print(f"30D probe finished: success={success_count} failure={failure_count} elapsed={elapsed:.3f}s", flush=True)
    print(f"raw: {RAW_FILE}", flush=True)
    print(f"summary: {SUMMARY_FILE}", flush=True)
    print(f"log: {LOG_FILE}", flush=True)


if __name__ == "__main__":
    main()
