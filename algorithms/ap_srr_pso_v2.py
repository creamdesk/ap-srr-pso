"""Conservative AP-SRR-PSO implementation.

This version is used as the default AP-SRR-PSO after the first cloud smoke test.
The initial version was too aggressive on simple and short-budget CEC2017 cases.
"""

from __future__ import annotations

import numpy as np

from algorithms.ap_srr_pso import APSRRPSO
from algorithms.base import stable_softmax


class ConservativeAPSRRPSO(APSRRPSO):
    """A more conservative AP-SRR-PSO variant.

    Main changes:
    - less frequent reallocation;
    - smaller reallocation ratio;
    - larger elite protection ratio;
    - lower probability for global and opposition moves;
    - smaller local perturbation scale.
    """

    name = "AP-SRR-PSO"

    def __init__(
        self,
        population_size: int = 50,
        inertia_weight: float = 0.729,
        cognitive_coefficient: float = 1.49445,
        social_coefficient: float = 1.49445,
        stagnation_threshold: int = 45,
        diversity_threshold: float = 0.0,
        rho_min: float = 0.02,
        rho_max: float = 0.18,
        elite_ratio: float = 0.20,
        local_sigma: float = 0.045,
        credit_window: int = 80,
        softmax_temperature: float = 0.60,
        seed: int | None = None,
        velocity_clamp_ratio: float = 0.2,
        enable_ips: bool = True,
        enable_arp: bool = True,
        enable_rca: bool = True,
    ) -> None:
        super().__init__(
            population_size=population_size,
            inertia_weight=inertia_weight,
            cognitive_coefficient=cognitive_coefficient,
            social_coefficient=social_coefficient,
            stagnation_threshold=stagnation_threshold,
            diversity_threshold=diversity_threshold,
            rho_min=rho_min,
            rho_max=rho_max,
            elite_ratio=elite_ratio,
            local_sigma=local_sigma,
            credit_window=credit_window,
            softmax_temperature=softmax_temperature,
            seed=seed,
            velocity_clamp_ratio=velocity_clamp_ratio,
            enable_ips=enable_ips,
            enable_arp=enable_arp,
            enable_rca=enable_rca,
        )
        self.operators = ["local", "differential", "global", "opposition"] if enable_arp else ["global"]

    def _operator_probabilities(self) -> np.ndarray:
        if len(self.operators) == 1:
            return np.array([1.0])

        prior_map = {
            "local": 0.50,
            "differential": 0.30,
            "global": 0.12,
            "opposition": 0.08,
        }
        prior = np.array([prior_map.get(op, 1.0 / len(self.operators)) for op in self.operators], dtype=float)
        prior = prior / np.sum(prior)

        if (not self.enable_rca) or len(self.credit_history) < max(8, 2 * len(self.operators)):
            return prior

        score = np.zeros(len(self.operators), dtype=float)
        count = np.zeros(len(self.operators), dtype=float)
        index = {op: i for i, op in enumerate(self.operators)}
        for record in self.credit_history:
            if record.operator not in index:
                continue
            i = index[record.operator]
            score[i] += record.success + np.log1p(max(0.0, record.improvement))
            count[i] += 1.0
        learned = stable_softmax(score / np.maximum(count, 1.0), temperature=self.softmax_temperature)
        return 0.60 * learned + 0.40 * prior

    def _generate_candidate(self, operator, positions, pbest_positions, gbest_position, lb, ub, fes, max_fes):
        dimension = gbest_position.size
        progress = fes / max(max_fes, 1)

        if operator == "local":
            sigma = self.local_sigma * (ub - lb) * max(0.02, (1.0 - progress) ** 0.5)
            return np.clip(gbest_position + self.rng.normal(0.0, sigma, size=dimension), lb, ub)

        if operator == "differential":
            if self.population_size < 4:
                return self.rng.uniform(lb, ub)
            ids = self.rng.choice(self.population_size, size=3, replace=False)
            x1, x2, x3 = pbest_positions[ids]
            scale = self.rng.uniform(0.20, 0.55)
            candidate = gbest_position + scale * (x2 - x3) + 0.15 * (x1 - gbest_position)
            return np.clip(candidate, lb, ub)

        if operator == "opposition":
            base = pbest_positions[self.rng.integers(0, self.population_size)]
            opposite = lb + ub - base
            beta = self.rng.uniform(0.15, 0.45)
            candidate = (1.0 - beta) * gbest_position + beta * opposite
            return np.clip(candidate, lb, ub)

        if operator == "global":
            # Keep global moves, but bias them mildly toward the best region.
            random_point = self.rng.uniform(lb, ub)
            beta = self.rng.uniform(0.10, 0.35)
            return np.clip((1.0 - beta) * gbest_position + beta * random_point, lb, ub)

        return super()._generate_candidate(operator, positions, pbest_positions, gbest_position, lb, ub, fes, max_fes)
