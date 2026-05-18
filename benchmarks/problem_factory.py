"""统一 benchmark problem 工厂。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from benchmarks.basic_functions import ackley, rastrigin, sphere
from benchmarks.cec_adapter import load_cec2017_problem, load_cec2022_problem


@dataclass(frozen=True)
class Problem:
    """统一问题对象。"""

    benchmark: str
    function: str
    dimension: int
    lower_bound: float | np.ndarray
    upper_bound: float | np.ndarray
    objective: Callable[[np.ndarray], float]
    optimum: float | None = None


def build_problem(benchmark: str, function_id: int | str, dimension: int) -> Problem:
    """创建 benchmark 问题。"""
    key = str(benchmark).strip().upper()
    if key in {"SPHERE", "BASIC-SPHERE"}:
        return Problem("BASIC", "Sphere", dimension, -100.0, 100.0, sphere, 0.0)
    if key in {"RASTRIGIN", "BASIC-RASTRIGIN"}:
        return Problem("BASIC", "Rastrigin", dimension, -5.12, 5.12, rastrigin, 0.0)
    if key in {"ACKLEY", "BASIC-ACKLEY"}:
        return Problem("BASIC", "Ackley", dimension, -32.768, 32.768, ackley, 0.0)
    if key == "CEC2017":
        return load_cec2017_problem(int(function_id), dimension)
    if key == "CEC2022":
        return load_cec2022_problem(int(function_id), dimension)
    raise ValueError(f"未知 benchmark: {benchmark}")
