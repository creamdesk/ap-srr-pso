"""CEC benchmark 适配器。

当前文件先提供统一接口。正式实验时应在这里集中处理 CEC2017/CEC2022 的函数编号、维度、边界和 opfunu 兼容问题。
不要在各个实验脚本里重复写 CEC 加载逻辑，否则后期极容易出现 F30 缺失、编号不一致、维度不一致等问题。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BenchmarkProblem:
    """统一基准问题结构。"""

    name: str
    function_id: int
    dimension: int
    lower_bound: float
    upper_bound: float
    objective: Callable[[np.ndarray], float]
    optimum: float | None = None


class CECAdapterError(RuntimeError):
    """CEC 适配错误。"""


def load_cec2017_problem(function_id: int, dimension: int) -> BenchmarkProblem:
    """加载 CEC2017 问题。

    说明：
        这里先保留接口。后续迁移旧项目时，把原有 cec_adapter.py 中经过验证的 opfunu 映射逻辑放到这里。
    """
    raise CECAdapterError(
        "CEC2017 adapter 尚未接入。请先使用 benchmarks/basic_functions.py 做 smoke test，"
        "再迁移旧项目中已经验证过的 CEC2017 适配逻辑。"
    )


def load_cec2022_problem(function_id: int, dimension: int) -> BenchmarkProblem:
    """加载 CEC2022 问题。"""
    raise CECAdapterError("CEC2022 adapter 尚未接入。")
