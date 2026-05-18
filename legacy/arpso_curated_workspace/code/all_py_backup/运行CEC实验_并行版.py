# -*- coding: utf-8 -*-
"""
运行 CEC2017 / CEC2022 实验：多进程并行版。

适合 16GB 内存机器的稳妥设置：
    默认 MAX_WORKERS = 4

特点：
    1. 默认使用 CEC2017 正式 29 个函数：F1 + F3-F30；
    2. 子进程只负责计算，主进程统一写 CSV，避免多进程同时写文件导致结果损坏；
    3. 结果文件名与串行版一致，可继续使用：python code/统计检验_CEC.py；
    4. 异常时会打印 Function / Algorithm / Run / Seed / Worker PID / traceback；
    5. 中断或异常时自动保存 partial CSV；
    6. 默认最多保留少量待执行任务，降低 16GB 内存压力。

运行方式：
    python code/运行CEC实验_并行版.py

如果想临时调整进程数，不改代码也可以在 PowerShell 里：
    $env:CEC_MAX_WORKERS="6"
    python code/运行CEC实验_并行版.py

建议：
    16GB 内存先用默认 4 进程；确认稳定后再试 6 进程。
"""

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from multiprocessing import freeze_support
import os
import sys
import time
import traceback
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

from common import stable_seed, summarize_results, mean_curve_dataframe
from cec_adapter import (
    CEC2017_OFFICIAL_IDS,
    CEC2022_OFFICIAL_IDS,
    get_cec2022_benchmarks,
    get_cec2017_benchmarks,
    get_environment_info,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "cec"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 1. 实验总开关
# ============================================================
RUN_MODE = "full"          # probe / full
CEC_YEAR = 2017

DIM = 30
POP_SIZE = 50
N_RUNS = 30
MAX_FES = 10000 * DIM
MAX_ITER = max(1, MAX_FES // POP_SIZE - 1)

CEC2017_IDS = CEC2017_OFFICIAL_IDS.copy()      # F1 + F3-F30，共 29 个
CEC2022_IDS = CEC2022_OFFICIAL_IDS.copy()      # F1-F12
STRICT_CEC_LOADING = True
DEBUG_CEC_MAPPING = True

# ============================================================
# 2. 并行设置
# ============================================================
# 16GB 内存默认建议 4。需要更快时可以用环境变量 CEC_MAX_WORKERS 临时改成 6。
MAX_WORKERS = int(os.environ.get("CEC_MAX_WORKERS", "4"))

# 不要一次性提交 7830 个任务，避免主进程堆积过多 future/result 对象。
MAX_PENDING_TASKS = max(MAX_WORKERS * 2, MAX_WORKERS)

# 每完成多少个任务保存一次轻量 checkpoint。checkpoint 默认不保存 mean_curves，避免拖慢。
CHECKPOINT_EVERY_COMPLETED = 60

# 如果设为 True，会在 checkpoint 时也保存 mean curves，但比较耗时、耗内存。
SAVE_CURVE_CHECKPOINT = False

# 子进程是否打印 CEC mapping。默认 False，否则 4 个进程会刷很多重复日志。
DEBUG_WORKER_CEC_MAPPING = False

PROBE_ALGORITHMS = [
    "ARPSO-v4",
    "ARPSO-EIS",
]

FULL_ALGORITHMS = [
    "PSO",
    "PSO-AW",
    "PSO-RS",
    "CLPSO",
    "HPSO-TVAC",
    "ARPSO-v4",
    "ARPSO-EIS",
    "GA",
    "DE",
]

ALGORITHMS = PROBE_ALGORITHMS if RUN_MODE == "probe" else FULL_ALGORITHMS

# ============================================================
# 3. Worker 全局变量。每个子进程初始化一次。
# ============================================================
_WORKER_BENCHMARKS = None
_WORKER_CONFIG = None


def fmt_seconds(seconds):
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def print_environment():
    print("=" * 100)
    print("[DEBUG] Runtime environment")
    for key, value in get_environment_info().items():
        print(f"  {key}: {value}")
    print(f"  project_root: {PROJECT_ROOT}")
    print(f"  results_dir : {RESULTS_DIR}")
    print(f"  script      : {Path(__file__).resolve()}")
    print("=" * 100)


def load_cec_benchmarks(debug=False):
    if CEC_YEAR == 2022:
        return get_cec2022_benchmarks(
            dim=DIM,
            function_ids=CEC2022_IDS,
            subtract_bias=True,
            strict=STRICT_CEC_LOADING,
            debug=debug,
        )

    if CEC_YEAR == 2017:
        return get_cec2017_benchmarks(
            dim=DIM,
            function_ids=CEC2017_IDS,
            subtract_bias=True,
            strict=STRICT_CEC_LOADING,
            debug=debug,
        )

    raise ValueError(f"Unsupported CEC_YEAR: {CEC_YEAR}")


def validate_experiment_config(benchmarks):
    functions = list(benchmarks.keys())

    expected_function_count = 29 if CEC_YEAR == 2017 else len(CEC2022_IDS)
    expected_total = expected_function_count * len(ALGORITHMS) * N_RUNS
    actual_total = len(functions) * len(ALGORITHMS) * N_RUNS

    print("=" * 100)
    print("[DEBUG] Parallel experiment configuration check")
    print(f"  RUN_MODE         : {RUN_MODE}")
    print(f"  CEC_YEAR         : {CEC_YEAR}")
    print(f"  DIM              : {DIM}")
    print(f"  POP_SIZE         : {POP_SIZE}")
    print(f"  N_RUNS           : {N_RUNS}")
    print(f"  MAX_FES          : {MAX_FES}")
    print(f"  MAX_ITER         : {MAX_ITER}")
    print(f"  Nominal FEs      : {(MAX_ITER + 1) * POP_SIZE}")
    print(f"  Algorithms       : {len(ALGORITHMS)} -> {', '.join(ALGORITHMS)}")
    print(f"  Functions        : {len(functions)}")
    print(f"  Total tasks      : {actual_total}")
    print(f"  Expected tasks   : {expected_total}")
    print(f"  MAX_WORKERS      : {MAX_WORKERS}")
    print(f"  MAX_PENDING_TASKS: {MAX_PENDING_TASKS}")
    print("  Function list    :")
    print("    " + ", ".join(functions))

    if MAX_WORKERS < 1:
        raise ValueError("MAX_WORKERS must be >= 1")

    if CEC_YEAR == 2017:
        expected_names = [f"CEC2017-F{fid}" for fid in CEC2017_OFFICIAL_IDS]
        missing = [name for name in expected_names if name not in functions]
        extra = [name for name in functions if name not in expected_names]

        print(f"  Expected CEC2017 functions: {len(expected_names)}")
        print(f"  Missing functions         : {missing if missing else 'None'}")
        print(f"  Extra functions           : {extra if extra else 'None'}")

        if len(functions) != 29 or missing or extra:
            raise RuntimeError(
                "CEC2017 function set is not the formal 29-function suite.\n"
                f"Loaded {len(functions)} functions: {functions}\n"
                f"Missing: {missing}\n"
                f"Extra: {extra}"
            )

        if "CEC2017-F30" not in functions:
            raise RuntimeError("CEC2017-F30 was not loaded. Stop to avoid invalid experiment.")

    if actual_total != expected_total:
        raise RuntimeError(
            "Total task count mismatch.\n"
            f"Actual total: {actual_total}\n"
            f"Expected total: {expected_total}"
        )

    print("[DEBUG] Configuration check passed.")
    print("=" * 100)


def print_benchmark_mapping(benchmarks):
    print("=" * 100)
    print("[DEBUG] Loaded benchmark mapping")
    for name, info in benchmarks.items():
        meta = info.get("meta", {})
        class_name = meta.get("class_name", "unknown")
        internal_fid = meta.get("internal_fid", "unknown")
        mapping_mode = meta.get("mapping_mode", "unknown")
        f_global = meta.get("f_global", "unknown")
        bounds = info.get("bounds", ("?", "?"))

        print(
            f"  {name:<12s} -> {class_name:<8s} | "
            f"internal_fid={internal_fid!s:<2s} | "
            f"mode={mapping_mode:<15s} | "
            f"bounds={bounds} | f_global={f_global}"
        )
    print("=" * 100)


def function_name_to_fid(function_name):
    # CEC2017-F30 -> 30
    return int(str(function_name).split("-F")[-1])


def make_task_list(functions):
    tasks = []
    task_id = 0
    for func_name in functions:
        fid = function_name_to_fid(func_name)
        for alg in ALGORITHMS:
            for run in range(1, N_RUNS + 1):
                task_id += 1
                seed = stable_seed(
                    f"cec{CEC_YEAR}_{RUN_MODE}",
                    func_name,
                    alg,
                    run,
                    DIM,
                    POP_SIZE,
                    MAX_ITER,
                )
                tasks.append({
                    "TaskID": task_id,
                    "Function": func_name,
                    "FID": fid,
                    "Algorithm": alg,
                    "Run": run,
                    "Seed": seed,
                })
    return tasks


def init_worker(cec_year, dim, function_ids, subtract_bias, strict, debug_mapping):
    """每个子进程启动时加载一次 CEC 函数，避免每个任务重复加载。"""
    global _WORKER_BENCHMARKS, _WORKER_CONFIG

    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", message=".*pkg_resources is deprecated.*")

    if cec_year == 2017:
        _WORKER_BENCHMARKS = get_cec2017_benchmarks(
            dim=dim,
            function_ids=function_ids,
            subtract_bias=subtract_bias,
            strict=strict,
            debug=debug_mapping,
        )
    elif cec_year == 2022:
        _WORKER_BENCHMARKS = get_cec2022_benchmarks(
            dim=dim,
            function_ids=function_ids,
            subtract_bias=subtract_bias,
            strict=strict,
            debug=debug_mapping,
        )
    else:
        raise ValueError(f"Unsupported cec_year in worker: {cec_year}")

    _WORKER_CONFIG = {
        "cec_year": cec_year,
        "dim": dim,
        "pid": os.getpid(),
    }


def validate_worker_result(result, task):
    if "best_value" not in result:
        raise KeyError(
            "Result has no 'best_value'. "
            f"Task={task}, Keys={list(result.keys())}"
        )

    best_value = float(result["best_value"])
    if not np.isfinite(best_value):
        raise FloatingPointError(
            f"Non-finite best_value detected. Task={task}, BestValue={best_value}"
        )

    curve = np.asarray(result.get("curve", []), dtype=float)
    if len(curve) == 0:
        # 不直接失败，因为某些算法可能没有曲线；但当前项目算法理论上都有。
        curve = np.asarray([], dtype=float)
    elif not np.all(np.isfinite(curve)):
        raise FloatingPointError(f"Non-finite values in convergence curve. Task={task}")

    return best_value, curve


def run_one_task(task):
    """子进程执行单个 Function-Algorithm-Run 任务。"""
    global _WORKER_BENCHMARKS, _WORKER_CONFIG

    if _WORKER_BENCHMARKS is None:
        raise RuntimeError("Worker benchmarks are not initialized.")

    # 放在函数内部 import，确保 Windows spawn 子进程能正确加载中文模块名。
    from 优化算法 import run_algorithm  # pylint: disable=import-outside-toplevel

    func_name = task["Function"]
    alg = task["Algorithm"]
    run = int(task["Run"])
    seed = int(task["Seed"])

    if func_name not in _WORKER_BENCHMARKS:
        raise KeyError(f"{func_name} is not loaded in worker PID={os.getpid()}")

    info = _WORKER_BENCHMARKS[func_name]
    func = info["func"]
    bounds = info["bounds"]
    meta = info.get("meta", {})

    start_time = time.perf_counter()

    try:
        result = run_algorithm(
            algorithm_name=alg,
            func=func,
            bounds=bounds,
            dim=DIM,
            pop_size=POP_SIZE,
            max_iter=MAX_ITER,
            seed=seed,
        )
        runtime_seconds = time.perf_counter() - start_time
        best_value, curve = validate_worker_result(result, task)
        restart_count = int(result.get("restart_count", 0))

        restart_iters = list(result.get("restart_iters", []))
        restart_ratios = list(result.get("restart_ratios", []))
        restart_sigmas = list(result.get("restart_sigmas", []))
        restart_scores = list(result.get("restart_inefficiency_scores", []))

        max_len = max(
            len(restart_iters),
            len(restart_ratios),
            len(restart_sigmas),
            len(restart_scores),
            0,
        )

        restart_details = []
        for idx in range(max_len):
            restart_details.append({
                "ExperimentMode": RUN_MODE,
                "Function": func_name,
                "Algorithm": alg,
                "Run": run,
                "RestartIndex": idx + 1,
                "RestartIter": restart_iters[idx] if idx < len(restart_iters) else np.nan,
                "RestartRatio": restart_ratios[idx] if idx < len(restart_ratios) else np.nan,
                "RestartSigma": restart_sigmas[idx] if idx < len(restart_sigmas) else np.nan,
                "RestartInefficiencyScore": restart_scores[idx] if idx < len(restart_scores) else np.nan,
            })

        return {
            "TaskID": int(task["TaskID"]),
            "WorkerPID": os.getpid(),
            "ExperimentMode": RUN_MODE,
            "Function": func_name,
            "Algorithm": alg,
            "Run": run,
            "BestValue": best_value,
            "RestartCount": restart_count,
            "RuntimeSeconds": runtime_seconds,
            "Seed": seed,
            "Curve": curve,
            "RestartDetails": restart_details,
            "MetaClass": meta.get("class_name", "unknown"),
            "Bounds": bounds,
        }
    except Exception as exc:
        tb = traceback.format_exc()
        raise RuntimeError(
            "Worker task failed.\n"
            f"  PID      : {os.getpid()}\n"
            f"  TaskID   : {task.get('TaskID')}\n"
            f"  Function : {func_name}\n"
            f"  Algorithm: {alg}\n"
            f"  Run      : {run}\n"
            f"  Seed     : {seed}\n"
            f"  Bounds   : {bounds}\n"
            f"  Class    : {meta.get('class_name', 'unknown')}\n"
            f"  Error    : {repr(exc)}\n"
            f"Traceback:\n{tb}"
        ) from exc


def sort_outputs(raw_df, restart_detail_df):
    func_order = {f"CEC{CEC_YEAR}-F{fid}": i for i, fid in enumerate(CEC2017_IDS if CEC_YEAR == 2017 else CEC2022_IDS)}
    alg_order = {alg: i for i, alg in enumerate(ALGORITHMS)}

    if not raw_df.empty:
        raw_df["_FunctionOrder"] = raw_df["Function"].map(func_order)
        raw_df["_AlgorithmOrder"] = raw_df["Algorithm"].map(alg_order)
        raw_df = raw_df.sort_values(["_FunctionOrder", "_AlgorithmOrder", "Run"]).drop(
            columns=["_FunctionOrder", "_AlgorithmOrder"]
        )

    if not restart_detail_df.empty:
        restart_detail_df["_FunctionOrder"] = restart_detail_df["Function"].map(func_order)
        restart_detail_df["_AlgorithmOrder"] = restart_detail_df["Algorithm"].map(alg_order)
        restart_detail_df = restart_detail_df.sort_values(
            ["_FunctionOrder", "_AlgorithmOrder", "Run", "RestartIndex"]
        ).drop(columns=["_FunctionOrder", "_AlgorithmOrder"])

    return raw_df, restart_detail_df


def save_partial_outputs(raw_rows, restart_detail_rows, curve_records, reason):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = RESULTS_DIR / f"cec{CEC_YEAR}_{RUN_MODE}_parallel_partial_{timestamp}"

    print()
    print("=" * 100)
    print(f"[DEBUG] Saving partial results because: {reason}")
    print(f"[DEBUG] Partial prefix: {prefix}")

    if raw_rows:
        raw_df = pd.DataFrame(raw_rows)
        restart_df = pd.DataFrame(restart_detail_rows)
        raw_df, restart_df = sort_outputs(raw_df, restart_df)
        raw_path = Path(str(prefix) + "_raw_results.csv")
        raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")
        print(f"  saved: {raw_path}")

        # 立刻生成一个临时 summary，方便你提前看趋势。
        try:
            functions = list(raw_df["Function"].drop_duplicates())
            summary_df, rank_detail_df, average_rank_df = summarize_results(raw_df, functions)
            summary_path = Path(str(prefix) + "_summary_results.csv")
            avg_rank_path = Path(str(prefix) + "_average_rank.csv")
            summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
            average_rank_df.to_csv(avg_rank_path, index=False, encoding="utf-8-sig")
            print(f"  saved: {summary_path}")
            print(f"  saved: {avg_rank_path}")
        except Exception as exc:
            print(f"  [Warning] Failed to save partial summary: {exc}")

    if restart_detail_rows:
        restart_df = pd.DataFrame(restart_detail_rows)
        restart_path = Path(str(prefix) + "_restart_details.csv")
        restart_df.to_csv(restart_path, index=False, encoding="utf-8-sig")
        print(f"  saved: {restart_path}")

    if curve_records:
        try:
            mean_curves_df = mean_curve_dataframe(curve_records)
            curve_path = Path(str(prefix) + "_mean_curves.csv")
            mean_curves_df.to_csv(curve_path, index=False, encoding="utf-8-sig")
            print(f"  saved: {curve_path}")
        except Exception as exc:
            print(f"  [Warning] Failed to save partial mean curves: {exc}")

    print("=" * 100)
    print()


def save_checkpoint(raw_rows, restart_detail_rows, curve_records, completed, total):
    if not raw_rows:
        return

    raw_df = pd.DataFrame(raw_rows)
    restart_df = pd.DataFrame(restart_detail_rows)
    raw_df, restart_df = sort_outputs(raw_df, restart_df)

    raw_path = RESULTS_DIR / f"cec{CEC_YEAR}_{RUN_MODE}_parallel_checkpoint_raw_results.csv"
    raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")

    if not restart_df.empty:
        restart_path = RESULTS_DIR / f"cec{CEC_YEAR}_{RUN_MODE}_parallel_checkpoint_restart_details.csv"
        restart_df.to_csv(restart_path, index=False, encoding="utf-8-sig")

    if SAVE_CURVE_CHECKPOINT:
        try:
            mean_curves_df = mean_curve_dataframe(curve_records)
            curve_path = RESULTS_DIR / f"cec{CEC_YEAR}_{RUN_MODE}_parallel_checkpoint_mean_curves.csv"
            mean_curves_df.to_csv(curve_path, index=False, encoding="utf-8-sig")
        except Exception as exc:
            print(f"[Warning] Checkpoint mean curve save failed: {exc}")

    print(f"[DEBUG] Parallel checkpoint saved at completed={completed}/{total}: {raw_path}")


def build_final_outputs(raw_rows, restart_detail_rows, curve_records, functions, experiment_start):
    raw_df = pd.DataFrame(raw_rows)
    restart_detail_df = pd.DataFrame(restart_detail_rows)
    raw_df, restart_detail_df = sort_outputs(raw_df, restart_detail_df)

    print()
    print("=" * 100)
    print("[DEBUG] Building final summary tables...")
    print(f"  Raw rows       : {len(raw_df)}")
    print(f"  Restart details: {len(restart_detail_df)}")
    print(f"  Curve records  : {len(curve_records)}")
    print("=" * 100)

    expected_total = len(functions) * len(ALGORITHMS) * N_RUNS
    if len(raw_df) != expected_total:
        raise RuntimeError(
            "Final raw row count mismatch.\n"
            f"Expected {expected_total}, got {len(raw_df)}.\n"
            "Do not use this as final paper result until all tasks finish."
        )

    summary_df, rank_detail_df, average_rank_df = summarize_results(raw_df, functions)

    restart_summary_df = (
        raw_df.groupby(["Function", "Algorithm"])
        .agg(
            AvgRestart=("RestartCount", "mean"),
            StdRestart=("RestartCount", "std"),
            MaxRestart=("RestartCount", "max"),
            MinRestart=("RestartCount", "min"),
        )
        .reset_index()
    )

    runtime_summary_df = (
        raw_df.groupby("Algorithm")
        .agg(
            AvgRuntimeSeconds=("RuntimeSeconds", "mean"),
            StdRuntimeSeconds=("RuntimeSeconds", "std"),
            TotalRuntimeSeconds=("RuntimeSeconds", "sum"),
        )
        .reset_index()
    )

    min_runtime = runtime_summary_df["AvgRuntimeSeconds"].min()
    runtime_summary_df["RelativeRuntime"] = runtime_summary_df["AvgRuntimeSeconds"] / (
        min_runtime + 1e-30
    )

    mean_curves_df = mean_curve_dataframe(curve_records)

    raw_df.to_csv(RESULTS_DIR / f"cec{CEC_YEAR}_raw_results.csv", index=False, encoding="utf-8-sig")
    summary_df.to_csv(RESULTS_DIR / f"cec{CEC_YEAR}_summary_results.csv", index=False, encoding="utf-8-sig")
    rank_detail_df.to_csv(RESULTS_DIR / f"cec{CEC_YEAR}_rank_detail.csv", index=False, encoding="utf-8-sig")
    average_rank_df.to_csv(RESULTS_DIR / f"cec{CEC_YEAR}_average_rank.csv", index=False, encoding="utf-8-sig")
    restart_summary_df.to_csv(RESULTS_DIR / f"cec{CEC_YEAR}_restart_summary.csv", index=False, encoding="utf-8-sig")
    restart_detail_df.to_csv(RESULTS_DIR / f"cec{CEC_YEAR}_restart_details.csv", index=False, encoding="utf-8-sig")
    runtime_summary_df.to_csv(RESULTS_DIR / f"cec{CEC_YEAR}_runtime_summary.csv", index=False, encoding="utf-8-sig")
    mean_curves_df.to_csv(RESULTS_DIR / f"cec{CEC_YEAR}_mean_curves.csv", index=False, encoding="utf-8-sig")

    total_elapsed = time.perf_counter() - experiment_start

    print()
    print("=" * 100)
    print("Parallel CEC experiment finished.")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total runtime: {fmt_seconds(total_elapsed)}")
    print(f"Saved to: {RESULTS_DIR}")
    print("Important files:")
    print(f"  cec{CEC_YEAR}_raw_results.csv")
    print(f"  cec{CEC_YEAR}_summary_results.csv")
    print(f"  cec{CEC_YEAR}_average_rank.csv")
    print(f"  cec{CEC_YEAR}_runtime_summary.csv")
    print(f"  cec{CEC_YEAR}_mean_curves.csv")
    print("Next step:")
    print("  python code\\统计检验_CEC.py")
    print("=" * 100)


def submit_more(executor, task_iter, pending):
    while len(pending) < MAX_PENDING_TASKS:
        try:
            task = next(task_iter)
        except StopIteration:
            break
        future = executor.submit(run_one_task, task)
        pending[future] = task


def main():
    print_environment()

    # 主进程加载一遍，只用于自检、打印 mapping，不参与计算。
    benchmarks = load_cec_benchmarks(debug=DEBUG_CEC_MAPPING)
    validate_experiment_config(benchmarks)
    print_benchmark_mapping(benchmarks)

    functions = list(benchmarks.keys())
    tasks = make_task_list(functions)
    total = len(tasks)

    raw_rows = []
    curve_records = []
    restart_detail_rows = []

    print("=" * 100)
    print(f"CEC{CEC_YEAR} parallel experiment started: {RUN_MODE}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Workers: {MAX_WORKERS}")
    print(f"Pending window: {MAX_PENDING_TASKS}")
    print("=" * 100)

    experiment_start = time.perf_counter()
    completed = 0
    submitted = 0

    function_ids = CEC2017_IDS if CEC_YEAR == 2017 else CEC2022_IDS

    executor = None
    try:
        with ProcessPoolExecutor(
            max_workers=MAX_WORKERS,
            initializer=init_worker,
            initargs=(
                CEC_YEAR,
                DIM,
                function_ids,
                True,
                STRICT_CEC_LOADING,
                DEBUG_WORKER_CEC_MAPPING,
            ),
        ) as executor:
            task_iter = iter(tasks)
            pending = {}
            submit_more(executor, task_iter, pending)
            submitted = len(pending)

            while pending:
                done, _ = wait(pending.keys(), return_when=FIRST_COMPLETED)

                for future in done:
                    task = pending.pop(future)

                    try:
                        item = future.result()
                    except Exception as exc:
                        print()
                        print("=" * 100)
                        print("[ERROR] Parallel task failed.")
                        print(f"  TaskID   : {task.get('TaskID')}")
                        print(f"  Function : {task.get('Function')}")
                        print(f"  Algorithm: {task.get('Algorithm')}")
                        print(f"  Run      : {task.get('Run')}")
                        print(f"  Seed     : {task.get('Seed')}")
                        print(f"  Error    : {repr(exc)}")
                        print("=" * 100)
                        save_partial_outputs(raw_rows, restart_detail_rows, curve_records, "parallel exception")
                        # 让异常继续抛出，避免错误结果被误认为正式结果。
                        raise

                    completed += 1

                    raw_rows.append({
                        "ExperimentMode": item["ExperimentMode"],
                        "Function": item["Function"],
                        "Algorithm": item["Algorithm"],
                        "Run": item["Run"],
                        "BestValue": item["BestValue"],
                        "RestartCount": item["RestartCount"],
                        "RuntimeSeconds": item["RuntimeSeconds"],
                        "Seed": item["Seed"],
                    })

                    curve_records.append({
                        "Function": item["Function"],
                        "Algorithm": item["Algorithm"],
                        "Run": item["Run"],
                        "Curve": item["Curve"],
                    })

                    restart_detail_rows.extend(item["RestartDetails"])

                    elapsed = time.perf_counter() - experiment_start
                    avg_per_task = elapsed / max(completed, 1)
                    eta = avg_per_task * max(total - completed, 0)
                    progress = completed / total * 100.0

                    print(
                        f"[{completed:04d}/{total}] {progress:6.2f}% | "
                        f"TaskID={item['TaskID']:04d} | PID={item['WorkerPID']} | "
                        f"{item['Function']:<12s} | {item['Algorithm']:<10s} | Run={item['Run']:02d} | "
                        f"BestError={item['BestValue']:.6e} | Restart={item['RestartCount']:3d} | "
                        f"Runtime={item['RuntimeSeconds']:7.3f}s | "
                        f"Elapsed={fmt_seconds(elapsed)} | ETA={fmt_seconds(eta)}"
                    )

                    if CHECKPOINT_EVERY_COMPLETED > 0 and completed % CHECKPOINT_EVERY_COMPLETED == 0:
                        save_checkpoint(raw_rows, restart_detail_rows, curve_records, completed, total)

                    before = len(pending)
                    submit_more(executor, task_iter, pending)
                    submitted += max(0, len(pending) - before)

        build_final_outputs(raw_rows, restart_detail_rows, curve_records, functions, experiment_start)

    except KeyboardInterrupt:
        print()
        print("=" * 100)
        print("[DEBUG] KeyboardInterrupt detected. The parallel experiment was manually stopped.")
        print("=" * 100)
        if executor is not None:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except Exception:
                pass
        save_partial_outputs(raw_rows, restart_detail_rows, curve_records, "keyboard interrupt")
        sys.exit(130)


if __name__ == "__main__":
    freeze_support()
    main()
