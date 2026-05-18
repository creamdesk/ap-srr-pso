"""统一算法接口和结果结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OptimizationResult:
    """单次优化运行结果。

    Attributes:
        algorithm: 算法名称。
        best_fitness: 最优适应度值。
        best_position: 最优位置。
        function_evaluations: 已使用函数评价次数。
        convergence_curve: 收敛曲线，通常记录每一代或固定间隔的全局最优值。
        metadata: 额外日志，例如重启次数、算子使用次数、运行时间等。
    """

    algorithm: str
    best_fitness: float
    best_position: list[float]
    function_evaluations: int
    convergence_curve: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
