"""CEC benchmark 统一适配器。

所有 CEC 函数加载逻辑集中在这里，不要在实验脚本里分散处理。
当前实现优先兼容 opfunu 常见 API：

    from opfunu.cec_based.cec2017 import F12017
    problem = F12017(ndim=30)
    problem.evaluate(x)

如果某个 opfunu 版本缺少 F30，会明确报错，并列出建议。
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BenchmarkProblem:
    """统一 CEC 问题结构。"""

    benchmark: str
    function: str
    dimension: int
    lower_bound: float | np.ndarray
    upper_bound: float | np.ndarray
    objective: Callable[[np.ndarray], float]
    optimum: float | None = None


class CECAdapterError(RuntimeError):
    """CEC 适配错误。"""


def _scalar_or_array_bound(value, default: float, dimension: int) -> float | np.ndarray:
    if value is None:
        return default
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return float(arr)
    if arr.size == dimension:
        return arr.reshape(dimension)
    return default


def _get_bound(problem: object, names: list[str], default: float, dimension: int) -> float | np.ndarray:
    for name in names:
        if hasattr(problem, name):
            return _scalar_or_array_bound(getattr(problem, name), default, dimension)
    return default


def _get_optimum(problem: object) -> float | None:
    for name in ["f_global", "f_shift", "bias", "global_optimum", "f_bias"]:
        if hasattr(problem, name):
            try:
                value = getattr(problem, name)
                arr = np.asarray(value, dtype=float)
                if arr.ndim == 0:
                    return float(arr)
            except Exception:
                continue
    return None


def _call_evaluate(problem: object, x: np.ndarray) -> float:
    if hasattr(problem, "evaluate"):
        return float(problem.evaluate(np.asarray(x, dtype=float)))
    if callable(problem):
        return float(problem(np.asarray(x, dtype=float)))
    raise CECAdapterError("CEC problem 不包含 evaluate 方法，也不是 callable 对象。")


def _instantiate_problem(module_name: str, class_candidates: list[str], dimension: int):
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise CECAdapterError(f"无法导入 {module_name}。请先安装 opfunu：pip install opfunu") from exc

    available = [name for name in dir(module) if name.startswith("F")]
    for class_name in class_candidates:
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            for kwargs in [{"ndim": dimension}, {"dim": dimension}, {"dimension": dimension}, {}]:
                try:
                    return cls(**kwargs)
                except TypeError:
                    continue
            try:
                return cls(dimension)
            except TypeError as exc:
                raise CECAdapterError(f"找到 {class_name}，但无法用维度 {dimension} 初始化。") from exc

    raise CECAdapterError(
        "当前 opfunu 版本中找不到目标 CEC 函数类。\n"
        f"模块: {module_name}\n"
        f"尝试类名: {class_candidates}\n"
        f"可用类名前 20 个: {available[:20]}\n"
        "建议：升级 opfunu，或把旧项目中已验证的官方 CEC 适配文件迁移进 benchmarks/。"
    )


def load_cec2017_problem(function_id: int, dimension: int) -> BenchmarkProblem:
    """加载 CEC2017 问题。"""
    if not 1 <= function_id <= 30:
        raise ValueError("CEC2017 function_id 应在 1-30 之间。")
    class_candidates = [f"F{function_id}2017", f"F{function_id:02d}2017"]
    problem = _instantiate_problem("opfunu.cec_based.cec2017", class_candidates, dimension)
    lb = _get_bound(problem, ["lb", "lower", "lower_bound", "bounds_lower"], -100.0, dimension)
    ub = _get_bound(problem, ["ub", "upper", "upper_bound", "bounds_upper"], 100.0, dimension)
    optimum = _get_optimum(problem)

    return BenchmarkProblem(
        benchmark="CEC2017",
        function=f"F{function_id}",
        dimension=dimension,
        lower_bound=lb,
        upper_bound=ub,
        objective=lambda x: _call_evaluate(problem, x),
        optimum=optimum,
    )


def load_cec2022_problem(function_id: int, dimension: int) -> BenchmarkProblem:
    """加载 CEC2022 问题。"""
    if not 1 <= function_id <= 12:
        raise ValueError("CEC2022 function_id 通常应在 1-12 之间。")
    class_candidates = [f"F{function_id}2022", f"F{function_id:02d}2022"]
    problem = _instantiate_problem("opfunu.cec_based.cec2022", class_candidates, dimension)
    lb = _get_bound(problem, ["lb", "lower", "lower_bound", "bounds_lower"], -100.0, dimension)
    ub = _get_bound(problem, ["ub", "upper", "upper_bound", "bounds_upper"], 100.0, dimension)
    optimum = _get_optimum(problem)

    return BenchmarkProblem(
        benchmark="CEC2022",
        function=f"F{function_id}",
        dimension=dimension,
        lower_bound=lb,
        upper_bound=ub,
        objective=lambda x: _call_evaluate(problem, x),
        optimum=optimum,
    )
