"""常用 PSO 变体：PSO-RS 与 PSO-AW。

这些实现用于论文对比和 smoke experiment，不是最终创新点。
"""

from __future__ import annotations

from algorithms.base import Objective, OptimizationResult, as_bounds, population_diversity

import numpy as np


class PSORS:
    """带随机重启的 PSO。

    当全局最优长时间没有改善时，随机重启一部分非精英粒子。
    """

    name = "PSO-RS"

    def __init__(
        self,
        population_size: int = 50,
        inertia_weight: float = 0.729,
        cognitive_coefficient: float = 1.49445,
        social_coefficient: float = 1.49445,
        stagnation_threshold: int = 30,
        restart_ratio: float = 0.2,
        elite_ratio: float = 0.1,
        seed: int | None = None,
        velocity_clamp_ratio: float = 0.2,
    ) -> None:
        self.population_size = population_size
        self.inertia_weight = inertia_weight
        self.cognitive_coefficient = cognitive_coefficient
        self.social_coefficient = social_coefficient
        self.stagnation_threshold = stagnation_threshold
        self.restart_ratio = restart_ratio
        self.elite_ratio = elite_ratio
        self.velocity_clamp_ratio = velocity_clamp_ratio
        self.rng = np.random.default_rng(seed)

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
        best_idx = int(np.argmin(fitness))
        gbest_position = positions[best_idx].copy()
        gbest_fitness = float(fitness[best_idx])
        convergence_curve = [gbest_fitness]
        no_improve = 0
        restart_count = 0
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
                    if value < gbest_fitness:
                        gbest_fitness = value
                        gbest_position = positions[i].copy()

            no_improve = 0 if gbest_fitness < old_best else no_improve + 1
            if no_improve >= self.stagnation_threshold and fes < max_fes:
                elite_count = max(1, int(self.elite_ratio * self.population_size))
                restart_count_i = max(1, int(self.restart_ratio * self.population_size))
                ranked = np.argsort(pbest_fitness)
                candidates = ranked[elite_count:]
                if candidates.size > 0:
                    selected = self.rng.choice(candidates, size=min(restart_count_i, candidates.size), replace=False)
                    positions[selected] = self.rng.uniform(lb, ub, size=(selected.size, dimension))
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
                        if value < gbest_fitness:
                            gbest_fitness = value
                            gbest_position = positions[idx].copy()
                    restart_count += int(selected.size)
                no_improve = 0

            if iteration % record_interval == 0:
                convergence_curve.append(gbest_fitness)

        return OptimizationResult(
            algorithm=self.name,
            best_fitness=gbest_fitness,
            best_position=gbest_position.tolist(),
            function_evaluations=fes,
            convergence_curve=convergence_curve,
            metadata={"iterations": iteration, "restart_count": restart_count},
        )


class PSOAW:
    """线性递减惯性权重 PSO。"""

    name = "PSO-AW"

    def __init__(
        self,
        population_size: int = 50,
        w_max: float = 0.9,
        w_min: float = 0.4,
        cognitive_coefficient: float = 2.0,
        social_coefficient: float = 2.0,
        seed: int | None = None,
        velocity_clamp_ratio: float = 0.2,
    ) -> None:
        self.population_size = population_size
        self.w_max = w_max
        self.w_min = w_min
        self.cognitive_coefficient = cognitive_coefficient
        self.social_coefficient = social_coefficient
        self.velocity_clamp_ratio = velocity_clamp_ratio
        self.rng = np.random.default_rng(seed)

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
        best_idx = int(np.argmin(fitness))
        gbest_position = positions[best_idx].copy()
        gbest_fitness = float(fitness[best_idx])
        convergence_curve = [gbest_fitness]
        iteration = 0
        max_iterations_est = max(1, int(np.ceil(max_fes / self.population_size)))

        while fes < max_fes:
            iteration += 1
            progress = min(1.0, iteration / max_iterations_est)
            w = self.w_max - (self.w_max - self.w_min) * progress
            r1 = self.rng.random((self.population_size, dimension))
            r2 = self.rng.random((self.population_size, dimension))
            velocities = (
                w * velocities
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
                    if value < gbest_fitness:
                        gbest_fitness = value
                        gbest_position = positions[i].copy()
            if iteration % record_interval == 0:
                convergence_curve.append(gbest_fitness)

        return OptimizationResult(
            algorithm=self.name,
            best_fitness=gbest_fitness,
            best_position=gbest_position.tolist(),
            function_evaluations=fes,
            convergence_curve=convergence_curve,
            metadata={
                "iterations": iteration,
                "restart_count": 0,
                "diversity_final": population_diversity(positions, lb, ub),
            },
        )
