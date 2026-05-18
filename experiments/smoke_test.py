"""快速自检脚本。

用途：
1. 检查 Python 包导入是否正常；
2. 检查基础 PSO 是否能完成一次小规模优化；
3. 检查结果目录和 CSV 输出是否正常。

运行：
    python experiments/smoke_test.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from algorithms.pso import PSO
from benchmarks.basic_functions import sphere


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "results" / "summary"
OUTPUT_FILE = OUTPUT_DIR / "smoke_test_result.csv"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    optimizer = PSO(population_size=20, seed=2026)
    result = optimizer.optimize(
        objective=sphere,
        dimension=10,
        lower_bound=-100.0,
        upper_bound=100.0,
        max_fes=2000,
        record_interval=5,
    )

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["algorithm", "best_fitness", "function_evaluations", "curve_length"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "algorithm": result.algorithm,
                "best_fitness": result.best_fitness,
                "function_evaluations": result.function_evaluations,
                "curve_length": len(result.convergence_curve),
            }
        )

    print("环境检查通过")
    print("PSO 小规模测试通过")
    print(f"最优值: {result.best_fitness:.6e}")
    print(f"函数评价次数: {result.function_evaluations}")
    print(f"结果文件已生成: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
