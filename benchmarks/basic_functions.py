"""基础测试函数。

这些函数主要用于快速自检，不用于最终 SCI 论文主实验。
"""

from __future__ import annotations

import numpy as np


def sphere(x: np.ndarray) -> float:
    """Sphere 函数，单峰基础测试。最优值为 0。"""
    return float(np.sum(x**2))


def rastrigin(x: np.ndarray) -> float:
    """Rastrigin 函数，多峰基础测试。最优值为 0。"""
    dimension = x.size
    return float(10 * dimension + np.sum(x**2 - 10 * np.cos(2 * np.pi * x)))


def ackley(x: np.ndarray) -> float:
    """Ackley 函数，多峰基础测试。最优值为 0。"""
    dimension = x.size
    sum_sq = np.sum(x**2)
    sum_cos = np.sum(np.cos(2 * np.pi * x))
    return float(-20 * np.exp(-0.2 * np.sqrt(sum_sq / dimension)) - np.exp(sum_cos / dimension) + 20 + np.e)
