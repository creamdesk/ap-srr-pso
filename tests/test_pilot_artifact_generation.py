import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_module(*args: str) -> None:
    subprocess.run([sys.executable, "-m", *args], cwd=ROOT, check=True)


def test_generate_tables_and_figures_from_synthetic_pilot() -> None:
    experiment = "pytest_synthetic_pilot"
    raw = ROOT / "results" / "raw" / f"{experiment}_raw.csv"
    summary = ROOT / "results" / "summary" / f"{experiment}_summary.csv"
    convergence = ROOT / "results" / "raw" / f"{experiment}_convergence.csv"
    curves = ROOT / "results" / "curves" / f"{experiment}_curves.jsonl"

    raw_rows = []
    for algorithm, base in [("ARPSO-SRR", 1.0), ("PSO-RS", 2.0)]:
        for run_id in [1, 2]:
            raw_rows.append(
                {
                    "experiment_name": experiment,
                    "benchmark": "CEC2017",
                    "function": "F1",
                    "function_id": 1,
                    "dimension": 10,
                    "algorithm": algorithm,
                    "run": run_id,
                    "run_id": run_id,
                    "seed": 20260000 + run_id,
                    "population_size": 8,
                    "max_fes": 40,
                    "best_fitness": base + run_id,
                    "error_value": base + run_id - 100.0,
                    "function_evaluations": 40,
                    "runtime_seconds": 0.01 * run_id,
                    "restart_count": run_id if algorithm == "ARPSO-SRR" else 0,
                    "operator_usage": "{}",
                    "operator_success": "{}",
                    "status": "ok",
                    "success_flag": 1,
                    "error": "",
                }
            )
    write_csv(raw, raw_rows)
    write_csv(
        summary,
        [
            {
                "experiment_name": experiment,
                "benchmark": "CEC2017",
                "function": "F1",
                "function_id": 1,
                "dimension": 10,
                "algorithm": "ARPSO-SRR",
                "runs": 2,
                "mean_best": 2.5,
                "std_best": 0.7,
                "median_best": 2.5,
                "best": 2.0,
                "worst": 3.0,
                "mean_runtime_seconds": 0.015,
                "total_runtime_seconds": 0.03,
                "success_count": 2,
                "failure_count": 0,
            },
            {
                "experiment_name": experiment,
                "benchmark": "CEC2017",
                "function": "F1",
                "function_id": 1,
                "dimension": 10,
                "algorithm": "PSO-RS",
                "runs": 2,
                "mean_best": 3.5,
                "std_best": 0.7,
                "median_best": 3.5,
                "best": 3.0,
                "worst": 4.0,
                "mean_runtime_seconds": 0.015,
                "total_runtime_seconds": 0.03,
                "success_count": 2,
                "failure_count": 0,
            },
        ],
    )
    write_csv(
        convergence,
        [
            {"algorithm": "ARPSO-SRR", "function_id": 1, "run_id": 1, "fe": 0, "best_so_far": 5.0},
            {"algorithm": "ARPSO-SRR", "function_id": 1, "run_id": 1, "fe": 40, "best_so_far": 2.0},
            {"algorithm": "PSO-RS", "function_id": 1, "run_id": 1, "fe": 0, "best_so_far": 6.0},
            {"algorithm": "PSO-RS", "function_id": 1, "run_id": 1, "fe": 40, "best_so_far": 3.0},
        ],
    )
    curves.parent.mkdir(parents=True, exist_ok=True)
    curves.write_text(
        json.dumps({"function": "F1", "function_id": 1, "algorithm": "ARPSO-SRR", "run": 1, "convergence_curve": [5.0, 2.0], "function_evaluations": 40})
        + "\n",
        encoding="utf-8",
    )

    run_module("analysis.generate_tables", "--experiment", experiment)
    run_module("analysis.generate_figures", "--experiment", experiment, "--no-png")

    assert (ROOT / "results" / "tables" / f"{experiment}_summary.tex").stat().st_size > 0
    assert (ROOT / "results" / "figures" / f"{experiment}_ranking.tex").stat().st_size > 0
    assert (ROOT / "results" / "figures" / f"{experiment}_convergence.tex").stat().st_size > 0
    assert (ROOT / "results" / "figures" / f"{experiment}_restart.tex").stat().st_size > 0
