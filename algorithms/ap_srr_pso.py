"""AP-SRR-PSO：自适应组合搜索资源重分配粒子群优化算法。

核心模块：
1. IPS：Ineffective Particle Score，低效粒子评分；
2. ARP：Adaptive Restart Portfolio，自适应重启算子组合；
3. RCA：Restart Credit Assignment，重启贡献度分配。
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass

import numpy as np

from algorithms.base import Objective, OptimizationResult, as_bounds, population_diversity, stable_softmax


@dataclass
class OperatorRecord:
    """重启算子使用记录。"""

    operator: str
    success: int
    improvement: float


class APSRRPSO:
    """Adaptive Portfolio Search Resource Reallocation PSO."""

    name = "AP-SRR-PSO"

    def __init__(
        self,
        population_size: int = 50,
        inertia_weight: float = 0.729,
        cognitive_coefficient: float = 1.49445,
        social_coefficient: float = 1.49445,
        stagnation_threshold: int = 25,
        diversity_threshold: float = 0.08,
        rho_min: float = 0.05,
        rho_max: float = 0.40,
        elite_ratio: float = 0.1,
        local_sigma: float = 0.12,
        credit_window: int = 80,
        softmax_temperature: float = 0.25,
        seed: int | None = None,
        velocity_clamp_ratio: float = 0.2,
        enable_ips: bool = True,
        enable_arp: bool = True,
        enable_rca: bool = True,
    ) -> None:
        self.population_size = population_size
        self.inertia_weight = inertia_weight
        self.cognitive_coefficient = cognitive_coefficient
        self.social_coefficient = social_coefficient
        self.stagnation_threshold = stagnation_threshold
        self.diversity_threshold = diversity_threshold
        self.rho_min = rho_min
        self.rho_max = rho_max
        self.elite_ratio = elite_ratio
        self.local_sigma = local_sigma
        self.credit_window = credit_window
        self.softmax_temperature = softmax_temperature
        self.velocity_clamp_ratio = velocity_clamp_ratio
        self.enable_ips = enable_ips
        self.enable_arp = enable_arp
        self.enable_rca = enable_rca
        self.rng = np.random.default_rng(seed)
        self.operators = ["global", "local", "opposition", "differential"]
        if not enable_arp:
            self.operators = ["global"]
        self.credit_history: deque[OperatorRecord] = deque(maxlen=credit_window)

    def _restart_intensity(self, global_stagnation: int, diversity: float) -> float:
        stagnation_score = min(1.0, global_stagnation / max(1, self.stagnation_threshold))
        diversity_loss = max(0.0, (self.diversity_threshold - diversity) / max(self.diversity_threshold, 1e-12))
        score = 0.55 * stagnation_score + 0.45 * diversity_loss
        return float(self.rho_min + (self.rho_max - self.rho_min) * np.clip(score, 0.0, 1.0))

    def _operator_probabilities(self) -> np.ndarray:
        if (not self.enable_rca) or len(self.credit_history) < max(4, len(self.operators)):
            return np.full(len(self.operators), 1.0 / len(self.operators))
        score = np.zeros(len(self.operators), dtype=float)
        count = np.zeros(len(self.operators), dtype=float)
        index = {op: i for i, op in enumerate(self.operators)}
        for record in self.credit_history:
            if record.operator not in index:
                continue
            i = index[record.operator]
            score[i] += record.success + np.log1p(max(0.0, record.improvement))
            count[i] += 1.0
        avg_score = np.divide(score, np.maximum(count, 1.0))
        return stable_softmax(avg_score, temperature=self.softmax_temperature)

    def _ineffective_scores(self, fitness: np.ndarray, pbest_fitness: np.ndarray, particle_stagnation: np.ndarray, distances_to_gbest: np.ndarray) -> np.ndarray:
        """IPS：计算低效粒子评分，分数越高越优先被重分配。"""
        if not self.enable_ips:
            return particle_stagnation.astype(float)

        def normalize(v: np.ndarray) -> np.ndarray:
            v = v.astype(float)
            span = float(np.max(v) - np.min(v))
            if span <= 1e-12:
                return np.zeros_like(v, dtype=float)
            return (v - np.min(v)) / span

        rank_badness = normalize(pbest_fitness)
        stagnation_badness = normalize(particle_stagnation)
        crowding_badness = 1.0 - normalize(distances_to_gbest)
        current_badness = normalize(fitness)
        return 0.35 * rank_badness + 0.35 * stagnation_badness + 0.15 * crowding_badness + 0.15 * current_badness

    def _generate_candidate(self, operator: str, positions: np.ndarray, pbest_positions: np.ndarray, gbest_position: np.ndarray, lb: np.ndarray, ub: np.ndarray, fes: int, max_fes: int) -> np.ndarray:
        dimension = gbest_position.size
        if operator == "global":
            return self.rng.uniform(lb, ub)
        if operator == "local":
            sigma = self.local_sigma * (ub - lb) * max(0.03, 1.0 - fes / max_fes)
            return np.clip(gbest_position + self.rng.normal(0.0, sigma, size=dimension), lb, ub)
        if operator == "opposition":
            base = pbest_positions[self.rng.integers(0, self.population_size)]
            opposite = lb + ub - base
            jitter = self.rng.normal(0.0, 0.03 * (ub - lb), size=dimension)
            return np.clip(opposite + jitter, lb, ub)
        if operator == "differential":
            if self.population_size < 4:
                return self.rng.uniform(lb, ub)
            ids = self.rng.choice(self.population_size, size=3, replace=False)
            x1, x2, x3 = positions[ids]
            f = self.rng.uniform(0.4, 0.9)
            candidate = x1 + f * (x2 - x3)
            mix = self.rng.uniform(0.0, 0.35)
            candidate = (1.0 - mix) * candidate + mix * gbest_position
            return np.clip(candidate, lb, ub)
        raise ValueError(f"未知重启算子: {operator}")

    def optimize(self, objective: Objective, dimension: int, lower_bound: float | np.ndarray, upper_bound: float | np.ndarray, max_fes: int, record_interval: int = 1) -> OptimizationResult:
        lb, ub = as_bounds(dimension, lower_bound, upper_bound)
        positions = self.rng.uniform(lb, ub, size=(self.population_size, dimension))
        vmax = self.velocity_clamp_ratio * (ub - lb)
        velocities = self.rng.uniform(-vmax, vmax, size=(self.population_size, dimension))
        fitness = np.array([objective(x) for x in positions], dtype=float)
        fes = self.population_size

        pbest_positions = positions.copy()
        pbest_fitness = fitness.copy()
        particle_stagnation = np.zeros(self.population_size, dtype=int)
        best_idx = int(np.argmin(fitness))
        gbest_position = positions[best_idx].copy()
        gbest_fitness = float(fitness[best_idx])

        convergence_curve = [gbest_fitness]
        diversity_curve = [population_diversity(positions, lb, ub)]
        operator_usage: Counter[str] = Counter()
        operator_success: Counter[str] = Counter()
        restart_count = 0
        global_stagnation = 0
        iteration = 0

        while fes < max_fes:
            iteration += 1
            old_best = gbest_fitness
            r1 = self.rng.random((self.population_size, dimension))
            r2 = self.rng.random((self.population_size, dimension))
            velocities = (
                self.inertia_weight * velocities
                + self.cognitive_coefficient * r1 * (pbest_positions - positions)
                + self.social_coefficient * r2 * (gbest_position - positions)
            )
            velocities = np.clip(velocities, -vmax, vmax)
            positions = np.clip(positions + velocities, lb, ub)

            for i in range(self.population_size):
                if fes >= max_fes:
                    break
                value = float(objective(positions[i]))
                fitness[i] = value
                fes += 1
                if value < pbest_fitness[i]:
                    pbest_fitness[i] = value
                    pbest_positions[i] = positions[i].copy()
                    particle_stagnation[i] = 0
                    if value < gbest_fitness:
                        gbest_fitness = value
                        gbest_position = positions[i].copy()
                else:
                    particle_stagnation[i] += 1

            global_stagnation = 0 if gbest_fitness < old_best else global_stagnation + 1
            diversity = population_diversity(positions, lb, ub)
            trigger_restart = global_stagnation >= self.stagnation_threshold or diversity < self.diversity_threshold

            if trigger_restart and fes < max_fes:
                rho = self._restart_intensity(global_stagnation, diversity)
                restart_n = max(1, int(round(rho * self.population_size)))
                elite_n = max(1, int(round(self.elite_ratio * self.population_size)))
                elite_indices = set(np.argsort(pbest_fitness)[:elite_n].tolist())
                distances = np.linalg.norm((positions - gbest_position) / (ub - lb), axis=1)
                scores = self._ineffective_scores(fitness, pbest_fitness, particle_stagnation, distances)
                ranking = np.argsort(-scores)
                selected = np.array([idx for idx in ranking if idx not in elite_indices][:restart_n], dtype=int)

                if selected.size > 0:
                    probs = self._operator_probabilities()
                    for idx in selected:
                        if fes >= max_fes:
                            break
                        old_pbest = float(pbest_fitness[idx])
                        operator = str(self.rng.choice(self.operators, p=probs))
                        candidate = self._generate_candidate(operator, positions, pbest_positions, gbest_position, lb, ub, fes, max_fes)
                        value = float(objective(candidate))
                        fes += 1
                        positions[idx] = candidate
                        velocities[idx] = self.rng.uniform(-vmax, vmax, size=dimension)
                        fitness[idx] = value
                        if value < pbest_fitness[idx]:
                            pbest_positions[idx] = candidate.copy()
                            pbest_fitness[idx] = value
                            particle_stagnation[idx] = 0
                        else:
                            particle_stagnation[idx] = max(0, particle_stagnation[idx] - 1)
                        improvement = max(0.0, old_pbest - value)
                        success = int(value < old_pbest)
                        operator_usage[operator] += 1
                        operator_success[operator] += success
                        self.credit_history.append(OperatorRecord(operator=operator, success=success, improvement=improvement))
                        if value < gbest_fitness:
                            gbest_fitness = value
                            gbest_position = candidate.copy()
                    restart_count += int(selected.size)
                global_stagnation = 0

            if iteration % record_interval == 0:
                convergence_curve.append(gbest_fitness)
                diversity_curve.append(diversity)

        return OptimizationResult(
            algorithm=self.name,
            best_fitness=gbest_fitness,
            best_position=gbest_position.tolist(),
            function_evaluations=fes,
            convergence_curve=convergence_curve,
            metadata={
                "iterations": iteration,
                "restart_count": restart_count,
                "operator_usage": dict(operator_usage),
                "operator_success": dict(operator_success),
                "operator_probabilities_final": dict(zip(self.operators, self._operator_probabilities().tolist(), strict=False)),
                "diversity_final": population_diversity(positions, lb, ub),
                "diversity_curve": diversity_curve,
                "enable_ips": self.enable_ips,
                "enable_arp": self.enable_arp,
                "enable_rca": self.enable_rca,
            },
        )
