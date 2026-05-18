"""算法工厂。"""

from __future__ import annotations

from typing import Any

from algorithms.ap_srr_pso import APSRRPSO
from algorithms.arpso_srr import ARPSOSRR
from algorithms.de import DifferentialEvolution
from algorithms.pso import PSO
from algorithms.pso_variants import PSOAW, PSORS


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
    if key in {"AP-SRR-PSO", "APSRRPSO"}:
        return APSRRPSO(**common, **kwargs)
    if key in {"AP-SRR-PSO-NO-IPS", "AP-SRR-PSO-WITHOUT-IPS"}:
        return APSRRPSO(**common, enable_ips=False, **kwargs)
    if key in {"AP-SRR-PSO-NO-ARP", "AP-SRR-PSO-WITHOUT-ARP"}:
        return APSRRPSO(**common, enable_arp=False, **kwargs)
    if key in {"AP-SRR-PSO-NO-RCA", "AP-SRR-PSO-WITHOUT-RCA"}:
        return APSRRPSO(**common, enable_rca=False, **kwargs)
    if key == "DE":
        return DifferentialEvolution(**common, **kwargs)

    raise ValueError(f"未知算法名称: {name}")
