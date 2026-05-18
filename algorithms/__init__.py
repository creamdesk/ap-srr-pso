"""算法模块。

所有算法统一暴露 optimize() 接口，便于批量实验脚本调用。
"""

from algorithms.ap_srr_pso import APSRRPSO
from algorithms.arpso_srr import ARPSOSRR
from algorithms.de import DifferentialEvolution
from algorithms.pso import PSO
from algorithms.pso_variants import PSOAW, PSORS

__all__ = ["PSO", "PSORS", "PSOAW", "ARPSOSRR", "APSRRPSO", "DifferentialEvolution"]
