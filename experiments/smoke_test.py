"""快速自检脚本。

运行：
    python experiments/smoke_test.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.factory import build_optimizer
from benchmarks.problem_factory import build_problem

OUTPUT_DIR = PROJECT_ROOT / "results" / "summary"
OUTPUT_FILE = OUTPUT_DIR / "smoke_test_result.csv"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    problem = build_problem("Sphere", function_id=1, dimension=10)
    optimizer = build_optimizer("AP-SRR-PSO", population_size=20, seed=2026)
    result = optimizer.optimize(
        objective=problem.objective,
        dimension=problem.dimension,
        lower_bound=problem.lower_bound,
        upper_bound=problem.upper_bound,
        max_fes=2000,
        record_interval=5,
    )

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["algorithm", "benchmark", "function", "best_fitness", "function_evaluations", "curve_length"])
        writer.writeheader()
        writer.writerow(
            {
                "algorithm": result.algorithm,
                "benchmark": problem.benchmark,
                "function": problem.function,
                "best_fitness": result.best_fitness,
                "function_evaluations": result.function_evaluations,
                "curve_length": len(result.convergence_curve),
            }
        )

    print("环境检查通过")
    print("AP-SRR-PSO 小规模测试通过")
    print(f"最优值: {result.best_fitness:.6e}")
    print(f"函数评价次数: {result.function_evaluations}")
    print(f"结果文件已生成: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
