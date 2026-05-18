"""统一算法接口和结果结构。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

Objective = Callable[[np.ndarray], float]


@dataclass
class OptimizationResult:
    """单次优化运行结果。"""

    algorithm: str
    best_fitness: float
    best_position: list[float]
    function_evaluations: int
    convergence_curve: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def as_bounds(dimension: int, lower_bound: float | np.ndarray, upper_bound: float | np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """把标量/向量边界统一转换为 numpy 数组。"""
    lb = np.full(dimension, lower_bound, dtype=float) if np.isscalar(lower_bound) else np.asarray(lower_bound, dtype=float)
    ub = np.full(dimension, upper_bound, dtype=float) if np.isscalar(upper_bound) else np.asarray(upper_bound, dtype=float)
    if lb.shape != (dimension,) or ub.shape != (dimension,):
        raise ValueError("边界维度必须与 dimension 一致。")
    if np.any(ub <= lb):
        raise ValueError("upper_bound 必须大于 lower_bound。")
    return lb, ub


def population_diversity(positions: np.ndarray, lb: np.ndarray, ub: np.ndarray) -> float:
    """归一化群体多样性。"""
    normalized = (positions - lb) / (ub - lb)
    center = np.mean(normalized, axis=0)
    return float(np.mean(np.linalg.norm(normalized - center, axis=1)) / np.sqrt(positions.shape[1]))


def stable_softmax(values: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """数值稳定 softmax。"""
    if temperature <= 0:
        raise ValueError("temperature 必须为正数。")
    scaled = values / temperature
    scaled = scaled - np.max(scaled)
    exp_values = np.exp(scaled)
    total = np.sum(exp_values)
    if total <= 0 or not np.isfinite(total):
        return np.full(values.shape, 1.0 / values.size)
    return exp_values / total
