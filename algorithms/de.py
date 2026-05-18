"""差分进化算法 DE/rand/1/bin。"""

from __future__ import annotations

import numpy as np

from algorithms.base import Objective, OptimizationResult, as_bounds


class DifferentialEvolution:
    """经典 DE/rand/1/bin。"""

    name = "DE"

    def __init__(self, population_size: int = 50, differential_weight: float = 0.5, crossover_rate: float = 0.9, seed: int | None = None) -> None:
        self.population_size = population_size
        self.differential_weight = differential_weight
        self.crossover_rate = crossover_rate
        self.rng = np.random.default_rng(seed)

    def optimize(self, objective: Objective, dimension: int, lower_bound: float | np.ndarray, upper_bound: float | np.ndarray, max_fes: int, record_interval: int = 1) -> OptimizationResult:
        lb, ub = as_bounds(dimension, lower_bound, upper_bound)
        population = self.rng.uniform(lb, ub, size=(self.population_size, dimension))
        fitness = np.array([objective(x) for x in population], dtype=float)
        fes = self.population_size
        best_idx = int(np.argmin(fitness))
        best_position = population[best_idx].copy()
        best_fitness = float(fitness[best_idx])
        convergence_curve = [best_fitness]
        generation = 0

        while fes < max_fes:
            generation += 1
            for i in range(self.population_size):
                if fes >= max_fes:
                    break
                candidates = [idx for idx in range(self.population_size) if idx != i]
                r1, r2, r3 = self.rng.choice(candidates, size=3, replace=False)
                mutant = population[r1] + self.differential_weight * (population[r2] - population[r3])
                mutant = np.clip(mutant, lb, ub)
                cross_mask = self.rng.random(dimension) < self.crossover_rate
                cross_mask[self.rng.integers(0, dimension)] = True
                trial = np.where(cross_mask, mutant, population[i])
                trial_fitness = float(objective(trial))
                fes += 1
                if trial_fitness < fitness[i]:
                    population[i] = trial
                    fitness[i] = trial_fitness
                    if trial_fitness < best_fitness:
                        best_fitness = trial_fitness
                        best_position = trial.copy()
            if generation % record_interval == 0:
                convergence_curve.append(best_fitness)

        return OptimizationResult(
            algorithm=self.name,
            best_fitness=best_fitness,
            best_position=best_position.tolist(),
            function_evaluations=fes,
            convergence_curve=convergence_curve,
            metadata={"generations": generation, "restart_count": 0, "differential_weight": self.differential_weight, "crossover_rate": self.crossover_rate},
        )
