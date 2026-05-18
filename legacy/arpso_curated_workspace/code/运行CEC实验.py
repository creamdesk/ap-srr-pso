# -*- coding: utf-8 -*-
"""
运行 CEC2017 / CEC2022 实验。

当前版本为“完整正式实验 + 强调试信息”：
    1. 默认使用 CEC2017 的 29 个函数：F1 + F3-F30；
    2. 严格检查函数数量，CEC2017 少于 29 个会直接报错；
    3. 自动修复 OPFUNU 中官方 F30 对应 F292017 的类名映射问题；
    4. 开跑前打印环境、函数映射、任务总数；
    5. 出错时打印函数名、算法名、运行轮次、随机种子、边界、异常栈；
    6. 中断或异常时自动保存 partial CSV，方便继续排查。

运行方式：
    python code/运行CEC实验.py

推荐环境：
    Python 3.11
    pip install opfunu==1.0.4 numpy pandas scipy matplotlib

如果你用 Python 3.13，pkg_resources 的 warning 可以暂时忽略；
真正要关注的是 CEC 函数数量是否为 29、总任务数是否为 7830。
"""

from pathlib import Path
import sys
import warnings
import time
import traceback
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
from 优化算法 import run_algorithm


warnings.filterwarnings("ignore", category=RuntimeWarning)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "cec"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 1. 实验总开关
# ============================================================
# probe：探路实验，只跑 ARPSO-v4 vs ARPSO-EIS
# full ：完整实验，跑所有对比算法，用于最终论文表格
RUN_MODE = "full"

# CEC2017 更适合 30 维；如果想跑 CEC2022，可以改成 2022
CEC_YEAR = 2017

DIM = 30
POP_SIZE = 50
N_RUNS = 30

# CEC 常用设置：MaxFEs = 10000 * D
MAX_FES = 10000 * DIM

# 算法初始种群也会消耗一次评价，所以这里减 1，避免明显超过 MaxFEs
MAX_ITER = max(1, MAX_FES // POP_SIZE - 1)

# ============================================================
# 2. CEC 函数列表
# ============================================================
# CEC2017 正式论文实验常用 29 个函数：
#     F1 + F3-F30
# 注意：F2 通常排除；F30 会由 cec_adapter 自动映射到 OPFUNU 的 F292017。
CEC2017_IDS = CEC2017_OFFICIAL_IDS.copy()

# CEC2022：通常使用 F1-F12
CEC2022_IDS = CEC2022_OFFICIAL_IDS.copy()

# 严格模式：如果 CEC2017 没有成功加载 29 个函数，直接停止，不让你白跑。
STRICT_CEC_LOADING = True

# 打印 CEC 函数到 OPFUNU 类名的映射，例如 CEC2017-F30 -> F292017。
DEBUG_CEC_MAPPING = True

# 每隔多少个任务保存一次临时结果。30 表示每个“函数-算法”的 30 次运行后保存一次。
CHECKPOINT_EVERY = 30

# 如果想看更细，可以设为 True；一般不建议，因为 7830 行日志已经很多。
DEBUG_EACH_RUN_DETAIL = False

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


def fmt_seconds(seconds):
    """Format seconds as hh:mm:ss."""
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


def load_cec_benchmarks():
    if CEC_YEAR == 2022:
        return get_cec2022_benchmarks(
            dim=DIM,
            function_ids=CEC2022_IDS,
            subtract_bias=True,
            strict=STRICT_CEC_LOADING,
            debug=DEBUG_CEC_MAPPING,
        )

    if CEC_YEAR == 2017:
        return get_cec2017_benchmarks(
            dim=DIM,
            function_ids=CEC2017_IDS,
            subtract_bias=True,
            strict=STRICT_CEC_LOADING,
            debug=DEBUG_CEC_MAPPING,
        )

    raise ValueError(f"Unsupported CEC_YEAR: {CEC_YEAR}")


def validate_experiment_config(benchmarks):
    functions = list(benchmarks.keys())

    expected_function_count = 29 if CEC_YEAR == 2017 else len(CEC2022_IDS)
    expected_total = expected_function_count * len(ALGORITHMS) * N_RUNS
    actual_total = len(functions) * len(ALGORITHMS) * N_RUNS

    print("=" * 100)
    print("[DEBUG] Experiment configuration check")
    print(f"  RUN_MODE      : {RUN_MODE}")
    print(f"  CEC_YEAR      : {CEC_YEAR}")
    print(f"  DIM           : {DIM}")
    print(f"  POP_SIZE      : {POP_SIZE}")
    print(f"  N_RUNS        : {N_RUNS}")
    print(f"  MAX_FES       : {MAX_FES}")
    print(f"  MAX_ITER      : {MAX_ITER}")
    print(f"  Nominal FEs   : {(MAX_ITER + 1) * POP_SIZE}")
    print(f"  Algorithms    : {len(ALGORITHMS)} -> {', '.join(ALGORITHMS)}")
    print(f"  Functions     : {len(functions)}")
    print(f"  Total tasks   : {actual_total}")
    print(f"  Expected tasks: {expected_total}")
    print("  Function list :")
    print("    " + ", ".join(functions))

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
                f"Extra: {extra}\n"
                "Please check CEC2017_IDS and cec_adapter.py."
            )

        if "CEC2017-F30" not in functions:
            raise RuntimeError("CEC2017-F30 was not loaded. Stop to avoid invalid experiment.")

    if actual_total != expected_total:
        raise RuntimeError(
            "Total task count mismatch.\n"
            f"Actual total: {actual_total}\n"
            f"Expected total: {expected_total}\n"
            "For CEC2017 full mode with 9 algorithms and 30 runs, this should be 7830."
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


def save_partial_outputs(raw_rows, restart_detail_rows, curve_records, reason):
    """Save partial results when interrupted or when an exception occurs."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = RESULTS_DIR / f"cec{CEC_YEAR}_{RUN_MODE}_partial_{timestamp}"

    print()
    print("=" * 100)
    print(f"[DEBUG] Saving partial results because: {reason}")
    print(f"[DEBUG] Partial prefix: {prefix}")

    if raw_rows:
        raw_df = pd.DataFrame(raw_rows)
        raw_path = Path(str(prefix) + "_raw_results.csv")
        raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")
        print(f"  saved: {raw_path}")

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


def save_checkpoint(raw_rows, restart_detail_rows, curve_records, counter, total):
    """Save lightweight checkpoint files during a long experiment."""
    if not raw_rows:
        return

    raw_df = pd.DataFrame(raw_rows)
    raw_path = RESULTS_DIR / f"cec{CEC_YEAR}_{RUN_MODE}_checkpoint_raw_results.csv"
    raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")

    if restart_detail_rows:
        restart_df = pd.DataFrame(restart_detail_rows)
        restart_path = RESULTS_DIR / f"cec{CEC_YEAR}_{RUN_MODE}_checkpoint_restart_details.csv"
        restart_df.to_csv(restart_path, index=False, encoding="utf-8-sig")

    # mean_curves can be moderately large, so save it only at checkpoint interval.
    try:
        mean_curves_df = mean_curve_dataframe(curve_records)
        curve_path = RESULTS_DIR / f"cec{CEC_YEAR}_{RUN_MODE}_checkpoint_mean_curves.csv"
        mean_curves_df.to_csv(curve_path, index=False, encoding="utf-8-sig")
    except Exception as exc:
        print(f"[Warning] Checkpoint mean curve save failed: {exc}")

    print(f"[DEBUG] Checkpoint saved at {counter}/{total}: {raw_path}")


def validate_single_result(result, func_name, alg, run, seed):
    if "best_value" not in result:
        raise KeyError(
            f"Result has no 'best_value'. Function={func_name}, Algorithm={alg}, "
            f"Run={run}, Seed={seed}, Keys={list(result.keys())}"
        )

    best_value = float(result["best_value"])

    if not np.isfinite(best_value):
        raise FloatingPointError(
            f"Non-finite best_value detected. Function={func_name}, Algorithm={alg}, "
            f"Run={run}, Seed={seed}, BestValue={best_value}"
        )

    curve = np.asarray(result.get("curve", []), dtype=float)

    if len(curve) == 0:
        print(
            f"[Warning] Empty convergence curve. "
            f"Function={func_name}, Algorithm={alg}, Run={run}, Seed={seed}"
        )
    elif len(curve) != MAX_ITER:
        print(
            f"[Warning] Curve length mismatch. "
            f"Function={func_name}, Algorithm={alg}, Run={run}, Seed={seed}, "
            f"CurveLength={len(curve)}, Expected={MAX_ITER}"
        )

    if len(curve) > 0 and not np.all(np.isfinite(curve)):
        raise FloatingPointError(
            f"Non-finite value detected in curve. Function={func_name}, Algorithm={alg}, "
            f"Run={run}, Seed={seed}"
        )

    return best_value, curve


def main():
    print_environment()

    raw_rows = []
    curve_records = []
    restart_detail_rows = []

    try:
        benchmarks = load_cec_benchmarks()
        validate_experiment_config(benchmarks)
        print_benchmark_mapping(benchmarks)

        functions = list(benchmarks.keys())

        total = len(functions) * len(ALGORITHMS) * N_RUNS
        counter = 0
        experiment_start = time.perf_counter()

        print("=" * 100)
        print(f"CEC{CEC_YEAR} experiment started: {RUN_MODE}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)

        for func_index, func_name in enumerate(functions, start=1):
            func = benchmarks[func_name]["func"]
            bounds = benchmarks[func_name]["bounds"]
            optimum = benchmarks[func_name].get("optimum", 0.0)
            meta = benchmarks[func_name].get("meta", {})

            print()
            print("-" * 100)
            print(
                f"[DEBUG] Function {func_index}/{len(functions)}: {func_name} | "
                f"bounds={bounds} | optimum={optimum} | "
                f"class={meta.get('class_name', 'unknown')}"
            )
            print("-" * 100)

            for alg in ALGORITHMS:
                alg_start = time.perf_counter()
                print(f"[DEBUG] Start algorithm block: Function={func_name}, Algorithm={alg}")

                for run in range(1, N_RUNS + 1):
                    counter += 1

                    seed = stable_seed(
                        f"cec{CEC_YEAR}_{RUN_MODE}",
                        func_name,
                        alg,
                        run,
                        DIM,
                        POP_SIZE,
                        MAX_ITER,
                    )

                    if DEBUG_EACH_RUN_DETAIL:
                        print(
                            f"[DEBUG] Running: counter={counter}, func={func_name}, "
                            f"alg={alg}, run={run}, seed={seed}, bounds={bounds}"
                        )

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
                    except Exception as exc:
                        print()
                        print("=" * 100)
                        print("[ERROR] Algorithm execution failed.")
                        print(f"  Function : {func_name}")
                        print(f"  Algorithm: {alg}")
                        print(f"  Run      : {run}")
                        print(f"  Seed     : {seed}")
                        print(f"  Bounds   : {bounds}")
                        print(f"  DIM      : {DIM}")
                        print(f"  POP_SIZE : {POP_SIZE}")
                        print(f"  MAX_ITER : {MAX_ITER}")
                        print(f"  Error    : {repr(exc)}")
                        print("[ERROR] Traceback:")
                        traceback.print_exc()
                        print("=" * 100)
                        save_partial_outputs(raw_rows, restart_detail_rows, curve_records, "exception")
                        raise

                    runtime_seconds = time.perf_counter() - start_time
                    best_value, curve = validate_single_result(result, func_name, alg, run, seed)
                    restart_count = int(result.get("restart_count", 0))

                    raw_rows.append(
                        {
                            "ExperimentMode": RUN_MODE,
                            "Function": func_name,
                            "Algorithm": alg,
                            "Run": run,
                            "BestValue": best_value,
                            "RestartCount": restart_count,
                            "RuntimeSeconds": runtime_seconds,
                            "Seed": seed,
                        }
                    )

                    curve_records.append(
                        {
                            "Function": func_name,
                            "Algorithm": alg,
                            "Run": run,
                            "Curve": curve,
                        }
                    )

                    restart_iters = result.get("restart_iters", [])
                    restart_ratios = result.get("restart_ratios", [])
                    restart_sigmas = result.get("restart_sigmas", [])
                    restart_scores = result.get("restart_inefficiency_scores", [])

                    max_len = max(
                        len(restart_iters),
                        len(restart_ratios),
                        len(restart_sigmas),
                        len(restart_scores),
                        0,
                    )

                    for idx in range(max_len):
                        restart_detail_rows.append(
                            {
                                "ExperimentMode": RUN_MODE,
                                "Function": func_name,
                                "Algorithm": alg,
                                "Run": run,
                                "RestartIndex": idx + 1,
                                "RestartIter": (
                                    restart_iters[idx]
                                    if idx < len(restart_iters)
                                    else np.nan
                                ),
                                "RestartRatio": (
                                    restart_ratios[idx]
                                    if idx < len(restart_ratios)
                                    else np.nan
                                ),
                                "RestartSigma": (
                                    restart_sigmas[idx]
                                    if idx < len(restart_sigmas)
                                    else np.nan
                                ),
                                "RestartInefficiencyScore": (
                                    restart_scores[idx]
                                    if idx < len(restart_scores)
                                    else np.nan
                                ),
                            }
                        )

                    elapsed = time.perf_counter() - experiment_start
                    avg_per_task = elapsed / max(counter, 1)
                    eta = avg_per_task * max(total - counter, 0)
                    progress = counter / total * 100.0

                    print(
                        f"[{counter:04d}/{total}] {progress:6.2f}% | "
                        f"{func_name:<12s} | {alg:<10s} | Run={run:02d} | "
                        f"BestError={best_value:.6e} | Restart={restart_count:3d} | "
                        f"Runtime={runtime_seconds:7.3f}s | "
                        f"Elapsed={fmt_seconds(elapsed)} | ETA={fmt_seconds(eta)}"
                    )

                    if CHECKPOINT_EVERY > 0 and counter % CHECKPOINT_EVERY == 0:
                        save_checkpoint(raw_rows, restart_detail_rows, curve_records, counter, total)

                alg_elapsed = time.perf_counter() - alg_start
                print(
                    f"[DEBUG] Finished algorithm block: Function={func_name}, "
                    f"Algorithm={alg}, Runtime={fmt_seconds(alg_elapsed)}"
                )

        raw_df = pd.DataFrame(raw_rows)
        restart_detail_df = pd.DataFrame(restart_detail_rows)

        print()
        print("=" * 100)
        print("[DEBUG] Building summary tables...")
        print(f"  Raw rows       : {len(raw_df)}")
        print(f"  Restart details: {len(restart_detail_df)}")
        print("=" * 100)

        summary_df, rank_detail_df, average_rank_df = summarize_results(
            raw_df,
            functions,
        )

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

        raw_df.to_csv(
            RESULTS_DIR / f"cec{CEC_YEAR}_raw_results.csv",
            index=False,
            encoding="utf-8-sig",
        )
        summary_df.to_csv(
            RESULTS_DIR / f"cec{CEC_YEAR}_summary_results.csv",
            index=False,
            encoding="utf-8-sig",
        )
        rank_detail_df.to_csv(
            RESULTS_DIR / f"cec{CEC_YEAR}_rank_detail.csv",
            index=False,
            encoding="utf-8-sig",
        )
        average_rank_df.to_csv(
            RESULTS_DIR / f"cec{CEC_YEAR}_average_rank.csv",
            index=False,
            encoding="utf-8-sig",
        )
        restart_summary_df.to_csv(
            RESULTS_DIR / f"cec{CEC_YEAR}_restart_summary.csv",
            index=False,
            encoding="utf-8-sig",
        )
        restart_detail_df.to_csv(
            RESULTS_DIR / f"cec{CEC_YEAR}_restart_details.csv",
            index=False,
            encoding="utf-8-sig",
        )
        runtime_summary_df.to_csv(
            RESULTS_DIR / f"cec{CEC_YEAR}_runtime_summary.csv",
            index=False,
            encoding="utf-8-sig",
        )
        mean_curves_df.to_csv(
            RESULTS_DIR / f"cec{CEC_YEAR}_mean_curves.csv",
            index=False,
            encoding="utf-8-sig",
        )

        total_elapsed = time.perf_counter() - experiment_start

        print()
        print("=" * 100)
        print("CEC experiment finished.")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total runtime: {fmt_seconds(total_elapsed)}")
        print(f"Saved to: {RESULTS_DIR}")
        print("Important files:")
        print(f"  cec{CEC_YEAR}_raw_results.csv")
        print(f"  cec{CEC_YEAR}_summary_results.csv")
        print(f"  cec{CEC_YEAR}_average_rank.csv")
        print(f"  cec{CEC_YEAR}_runtime_summary.csv")
        print(f"  cec{CEC_YEAR}_mean_curves.csv")
        print("=" * 100)

    except KeyboardInterrupt:
        print()
        print("=" * 100)
        print("[DEBUG] KeyboardInterrupt detected. The experiment was manually stopped.")
        print("=" * 100)
        save_partial_outputs(raw_rows, restart_detail_rows, curve_records, "keyboard interrupt")
        sys.exit(130)


if __name__ == "__main__":
    main()
