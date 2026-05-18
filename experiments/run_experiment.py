"""统一实验入口。

示例：
    python experiments/run_experiment.py \
        --benchmark Sphere \
        --dimension 10 \
        --functions 1 \
        --algorithms PSO ARPSO-SRR AP-SRR-PSO DE \
        --runs 3 \
        --max-fes 5000 \
        --population-size 30 \
        --output results/raw/basic_demo.csv \
        --save-curves
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.factory import build_optimizer
from benchmarks.problem_factory import build_problem


@dataclass(frozen=True)
class Task:
    benchmark: str
    function_id: int
    algorithm: str
    dimension: int
    run: int
    seed: int
    population_size: int
    max_fes: int
    record_interval: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AP-SRR-PSO 统一实验入口")
    parser.add_argument("--benchmark", required=True, help="Sphere / Rastrigin / Ackley / CEC2017 / CEC2022")
    parser.add_argument("--dimension", type=int, required=True)
    parser.add_argument("--functions", nargs="+", type=int, required=True)
    parser.add_argument("--algorithms", nargs="+", required=True)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--max-fes", type=int, default=10000)
    parser.add_argument("--population-size", type=int, default=50)
    parser.add_argument("--base-seed", type=int, default=2026)
    parser.add_argument("--record-interval", type=int, default=10)
    parser.add_argument("--output", default="results/raw/experiment_results.csv")
    parser.add_argument("--n-jobs", type=int, default=1, help="并行任务数。Google Cloud 多核 CPU 可设为 8/16/32。")
    parser.add_argument("--save-curves", action="store_true", help="保存每个任务的收敛曲线 CSV。")
    return parser.parse_args()


def make_seed(base_seed: int, function_id: int, algorithm_index: int, run: int) -> int:
    return int(base_seed + function_id * 100000 + algorithm_index * 1000 + run)


def run_task(task: Task, curve_dir: Path | None = None) -> dict[str, Any]:
    problem = build_problem(task.benchmark, task.function_id, task.dimension)
    optimizer = build_optimizer(task.algorithm, population_size=task.population_size, seed=task.seed)

    start = time.perf_counter()
    result = optimizer.optimize(
        objective=problem.objective,
        dimension=task.dimension,
        lower_bound=problem.lower_bound,
        upper_bound=problem.upper_bound,
        max_fes=task.max_fes,
        record_interval=task.record_interval,
    )
    runtime = time.perf_counter() - start

    curve_file = ""
    if curve_dir is not None:
        curve_dir.mkdir(parents=True, exist_ok=True)
        safe_algorithm = result.algorithm.replace("/", "-").replace(" ", "_")
        curve_path = curve_dir / f"{problem.benchmark}_{problem.function}_{task.dimension}D_{safe_algorithm}_run{task.run}.csv"
        pd.DataFrame({"step": list(range(len(result.convergence_curve))), "best_fitness": result.convergence_curve}).to_csv(curve_path, index=False)
        curve_file = str(curve_path.relative_to(PROJECT_ROOT))

    metadata = dict(result.metadata)
    metadata.pop("diversity_curve", None)

    return {
        "benchmark": problem.benchmark,
        "function": problem.function,
        "function_id": task.function_id,
        "algorithm": result.algorithm,
        "dimension": task.dimension,
        "run": task.run,
        "seed": task.seed,
        "best_fitness": result.best_fitness,
        "function_evaluations": result.function_evaluations,
        "runtime_seconds": runtime,
        "restart_count": metadata.get("restart_count", 0),
        "curve_file": curve_file,
        "metadata": json.dumps(metadata, ensure_ascii=False),
    }


def main() -> None:
    args = parse_args()
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    curve_dir = PROJECT_ROOT / "results" / "curves" if args.save_curves else None

    tasks: list[Task] = []
    for function_id in args.functions:
        for algorithm_index, algorithm in enumerate(args.algorithms):
            for run in range(1, args.runs + 1):
                tasks.append(
                    Task(
                        benchmark=args.benchmark,
                        function_id=function_id,
                        algorithm=algorithm,
                        dimension=args.dimension,
                        run=run,
                        seed=make_seed(args.base_seed, function_id, algorithm_index, run),
                        population_size=args.population_size,
                        max_fes=args.max_fes,
                        record_interval=args.record_interval,
                    )
                )

    print(f"任务数: {len(tasks)}")
    print(f"输出文件: {output_path}")

    if args.n_jobs == 1:
        rows = [run_task(task, curve_dir=curve_dir) for task in tqdm(tasks, desc="运行实验")]
    else:
        rows = Parallel(n_jobs=args.n_jobs)(delayed(run_task)(task, curve_dir=curve_dir) for task in tqdm(tasks, desc="提交并行任务"))

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"实验完成，结果已保存: {output_path}")


if __name__ == "__main__":
    main()
