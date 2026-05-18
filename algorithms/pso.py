"""标准 PSO 基础实现。

该文件先提供一个稳定、清晰、可复现实验的基础版本。
后续 ARPSO-SRR 和 AP-SRR-PSO 都应该继承或复用这里的核心结构。
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from algorithms.base import OptimizationResult


class PSO:
    """标准粒子群优化算法。"""

    def __init__(
        self,
        population_size: int = 50,
        inertia_weight: float = 0.729,
        cognitive_coefficient: float = 1.49445,
        social_coefficient: float = 1.49445,
        seed: int | None = None,
    ) -> None:
        self.population_size = population_size
        self.inertia_weight = inertia_weight
        self.cognitive_coefficient = cognitive_coefficient
        self.social_coefficient = social_coefficient
        self.rng = np.random.default_rng(seed)

    def optimize(
        self,
        objective: Callable[[np.ndarray], float],
        dimension: int,
        lower_bound: float | np.ndarray,
        upper_bound: float | np.ndarray,
        max_fes: int,
        record_interval: int = 1,
    ) -> OptimizationResult:
        """执行一次优化。

        Args:
            objective: 目标函数，输入一维 numpy 数组，返回 float。
            dimension: 问题维度。
            lower_bound: 下界，可以是标量或长度为 dimension 的数组。
            upper_bound: 上界，可以是标量或长度为 dimension 的数组。
            max_fes: 最大函数评价次数。
            record_interval: 收敛曲线记录间隔，单位为迭代代数。
        """
        lb = np.full(dimension, lower_bound, dtype=float) if np.isscalar(lower_bound) else np.asarray(lower_bound, dtype=float)
        ub = np.full(dimension, upper_bound, dtype=float) if np.isscalar(upper_bound) else np.asarray(upper_bound, dtype=float)

        positions = self.rng.uniform(lb, ub, size=(self.population_size, dimension))
        velocity_limit = 0.2 * (ub - lb)
        velocities = self.rng.uniform(-velocity_limit, velocity_limit, size=(self.population_size, dimension))

        fitness = np.array([objective(x) for x in positions], dtype=float)
        fes = self.population_size

        personal_best_positions = positions.copy()
        personal_best_fitness = fitness.copy()

        best_index = int(np.argmin(fitness))
        global_best_position = positions[best_index].copy()
        global_best_fitness = float(fitness[best_index])

        convergence_curve: list[float] = [global_best_fitness]
        iteration = 0

        while fes < max_fes:
            iteration += 1
            r1 = self.rng.random(size=(self.population_size, dimension))
            r2 = self.rng.random(size=(self.population_size, dimension))

            velocities = (
                self.inertia_weight * velocities
                + self.cognitive_coefficient * r1 * (personal_best_positions - positions)
                + self.social_coefficient * r2 * (global_best_position - positions)
            )
            velocities = np.clip(velocities, -velocity_limit, velocity_limit)

            positions = positions + velocities
            positions = np.clip(positions, lb, ub)

            for i in range(self.population_size):
                if fes >= max_fes:
                    break
                value = float(objective(positions[i]))
                fitness[i] = value
                fes += 1

                if value < personal_best_fitness[i]:
                    personal_best_fitness[i] = value
                    personal_best_positions[i] = positions[i].copy()

                    if value < global_best_fitness:
                        global_best_fitness = value
                        global_best_position = positions[i].copy()

            if iteration % record_interval == 0:
                convergence_curve.append(global_best_fitness)

        return OptimizationResult(
            algorithm="PSO",
            best_fitness=global_best_fitness,
            best_position=global_best_position.tolist(),
            function_evaluations=fes,
            convergence_curve=convergence_curve,
            metadata={
                "population_size": self.population_size,
                "inertia_weight": self.inertia_weight,
                "cognitive_coefficient": self.cognitive_coefficient,
                "social_coefficient": self.social_coefficient,
                "iterations": iteration,
            },
        )
