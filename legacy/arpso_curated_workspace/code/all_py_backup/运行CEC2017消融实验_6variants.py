# -*- coding: utf-8 -*-
"""
CEC2017 消融实验：6 个重启/资源重分配变体
================================================
建议保存为：code/运行CEC2017消融实验_6variants.py
运行方式：python code/运行CEC2017消融实验_6variants.py

6 个算法：
1. PSO-RS        : 简单随机重启
2. ARPSO-Fixed  : 固定重启比例 + 混合重启
3. ARPSO-Global : 自适应重启比例 + 仅全局随机重启
4. ARPSO-Local  : 自适应重启比例 + 仅局部扰动重启
5. ARPSO-SRR    : 自适应重启比例 + 全局/局部混合重启，主方法
6. ARPSO-EIS    : 自适应混合重启 + 低效粒子识别，消融/对比变体

输出目录：results/cec2017_ablation6
主要输出文件：
- ablation6_raw_results.csv
- ablation6_summary_results.csv
- ablation6_average_rank.csv
- ablation6_group_average_rank.csv
- ablation6_runtime_summary.csv
- ablation6_restart_summary.csv
- ablation6_wilcoxon_summary.csv
- ablation6_friedman.csv
- ablation6_mean_curves.csv
- ablation6_restart_details.csv

注意：
- 默认跑 CEC2017 F1, F3-F30，共 29 个函数。
- 默认 30 维，种群 50，最大 FEs = 300000，独立运行 30 次。
- 如果想先快速测试，把 SMOKE_TEST = True。
"""

import os
import csv
import math
import time
import traceback
import importlib
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
from scipy.stats import rankdata, friedmanchisquare, wilcoxon


# ============================================================
# 0. 全局配置
# ============================================================
SMOKE_TEST = False          # True: 快速测试；False: 正式实验
N_WORKERS = 8               # 你的机器之前是 4 个 PID 并行，这里默认 4
BASE_SEED = 20260429

DIM = 30
POP_SIZE = 50
MAX_FES = 10000 * DIM
N_RUNS = 30

FUNCTION_IDS = [1] + list(range(3, 31))
ALGORITHMS = [
    "PSO-RS",
    "ARPSO-Fixed",
    "ARPSO-Global",
    "ARPSO-Local",
    "ARPSO-SRR",
    "ARPSO-EIS",
]
BASE_ALGORITHM = "ARPSO-SRR"

RESULT_DIR = Path("results") / "cec2017_ablation6"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# 曲线记录间隔。值越小，曲线越细，但文件越大。
CURVE_FE_INTERVAL = 5000

# PSO 基础参数。所有消融版本保持一致，只改变重启机制。
W_MAX = 0.9
W_MIN = 0.4
C1 = 2.0
C2 = 2.0
VEL_CLAMP_RATIO = 0.2

# 重启触发与强度参数
STAGNATION_THRESHOLD = 50
DIVERSITY_THRESHOLD = 0.05
RHO_MIN = 0.08
RHO_MAX = 0.40
RHO_FIXED = 0.20

# 局部扰动范围
SIGMA_MIN = 0.002
SIGMA_MAX = 0.060

# 混合重启中，全局随机重启比例
GLOBAL_PART_RATIO = 0.50

if SMOKE_TEST:
    DIM = 10
    POP_SIZE = 20
    MAX_FES = 2000
    N_RUNS = 2
    FUNCTION_IDS = [1, 3, 4]
    N_WORKERS = 8
    CURVE_FE_INTERVAL = 200
    RESULT_DIR = Path("results") / "cec2017_ablation6_smoke"
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. CEC2017 函数加载
# ============================================================
def load_cec2017_function(fid: int, dim: int):
    """兼容 opfunu 不同版本的 CEC2017 函数加载方式。"""
    try:
        cec2017 = importlib.import_module("opfunu.cec_based.cec2017")
    except Exception as e:
        raise RuntimeError(
            "无法导入 opfunu.cec_based.cec2017。请先安装：pip install opfunu"
        ) from e

    cls = None
    candidate_names = [f"F{fid}2017", f"F{fid}"]
    for name in candidate_names:
        if hasattr(cec2017, name):
            cls = getattr(cec2017, name)
            break
    if cls is None:
        raise RuntimeError(f"当前 opfunu 版本中找不到 CEC2017 F{fid} 类。")

    try:
        problem = cls(ndim=dim)
    except TypeError:
        problem = cls(dim)

    lb = getattr(problem, "lb", None)
    ub = getattr(problem, "ub", None)

    if lb is None:
        lb = getattr(problem, "lower", None)
    if ub is None:
        ub = getattr(problem, "upper", None)

    if lb is None or ub is None:
        lb = -100.0 * np.ones(dim)
        ub = 100.0 * np.ones(dim)
    else:
        lb = np.asarray(lb, dtype=float)
        ub = np.asarray(ub, dtype=float)
        if lb.size == 1:
            lb = np.full(dim, float(lb))
        if ub.size == 1:
            ub = np.full(dim, float(ub))

    # CEC2017 单目标函数常用 bias 为 100 * fid。
    # opfunu 多数版本会提供 f_global；如果没有，则用 100 * fid。
    f_opt = getattr(problem, "f_global", None)
    if f_opt is None:
        f_opt = getattr(problem, "f_bias", None)
    if f_opt is None:
        f_opt = 100.0 * fid
    f_opt = float(f_opt)

    return problem, lb, ub, f_opt


def evaluate(problem, x: np.ndarray) -> float:
    """单点评价。"""
    val = problem.evaluate(x)
    return float(val)


# ============================================================
# 2. 工具函数
# ============================================================
def normalized_diversity(X: np.ndarray, lb: np.ndarray, ub: np.ndarray) -> float:
    """归一化后的种群多样性，便于不同维度和边界下比较。"""
    span = np.maximum(ub - lb, 1e-12)
    Xn = (X - lb) / span
    center = np.mean(Xn, axis=0)
    div = np.mean(np.linalg.norm(Xn - center, axis=1)) / math.sqrt(X.shape[1])
    return float(div)


def linear_inertia(fes: int, max_fes: int) -> float:
    progress = min(1.0, fes / max_fes)
    return W_MAX - (W_MAX - W_MIN) * progress


def local_sigma(fes: int, max_fes: int) -> float:
    progress = min(1.0, fes / max_fes)
    return SIGMA_MAX - (SIGMA_MAX - SIGMA_MIN) * progress


def restart_demand(stagnation: int, diversity: float) -> float:
    q_stag = min(1.0, stagnation / max(1, 3 * STAGNATION_THRESHOLD))
    q_div = max(0.0, (DIVERSITY_THRESHOLD - diversity) / max(DIVERSITY_THRESHOLD, 1e-12))
    return float(np.clip(max(q_stag, q_div), 0.0, 1.0))


def calc_restart_ratio(algorithm: str, stagnation: int, diversity: float) -> float:
    if algorithm == "ARPSO-Fixed":
        return RHO_FIXED
    q = restart_demand(stagnation, diversity)
    return RHO_MIN + (RHO_MAX - RHO_MIN) * q


def pairwise_nearest_distance(X: np.ndarray, lb: np.ndarray, ub: np.ndarray) -> np.ndarray:
    """每个粒子到最近邻的归一化距离。N=50 时直接矩阵计算足够快。"""
    span = np.maximum(ub - lb, 1e-12)
    Xn = (X - lb) / span
    diff = Xn[:, None, :] - Xn[None, :, :]
    dist = np.sqrt(np.sum(diff * diff, axis=2))
    np.fill_diagonal(dist, np.inf)
    nearest = np.min(dist, axis=1)
    return nearest


def minmax_norm(a: np.ndarray, invert: bool = False) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    amin = np.min(a)
    amax = np.max(a)
    if amax - amin < 1e-12:
        out = np.zeros_like(a)
    else:
        out = (a - amin) / (amax - amin)
    if invert:
        out = 1.0 - out
    return out


def select_particles(
    algorithm: str,
    X: np.ndarray,
    fit: np.ndarray,
    pbest_update_count: np.ndarray,
    no_improve_count: np.ndarray,
    lb: np.ndarray,
    ub: np.ndarray,
    gbest_index: int,
    m: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """选择需要重启的粒子。避免直接重启当前全局最优粒子。"""
    n = X.shape[0]
    m = int(min(max(1, m), n - 1))
    candidates = np.array([i for i in range(n) if i != gbest_index], dtype=int)

    if algorithm == "PSO-RS":
        # 简单随机重启：不做精细筛选。
        return rng.choice(candidates, size=m, replace=False)

    if algorithm == "ARPSO-EIS":
        # EIS: inefficient particle score
        # 1) fitness disadvantage: 越差越应该重启
        fitness_score = minmax_norm(fit, invert=False)

        # 2) crowding score: 最近邻距离越小，越拥挤，越应该重启
        nearest = pairwise_nearest_distance(X, lb, ub)
        crowding_score = minmax_norm(nearest, invert=True)

        # 3) contribution score: 历史 pbest 改进越少，越应该重启
        contribution_score = minmax_norm(pbest_update_count, invert=True)

        # 4) stagnation score: 个体长时间不改进，越应该重启
        stagnation_score = minmax_norm(no_improve_count, invert=False)

        score = (
            0.40 * fitness_score
            + 0.25 * crowding_score
            + 0.20 * contribution_score
            + 0.15 * stagnation_score
        )
        score[gbest_index] = -np.inf
        return np.argsort(-score)[:m]

    # ARPSO-SRR / Fixed / Global / Local：采用较轻量的资源重分配选择。
    # 重点不是复杂打分，而是重启强度和重启方式。
    fitness_score = minmax_norm(fit, invert=False)
    stagnation_score = minmax_norm(no_improve_count, invert=False)
    score = 0.65 * fitness_score + 0.35 * stagnation_score
    score[gbest_index] = -np.inf
    return np.argsort(-score)[:m]


def regenerate_positions(
    algorithm: str,
    m: int,
    gbest: np.ndarray,
    lb: np.ndarray,
    ub: np.ndarray,
    fes: int,
    max_fes: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """根据不同消融版本生成重启后的新位置。"""
    dim = lb.size
    span = ub - lb

    def global_restart(k: int) -> np.ndarray:
        return lb + span * rng.random((k, dim))

    def local_restart(k: int) -> np.ndarray:
        sigma = local_sigma(fes, max_fes)
        # 正态扰动更适合局部扰动；随后做边界截断。
        Z = rng.normal(loc=0.0, scale=1.0, size=(k, dim))
        Y = gbest + sigma * span * Z
        return np.clip(Y, lb, ub)

    if algorithm in ["PSO-RS", "ARPSO-Global"]:
        return global_restart(m)

    if algorithm == "ARPSO-Local":
        return local_restart(m)

    # ARPSO-Fixed / ARPSO-SRR / ARPSO-EIS：混合重启
    k_global = int(round(m * GLOBAL_PART_RATIO))
    k_global = min(max(1, k_global), m)
    k_local = m - k_global
    parts = [global_restart(k_global)]
    if k_local > 0:
        parts.append(local_restart(k_local))
    Y = np.vstack(parts)
    rng.shuffle(Y, axis=0)
    return Y


# ============================================================
# 3. 单次实验核心
# ============================================================
@dataclass
class RunResult:
    raw: dict
    curves: list
    restarts: list


def run_single(fid: int, algorithm: str, run_id: int, seed: int) -> RunResult:
    t0 = time.time()
    rng = np.random.default_rng(seed)
    problem, lb, ub, f_opt = load_cec2017_function(fid, DIM)
    dim = DIM
    n = POP_SIZE

    span = ub - lb
    vmax = VEL_CLAMP_RATIO * span

    # 初始化
    X = lb + span * rng.random((n, dim))
    V = rng.uniform(-vmax, vmax, size=(n, dim))

    fit = np.empty(n, dtype=float)
    for i in range(n):
        fit[i] = evaluate(problem, X[i])
    fes = n

    P = X.copy()
    pbest_fit = fit.copy()
    pbest_update_count = np.zeros(n, dtype=int)
    no_improve_count = np.zeros(n, dtype=int)

    gbest_index = int(np.argmin(pbest_fit))
    G = P[gbest_index].copy()
    gfit = float(pbest_fit[gbest_index])

    stagnation = 0
    restart_count = 0
    restarted_particles_total = 0

    curves = []
    restarts = []
    next_curve_fe = CURVE_FE_INTERVAL

    while fes < MAX_FES:
        old_gfit = gfit

        # 标准 PSO 更新
        w = linear_inertia(fes, MAX_FES)
        r1 = rng.random((n, dim))
        r2 = rng.random((n, dim))
        V = w * V + C1 * r1 * (P - X) + C2 * r2 * (G - X)
        V = np.clip(V, -vmax, vmax)
        X = X + V
        X = np.clip(X, lb, ub)

        # 正常评价。若剩余 FEs 不足以评价整个种群，则只评价部分粒子。
        remaining = MAX_FES - fes
        eval_n = min(n, remaining)
        for i in range(eval_n):
            fit[i] = evaluate(problem, X[i])
        fes += eval_n

        # 更新 pbest / gbest
        improved = fit[:eval_n] < pbest_fit[:eval_n]
        if np.any(improved):
            idxs = np.where(improved)[0]
            P[idxs] = X[idxs]
            pbest_fit[idxs] = fit[idxs]
            pbest_update_count[idxs] += 1
            no_improve_count[idxs] = 0
        not_improved = np.ones(n, dtype=bool)
        not_improved[:eval_n] = ~improved
        no_improve_count[not_improved] += 1

        gbest_index = int(np.argmin(pbest_fit))
        if pbest_fit[gbest_index] < gfit:
            gfit = float(pbest_fit[gbest_index])
            G = P[gbest_index].copy()

        if gfit < old_gfit - 1e-12:
            stagnation = 0
        else:
            stagnation += 1

        div = normalized_diversity(X, lb, ub)

        # 曲线记录
        while fes >= next_curve_fe:
            curves.append({
                "Function": f"F{fid}",
                "FunctionID": fid,
                "Algorithm": algorithm,
                "Run": run_id,
                "FE": next_curve_fe,
                "BestFitness": gfit,
                "BestError": max(0.0, gfit - f_opt),
            })
            next_curve_fe += CURVE_FE_INTERVAL

        if fes >= MAX_FES:
            break

        # 重启触发
        restart_triggered = (stagnation >= STAGNATION_THRESHOLD) or (div <= DIVERSITY_THRESHOLD)
        if restart_triggered:
            rho = calc_restart_ratio(algorithm, stagnation, div)
            m = int(math.ceil(rho * n))
            m = min(max(1, m), n - 1, MAX_FES - fes)
            if m <= 0:
                break

            current_gbest_index = int(np.argmin(pbest_fit))
            selected = select_particles(
                algorithm=algorithm,
                X=X,
                fit=fit,
                pbest_update_count=pbest_update_count,
                no_improve_count=no_improve_count,
                lb=lb,
                ub=ub,
                gbest_index=current_gbest_index,
                m=m,
                rng=rng,
            )

            new_X = regenerate_positions(
                algorithm=algorithm,
                m=m,
                gbest=G,
                lb=lb,
                ub=ub,
                fes=fes,
                max_fes=MAX_FES,
                rng=rng,
            )

            # 重启后立即评价，并重置这些粒子的 pbest。
            new_fit = np.empty(m, dtype=float)
            for j in range(m):
                new_fit[j] = evaluate(problem, new_X[j])
            fes += m

            X[selected] = new_X
            V[selected] = rng.uniform(-vmax, vmax, size=(m, dim))
            fit[selected] = new_fit
            P[selected] = new_X
            pbest_fit[selected] = new_fit
            no_improve_count[selected] = 0
            pbest_update_count[selected] = 0

            gbest_index = int(np.argmin(pbest_fit))
            if pbest_fit[gbest_index] < gfit:
                gfit = float(pbest_fit[gbest_index])
                G = P[gbest_index].copy()

            restart_count += 1
            restarted_particles_total += m
            restarts.append({
                "Function": f"F{fid}",
                "FunctionID": fid,
                "Algorithm": algorithm,
                "Run": run_id,
                "FE": fes,
                "RestartIndex": restart_count,
                "RestartedParticles": m,
                "RestartRatio": rho,
                "Diversity": div,
                "Stagnation": stagnation,
                "BestFitnessAfterRestart": gfit,
                "BestErrorAfterRestart": max(0.0, gfit - f_opt),
            })

            stagnation = 0

    runtime = time.time() - t0
    best_error = max(0.0, gfit - f_opt)
    raw = {
        "Function": f"F{fid}",
        "FunctionID": fid,
        "Algorithm": algorithm,
        "Run": run_id,
        "Seed": seed,
        "BestFitness": gfit,
        "Fopt": f_opt,
        "BestError": best_error,
        "RestartCount": restart_count,
        "RestartedParticlesTotal": restarted_particles_total,
        "Runtime": runtime,
        "FEs": fes,
    }
    return RunResult(raw=raw, curves=curves, restarts=restarts)


# ============================================================
# 4. 统计汇总
# ============================================================
def build_summaries(raw_df: pd.DataFrame, curve_df: pd.DataFrame, restart_df: pd.DataFrame):
    # 1) 函数级 summary
    summary = (
        raw_df.groupby(["FunctionID", "Function", "Algorithm"])
        .agg(
            MeanError=("BestError", "mean"),
            StdError=("BestError", "std"),
            MedianError=("BestError", "median"),
            BestError=("BestError", "min"),
            WorstError=("BestError", "max"),
            AvgRestart=("RestartCount", "mean"),
            AvgRuntime=("Runtime", "mean"),
        )
        .reset_index()
        .sort_values(["FunctionID", "Algorithm"])
    )

    # 2) 每个函数上按 MeanError 排名
    rank_records = []
    for fid, g in summary.groupby("FunctionID"):
        ranks = rankdata(g["MeanError"].values, method="average")
        for (_, row), r in zip(g.iterrows(), ranks):
            rank_records.append({
                "FunctionID": int(fid),
                "Function": row["Function"],
                "Algorithm": row["Algorithm"],
                "MeanError": row["MeanError"],
                "Rank": float(r),
            })
    rank_detail = pd.DataFrame(rank_records)
    avg_rank = (
        rank_detail.groupby("Algorithm")
        .agg(AverageRank=("Rank", "mean"))
        .reset_index()
        .sort_values("AverageRank")
    )

    # 3) 函数组平均排名
    def group_name(fid: int) -> str:
        if fid in [1, 3]:
            return "Unimodal"
        if 4 <= fid <= 10:
            return "Simple multimodal"
        if 11 <= fid <= 20:
            return "Hybrid"
        if 21 <= fid <= 30:
            return "Composition"
        return "Other"

    rank_detail["Group"] = rank_detail["FunctionID"].apply(group_name)
    group_rank = (
        rank_detail.groupby(["Group", "Algorithm"])
        .agg(GroupAverageRank=("Rank", "mean"))
        .reset_index()
        .sort_values(["Group", "GroupAverageRank"])
    )

    # 4) runtime summary
    runtime_summary = (
        raw_df.groupby("Algorithm")
        .agg(
            AvgRuntime=("Runtime", "mean"),
            StdRuntime=("Runtime", "std"),
            AvgFEs=("FEs", "mean"),
        )
        .reset_index()
    )
    base_rt = float(runtime_summary.loc[runtime_summary["Algorithm"] == BASE_ALGORITHM, "AvgRuntime"].iloc[0])
    runtime_summary["RelativeRuntimeToSRR"] = runtime_summary["AvgRuntime"] / base_rt
    runtime_summary = runtime_summary.sort_values("AvgRuntime")

    # 5) restart summary
    restart_summary = (
        raw_df.groupby("Algorithm")
        .agg(
            AvgRestartCount=("RestartCount", "mean"),
            StdRestartCount=("RestartCount", "std"),
            AvgRestartedParticles=("RestartedParticlesTotal", "mean"),
        )
        .reset_index()
        .sort_values("AvgRestartCount")
    )

    # 6) mean curves
    if curve_df.empty:
        mean_curves = pd.DataFrame()
    else:
        mean_curves = (
            curve_df.groupby(["FunctionID", "Function", "Algorithm", "FE"])
            .agg(MeanBestError=("BestError", "mean"), StdBestError=("BestError", "std"))
            .reset_index()
            .sort_values(["FunctionID", "Algorithm", "FE"])
        )

    # 7) Friedman test: 使用每个函数上的算法排名
    pivot_rank = rank_detail.pivot(index="FunctionID", columns="Algorithm", values="Rank")
    friedman_inputs = [pivot_rank[alg].values for alg in ALGORITHMS if alg in pivot_rank.columns]
    stat, pval = friedmanchisquare(*friedman_inputs)
    friedman_df = pd.DataFrame([{
        "Test": "Friedman",
        "Statistic": float(stat),
        "PValue": float(pval),
        "NumBlocks": int(pivot_rank.shape[0]),
        "NumAlgorithms": int(len(friedman_inputs)),
    }])

    # 8) Wilcoxon: ARPSO-SRR vs 其他算法，按每个函数 30 次 paired runs 比较
    wilcoxon_records = []
    per_func_records = []
    for alg in ALGORITHMS:
        if alg == BASE_ALGORITHM:
            continue
        win = nsd = loss = 0
        for fid in sorted(raw_df["FunctionID"].unique()):
            base_vals = raw_df[(raw_df["FunctionID"] == fid) & (raw_df["Algorithm"] == BASE_ALGORITHM)].sort_values("Run")["BestError"].values
            comp_vals = raw_df[(raw_df["FunctionID"] == fid) & (raw_df["Algorithm"] == alg)].sort_values("Run")["BestError"].values
            if len(base_vals) == 0 or len(comp_vals) == 0:
                continue
            n = min(len(base_vals), len(comp_vals))
            base_vals = base_vals[:n]
            comp_vals = comp_vals[:n]
            try:
                # 如果全相等，scipy 可能报错，直接视为 NSD。
                if np.allclose(base_vals, comp_vals):
                    p = 1.0
                else:
                    _, p = wilcoxon(base_vals, comp_vals, alternative="two-sided", zero_method="wilcox")
            except Exception:
                p = 1.0

            base_mean = float(np.mean(base_vals))
            comp_mean = float(np.mean(comp_vals))
            if p < 0.05 and base_mean < comp_mean:
                result = "Win"
                win += 1
            elif p < 0.05 and base_mean > comp_mean:
                result = "Loss"
                loss += 1
            else:
                result = "NSD"
                nsd += 1
            per_func_records.append({
                "FunctionID": int(fid),
                "Function": f"F{fid}",
                "BaseAlgorithm": BASE_ALGORITHM,
                "ComparedAlgorithm": alg,
                "BaseMeanError": base_mean,
                "ComparedMeanError": comp_mean,
                "PValue": float(p),
                "Result": result,
            })
        wilcoxon_records.append({
            "BaseAlgorithm": BASE_ALGORITHM,
            "ComparedAlgorithm": alg,
            "Win": win,
            "NSD": nsd,
            "Loss": loss,
        })
    wilcoxon_summary = pd.DataFrame(wilcoxon_records)
    wilcoxon_detail = pd.DataFrame(per_func_records)

    return {
        "summary": summary,
        "rank_detail": rank_detail,
        "average_rank": avg_rank,
        "group_average_rank": group_rank,
        "runtime_summary": runtime_summary,
        "restart_summary": restart_summary,
        "mean_curves": mean_curves,
        "friedman": friedman_df,
        "wilcoxon_summary": wilcoxon_summary,
        "wilcoxon_detail": wilcoxon_detail,
    }


# ============================================================
# 5. 主程序
# ============================================================
def main():
    print("=" * 100)
    print("CEC2017 ablation experiment: 6 variants")
    print(f"Functions    : {FUNCTION_IDS}")
    print(f"Algorithms   : {ALGORITHMS}")
    print(f"Dimension    : {DIM}")
    print(f"Population   : {POP_SIZE}")
    print(f"Max FEs      : {MAX_FES}")
    print(f"Runs         : {N_RUNS}")
    print(f"Workers      : {N_WORKERS}")
    print(f"Result dir   : {RESULT_DIR}")
    print("=" * 100)

    tasks = []
    task_id = 0
    for fid in FUNCTION_IDS:
        for alg_idx, alg in enumerate(ALGORITHMS):
            for run in range(1, N_RUNS + 1):
                task_id += 1
                seed = BASE_SEED + fid * 100000 + alg_idx * 1000 + run
                tasks.append((task_id, fid, alg, run, seed))

    raw_path = RESULT_DIR / "ablation6_raw_results.csv"
    curves_path = RESULT_DIR / "ablation6_curve_records.csv"
    restart_path = RESULT_DIR / "ablation6_restart_details.csv"
    error_path = RESULT_DIR / "ablation6_errors.log"

    raw_rows = []
    curve_rows = []
    restart_rows = []

    start_time = time.time()
    finished = 0
    total = len(tasks)

    # 如果旧文件存在，建议手动备份。这里直接覆盖，避免混入旧结果。
    for p in [raw_path, curves_path, restart_path, error_path]:
        if p.exists():
            p.unlink()

    with ProcessPoolExecutor(max_workers=N_WORKERS) as ex:
        future_map = {
            ex.submit(run_single, fid, alg, run, seed): (tid, fid, alg, run, seed)
            for tid, fid, alg, run, seed in tasks
        }

        for fut in as_completed(future_map):
            tid, fid, alg, run, seed = future_map[fut]
            try:
                result = fut.result()
                raw_rows.append(result.raw)
                curve_rows.extend(result.curves)
                restart_rows.extend(result.restarts)
            except Exception as e:
                msg = f"TaskID={tid}, F{fid}, {alg}, Run={run}, Seed={seed}\n{repr(e)}\n{traceback.format_exc()}\n"
                print("[ERROR]", msg)
                with open(error_path, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")

            finished += 1
            elapsed = time.time() - start_time
            avg_time = elapsed / max(1, finished)
            eta = avg_time * (total - finished)
            percent = 100.0 * finished / total

            print(
                f"[{finished:04d}/{total}] {percent:6.2f}% | "
                f"TaskID={tid:04d} | F{fid:<2d} | {alg:<12s} | Run={run:02d} | "
                f"Elapsed={elapsed/3600:6.2f}h | ETA={eta/3600:6.2f}h"
            )

            # 定期 checkpoint，防止中途崩掉白跑。
            if finished % 50 == 0 or finished == total:
                if raw_rows:
                    pd.DataFrame(raw_rows).to_csv(raw_path, index=False, encoding="utf-8-sig")
                if curve_rows:
                    pd.DataFrame(curve_rows).to_csv(curves_path, index=False, encoding="utf-8-sig")
                if restart_rows:
                    pd.DataFrame(restart_rows).to_csv(restart_path, index=False, encoding="utf-8-sig")

    raw_df = pd.DataFrame(raw_rows)
    curve_df = pd.DataFrame(curve_rows)
    restart_df = pd.DataFrame(restart_rows)

    print("=" * 100)
    print("Building summary tables...")
    print(f"Raw rows       : {len(raw_df)}")
    print(f"Curve records  : {len(curve_df)}")
    print(f"Restart details: {len(restart_df)}")
    print("=" * 100)

    summaries = build_summaries(raw_df, curve_df, restart_df)

    raw_df.to_csv(RESULT_DIR / "ablation6_raw_results.csv", index=False, encoding="utf-8-sig")
    curve_df.to_csv(RESULT_DIR / "ablation6_curve_records.csv", index=False, encoding="utf-8-sig")
    restart_df.to_csv(RESULT_DIR / "ablation6_restart_details.csv", index=False, encoding="utf-8-sig")

    summaries["summary"].to_csv(RESULT_DIR / "ablation6_summary_results.csv", index=False, encoding="utf-8-sig")
    summaries["rank_detail"].to_csv(RESULT_DIR / "ablation6_rank_detail.csv", index=False, encoding="utf-8-sig")
    summaries["average_rank"].to_csv(RESULT_DIR / "ablation6_average_rank.csv", index=False, encoding="utf-8-sig")
    summaries["group_average_rank"].to_csv(RESULT_DIR / "ablation6_group_average_rank.csv", index=False, encoding="utf-8-sig")
    summaries["runtime_summary"].to_csv(RESULT_DIR / "ablation6_runtime_summary.csv", index=False, encoding="utf-8-sig")
    summaries["restart_summary"].to_csv(RESULT_DIR / "ablation6_restart_summary.csv", index=False, encoding="utf-8-sig")
    summaries["mean_curves"].to_csv(RESULT_DIR / "ablation6_mean_curves.csv", index=False, encoding="utf-8-sig")
    summaries["friedman"].to_csv(RESULT_DIR / "ablation6_friedman.csv", index=False, encoding="utf-8-sig")
    summaries["wilcoxon_summary"].to_csv(RESULT_DIR / "ablation6_wilcoxon_summary.csv", index=False, encoding="utf-8-sig")
    summaries["wilcoxon_detail"].to_csv(RESULT_DIR / "ablation6_wilcoxon_per_function_details.csv", index=False, encoding="utf-8-sig")

    print("\nAverage rank:")
    print(summaries["average_rank"].to_string(index=False))

    print("\nFriedman:")
    print(summaries["friedman"].to_string(index=False))

    print("\nWilcoxon summary:")
    print(summaries["wilcoxon_summary"].to_string(index=False))

    print("=" * 100)
    print("CEC2017 ablation experiment finished.")
    print(f"Total runtime: {(time.time() - start_time) / 3600:.2f} h")
    print(f"Saved to: {RESULT_DIR}")
    print("Important files:")
    print("  ablation6_raw_results.csv")
    print("  ablation6_summary_results.csv")
    print("  ablation6_average_rank.csv")
    print("  ablation6_group_average_rank.csv")
    print("  ablation6_runtime_summary.csv")
    print("  ablation6_restart_summary.csv")
    print("  ablation6_wilcoxon_summary.csv")
    print("  ablation6_friedman.csv")
    print("=" * 100)


if __name__ == "__main__":
    # Windows 多进程必须放在这个保护下面。
    main()
