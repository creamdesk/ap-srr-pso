"""算法工厂。"""

from __future__ import annotations

from typing import Any

from algorithms.ap_srr_pso import APSRRPSO as AggressiveAPSRRPSO
from algorithms.ap_srr_pso_v2 import ConservativeAPSRRPSO
from algorithms.arpso_srr import ARPSOSRR
from algorithms.de import DifferentialEvolution
from algorithms.pso import PSO
from algorithms.pso_variants import PSOAW, PSORS


def _with_operators(optimizer: ConservativeAPSRRPSO, operators: list[str]):
    """为 AP-SRR-PSO 方向实验指定算子池。"""
    optimizer.operators = operators
    return optimizer


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
        return ConservativeAPSRRPSO(**common, **kwargs)
    if key in {"AP-SRR-PSO-V1", "AP-SRR-PSO-AGGRESSIVE"}:
        return AggressiveAPSRRPSO(**common, **kwargs)

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
        return _with_operators(opt, ["local"])

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
        return _with_operators(opt, ["local", "differential"])

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
        return _with_operators(opt, ["local", "differential"])

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
        return _with_operators(opt, ["local", "differential", "global", "opposition"])

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
        return _with_operators(opt, ["local", "differential", "global", "opposition"])

    if key in {"AP-SRR-PSO-NO-IPS", "AP-SRR-PSO-WITHOUT-IPS"}:
        return ConservativeAPSRRPSO(**common, enable_ips=False, **kwargs)
    if key in {"AP-SRR-PSO-NO-ARP", "AP-SRR-PSO-WITHOUT-ARP"}:
        return ConservativeAPSRRPSO(**common, enable_arp=False, **kwargs)
    if key in {"AP-SRR-PSO-NO-RCA", "AP-SRR-PSO-WITHOUT-RCA"}:
        return ConservativeAPSRRPSO(**common, enable_rca=False, **kwargs)
    if key == "DE":
        return DifferentialEvolution(**common, **kwargs)

    raise ValueError(f"未知算法名称: {name}")
