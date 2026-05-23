from argparse import Namespace

import pandas as pd

from algorithms.factory import build_optimizer
from analysis.summarize_results import summarize
from experiments.run_experiment import build_tasks


def test_factory_builds_core_algorithms() -> None:
    names = ["AP-SRR-PSO", "ARPSO-SRR", "PSO", "PSO-RS", "PSO-AW", "DE"]
    for index, name in enumerate(names):
        optimizer = build_optimizer(name, population_size=8, seed=20260523 + index)
        assert hasattr(optimizer, "optimize")


def test_run_experiment_build_tasks_is_deterministic() -> None:
    args = Namespace(
        benchmark="CEC2017",
        dimension=30,
        functions=[1, 3],
        algorithms=["PSO", "AP-SRR-PSO"],
        runs=2,
        population_size=50,
        max_fes=1000,
        base_seed=20260523,
        record_interval=10,
    )
    tasks = build_tasks(args)
    assert len(tasks) == 8
    assert tasks[0].seed == 20360524
    assert tasks[-1].algorithm == "AP-SRR-PSO"


def test_summarize_accepts_function_id_schema() -> None:
    df = pd.DataFrame(
        [
            {"benchmark": "CEC2017", "function_id": 1, "algorithm": "PSO", "dimension": 10, "best_fitness": 2.0, "status": "ok"},
            {"benchmark": "CEC2017", "function_id": 1, "algorithm": "PSO", "dimension": 10, "best_fitness": 4.0, "status": "ok"},
            {
                "benchmark": "CEC2017",
                "function_id": 1,
                "algorithm": "AP-SRR-PSO",
                "dimension": 10,
                "best_fitness": 1.0,
                "status": "ok",
            },
        ]
    )
    summary = summarize(df)
    assert set(summary["function"]) == {"F1"}
    assert set(summary["algorithm"]) == {"PSO", "AP-SRR-PSO"}
    assert summary.loc[summary["algorithm"] == "PSO", "mean"].item() == 3.0
