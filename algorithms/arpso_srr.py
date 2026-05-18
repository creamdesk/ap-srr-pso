"""ARPSO-SRR：自适应重启与搜索资源重分配 PSO。

该版本用于承接旧 EI/会议版主方法，作为 SCI 升级版 AP-SRR-PSO 的直接基线。
"""

from __future__ import annotations

import numpy as np

from algorithms.base import Objective, OptimizationResult, as_bounds, population_diversity


class ARPSOSRR:
    """Adaptive Restart PSO based on Search Resource Reallocation."""

    name = "ARPSO-SRR"

    def __init__(
        self,
        population_size: int = 50,
        inertia_weight: float = 0.729,
        cognitive_coefficient: float = 1.49445,
        social_coefficient: float = 1.49445,
        stagnation_threshold: int = 25,
        diversity_threshold: float = 0.08,
        rho_min: float = 0.05,
        rho_max: float = 0.35,
        elite_ratio: float = 0.1,
        local_ratio: float = 0.5,
        local_sigma: float = 0.1,
        seed: int | None = None,
        velocity_clamp_ratio: float = 0.2,
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
        self.local_ratio = local_ratio
        self.local_sigma = local_sigma
        self.velocity_clamp_ratio = velocity_clamp_ratio
        self.rng = np.random.default_rng(seed)

    def _restart_intensity(self, global_stagnation: int, diversity: float) -> float:
        stagnation_score = min(1.0, global_stagnation / max(1, self.stagnation_threshold))
        diversity_loss = max(0.0, (self.diversity_threshold - diversity) / max(self.diversity_threshold, 1e-12))
        score = 0.6 * stagnation_score + 0.4 * diversity_loss
        return float(self.rho_min + (self.rho_max - self.rho_min) * np.clip(score, 0.0, 1.0))

    def optimize(
        self,
        objective: Objective,
        dimension: int,
        lower_bound: float | np.ndarray,
        upper_bound: float | np.ndarray,
        max_fes: int,
        record_interval: int = 1,
    ) -> OptimizationResult:
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
                candidates = [i for i in np.argsort(-particle_stagnation) if i not in elite_indices]
                selected = np.array(candidates[:restart_n], dtype=int)

                if selected.size > 0:
                    local_n = int(round(self.local_ratio * selected.size))
                    local_indices = selected[:local_n]
                    global_indices = selected[local_n:]

                    if local_indices.size > 0:
                        sigma = self.local_sigma * (ub - lb) * max(0.05, 1.0 - fes / max_fes)
                        positions[local_indices] = np.clip(
                            gbest_position + self.rng.normal(0.0, sigma, size=(local_indices.size, dimension)), lb, ub
                        )
                    if global_indices.size > 0:
                        positions[global_indices] = self.rng.uniform(lb, ub, size=(global_indices.size, dimension))

                    velocities[selected] = self.rng.uniform(-vmax, vmax, size=(selected.size, dimension))
                    for idx in selected:
                        if fes >= max_fes:
                            break
                        value = float(objective(positions[idx]))
                        fitness[idx] = value
                        fes += 1
                        if value < pbest_fitness[idx]:
                            pbest_positions[idx] = positions[idx].copy()
                            pbest_fitness[idx] = value
                            particle_stagnation[idx] = 0
                        else:
                            particle_stagnation[idx] = max(0, particle_stagnation[idx] - 1)
                        if value < gbest_fitness:
                            gbest_fitness = value
                            gbest_position = positions[idx].copy()
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
                "diversity_final": population_diversity(positions, lb, ub),
                "diversity_curve": diversity_curve,
                "stagnation_threshold": self.stagnation_threshold,
                "rho_min": self.rho_min,
                "rho_max": self.rho_max,
            },
        )
