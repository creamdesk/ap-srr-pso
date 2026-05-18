"""标准 PSO 基础实现。"""

from __future__ import annotations

import numpy as np

from algorithms.base import Objective, OptimizationResult, as_bounds


class PSO:
    """标准粒子群优化算法。"""

    name = "PSO"

    def __init__(
        self,
        population_size: int = 50,
        inertia_weight: float = 0.729,
        cognitive_coefficient: float = 1.49445,
        social_coefficient: float = 1.49445,
        seed: int | None = None,
        velocity_clamp_ratio: float = 0.2,
    ) -> None:
        self.population_size = population_size
        self.inertia_weight = inertia_weight
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
        best_index = int(np.argmin(fitness))
        gbest_position = positions[best_index].copy()
        gbest_fitness = float(fitness[best_index])
        convergence_curve = [gbest_fitness]
        iteration = 0

        while fes < max_fes:
            iteration += 1
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

            if iteration % record_interval == 0:
                convergence_curve.append(gbest_fitness)

        return OptimizationResult(
            algorithm=self.name,
            best_fitness=gbest_fitness,
            best_position=gbest_position.tolist(),
            function_evaluations=fes,
            convergence_curve=convergence_curve,
            metadata={"iterations": iteration, "population_size": self.population_size, "restart_count": 0},
        )
