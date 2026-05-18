"""算法工厂。"""

from __future__ import annotations

from typing import Any

from algorithms.ap_srr_pso import APSRRPSO as AggressiveAPSRRPSO
from algorithms.ap_srr_pso_v2 import ConservativeAPSRRPSO
from algorithms.arpso_srr import ARPSOSRR
from algorithms.de import DifferentialEvolution
from algorithms.pso import PSO
from algorithms.pso_variants import PSOAW, PSORS


def _named(optimizer, display_name: str):
    """设置实验输出名称。

    注意：run_experiment.py 使用 result.algorithm 分组统计。若不同方向都返回同一个 name，
    结果会被错误合并，因此方向筛选必须保留各自名称。
    """
    optimizer.name = display_name
    return optimizer


def _with_operators(optimizer: ConservativeAPSRRPSO, operators: list[str], display_name: str):
    """为 AP-SRR-PSO 方向实验指定算子池和输出名称。"""
    optimizer.operators = operators
    return _named(optimizer, display_name)


def build_optimizer(name: str, *, population_size: int, seed: int | None = None, **kwargs: Any):
    """根据名称创建优化器。"""
    key = name.strip().upper().replace("_", "-")
    common = {"population_size": population_size, "seed": seed}

    if key == "PSO":
        return PSO(**common, **kwargs)
    if key in {"PSO-RS", "PSORS"}:
        return PSORS(**common, **kwargs)
    if key in {"PSO-AW", "PSOAW"}:
        return PSOAW(**common, **kwargs)
    if key in {"ARPSO-SRR", "ARPSO-SRR-BASE", "ARPSO-V4"}:
        return ARPSOSRR(**common, **kwargs)

    if key in {"AP-SRR-PSO", "APSRRPSO", "AP-SRR-PSO-V2", "AP-SRR-PSO-BALANCED"}:
        return _named(ConservativeAPSRRPSO(**common, **kwargs), "AP-SRR-PSO")
    if key in {"AP-SRR-PSO-V1", "AP-SRR-PSO-AGGRESSIVE"}:
        return _named(AggressiveAPSRRPSO(**common, **kwargs), "AP-SRR-PSO-V1")

    # 方向 A：极保守，仅做局部精修，检验 exploitation-preserving reallocation。
    if key in {"AP-SRR-PSO-LOCAL", "AP-SRR-LOCAL"}:
        opt = ConservativeAPSRRPSO(
            **common,
            stagnation_threshold=55,
            diversity_threshold=0.0,
            rho_min=0.01,
            rho_max=0.12,
            elite_ratio=0.25,
            local_sigma=0.030,
            **kwargs,
        )
        return _with_operators(opt, ["local"], "AP-SRR-PSO-LOCAL")

    # 方向 B：局部 + 差分，去掉 global/opposition，检验方向扰动是否更稳定。
    if key in {"AP-SRR-PSO-DIFF", "AP-SRR-DIFF", "AP-SRR-PSO-LOCAL-DIFF"}:
        opt = ConservativeAPSRRPSO(
            **common,
            stagnation_threshold=45,
            diversity_threshold=0.0,
            rho_min=0.02,
            rho_max=0.18,
            elite_ratio=0.20,
            local_sigma=0.040,
            softmax_temperature=0.55,
            **kwargs,
        )
        return _with_operators(opt, ["local", "differential"], "AP-SRR-PSO-DIFF")

    # 方向 C：罕见重分配，只在明显停滞后少量迁移，检验安全性。
    if key in {"AP-SRR-PSO-RARE", "AP-SRR-RARE"}:
        opt = ConservativeAPSRRPSO(
            **common,
            stagnation_threshold=70,
            diversity_threshold=0.0,
            rho_min=0.005,
            rho_max=0.10,
            elite_ratio=0.30,
            local_sigma=0.025,
            softmax_temperature=0.70,
            **kwargs,
        )
        return _with_operators(opt, ["local", "differential"], "AP-SRR-PSO-RARE")

    # 精筛 1：RARE-DIFF 稳健版，优先平衡稳定性和跳出能力。
    if key in {"AP-SRR-PSO-RD", "AP-SRR-RD", "AP-SRR-PSO-RARE-DIFF"}:
        opt = ConservativeAPSRRPSO(
            **common,
            stagnation_threshold=60,
            diversity_threshold=0.0,
            rho_min=0.010,
            rho_max=0.14,
            elite_ratio=0.28,
            local_sigma=0.030,
            softmax_temperature=0.65,
            **kwargs,
        )
        return _with_operators(opt, ["local", "differential"], "AP-SRR-PSO-RD")

    # 精筛 2：RARE-DIFF-C，极稳健版，重点降低 F1/F10 的极端坏 run。
    if key in {"AP-SRR-PSO-RD-C", "AP-SRR-RD-C"}:
        opt = ConservativeAPSRRPSO(
            **common,
            stagnation_threshold=75,
            diversity_threshold=0.0,
            rho_min=0.005,
            rho_max=0.10,
            elite_ratio=0.32,
            local_sigma=0.022,
            softmax_temperature=0.75,
            **kwargs,
        )
        return _with_operators(opt, ["local", "differential"], "AP-SRR-PSO-RD-C")

    # 精筛 3：RARE-DIFF-M，稍强响应版，针对 F10/F复杂多峰做补偿。
    if key in {"AP-SRR-PSO-RD-M", "AP-SRR-RD-M"}:
        opt = ConservativeAPSRRPSO(
            **common,
            stagnation_threshold=50,
            diversity_threshold=0.0,
            rho_min=0.015,
            rho_max=0.18,
            elite_ratio=0.25,
            local_sigma=0.035,
            softmax_temperature=0.60,
            **kwargs,
        )
        return _with_operators(opt, ["local", "differential"], "AP-SRR-PSO-RD-M")

    # 精筛 4：RARE-DIFF-E，带少量安全全局探索，测试复杂函数上是否值得保留 global。
    if key in {"AP-SRR-PSO-RD-E", "AP-SRR-RD-E"}:
        opt = ConservativeAPSRRPSO(
            **common,
            stagnation_threshold=55,
            diversity_threshold=0.0,
            rho_min=0.015,
            rho_max=0.16,
            elite_ratio=0.25,
            local_sigma=0.035,
            softmax_temperature=0.65,
            **kwargs,
        )
        return _with_operators(opt, ["local", "differential", "global"], "AP-SRR-PSO-RD-E")

    # 方向 D：中等强度组合策略，保留 portfolio，但限制破坏性算子比例。
    if key in {"AP-SRR-PSO-PORTFOLIO", "AP-SRR-PORTFOLIO"}:
        opt = ConservativeAPSRRPSO(
            **common,
            stagnation_threshold=45,
            diversity_threshold=0.0,
            rho_min=0.02,
            rho_max=0.20,
            elite_ratio=0.20,
            local_sigma=0.045,
            softmax_temperature=0.60,
            **kwargs,
        )
        return _with_operators(opt, ["local", "differential", "global", "opposition"], "AP-SRR-PSO-PORTFOLIO")

    # 方向 E：稍强探索，主要用于复杂多峰函数，不建议作为默认全局策略。
    if key in {"AP-SRR-PSO-EXPLORE", "AP-SRR-EXPLORE"}:
        opt = ConservativeAPSRRPSO(
            **common,
            stagnation_threshold=35,
            diversity_threshold=0.0,
            rho_min=0.03,
            rho_max=0.26,
            elite_ratio=0.18,
            local_sigma=0.060,
            softmax_temperature=0.50,
            **kwargs,
        )
        return _with_operators(opt, ["local", "differential", "global", "opposition"], "AP-SRR-PSO-EXPLORE")

    if key in {"AP-SRR-PSO-NO-IPS", "AP-SRR-PSO-WITHOUT-IPS"}:
        return _named(ConservativeAPSRRPSO(**common, enable_ips=False, **kwargs), "AP-SRR-PSO-NO-IPS")
    if key in {"AP-SRR-PSO-NO-ARP", "AP-SRR-PSO-WITHOUT-ARP"}:
        return _named(ConservativeAPSRRPSO(**common, enable_arp=False, **kwargs), "AP-SRR-PSO-NO-ARP")
    if key in {"AP-SRR-PSO-NO-RCA", "AP-SRR-PSO-WITHOUT-RCA"}:
        return _named(ConservativeAPSRRPSO(**common, enable_rca=False, **kwargs), "AP-SRR-PSO-NO-RCA")
    if key == "DE":
        return DifferentialEvolution(**common, **kwargs)

    raise ValueError(f"未知算法名称: {name}")
