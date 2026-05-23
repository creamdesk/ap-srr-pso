"""统计检验脚本。

包括 Wilcoxon、Friedman、平均排名和 Win/Tie/Loss。
当 --target 不存在或留空时，仍然输出平均排名和 Friedman，跳过 Win/Tie/Loss。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="随机优化实验统计检验")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", default="", help="目标算法；留空则只输出平均排名和 Friedman")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--output-dir", default="results/stats")
    return parser.parse_args()


def _prepare_function_algorithm_means(df: pd.DataFrame) -> pd.DataFrame:
    means = df.groupby(["function", "algorithm"], as_index=False)["best_fitness"].mean()
    return means.pivot(index="function", columns="algorithm", values="best_fitness")


def normalize_input(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "function" not in df.columns and "function_id" in df.columns:
        df["function"] = df["function_id"].apply(lambda x: f"F{int(x)}")
    required = {"function", "algorithm", "best_fitness"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"缺少字段: {sorted(missing)}")
    df["best_fitness"] = pd.to_numeric(df["best_fitness"], errors="coerce")
    df = df.dropna(subset=["best_fitness"])
    return df


def warn_low_runs(df: pd.DataFrame) -> None:
    if "run" not in df.columns:
        print("警告：结果文件缺少 run 字段，无法判断独立运行次数；不要直接用于正式统计结论。")
        return
    run_counts = df.groupby(["function", "algorithm"])["run"].nunique()
    min_runs = int(run_counts.min()) if not run_counts.empty else 0
    if min_runs < 5:
        print(f"警告：最少独立运行次数为 {min_runs}，只适合工程验证，不适合作为正式统计显著性结论。")


def average_rank(df: pd.DataFrame) -> pd.DataFrame:
    pivot = _prepare_function_algorithm_means(df)
    ranks = pivot.rank(axis=1, method="average", ascending=True)
    avg = ranks.mean(axis=0).sort_values()
    return avg.rename("average_rank").reset_index()


def win_tie_loss(df: pd.DataFrame, target: str, alpha: float) -> pd.DataFrame:
    algorithms = sorted(df["algorithm"].unique())
    functions = sorted(df["function"].unique())
    rows = []
    for algorithm in algorithms:
        if algorithm == target:
            continue
        win = tie = loss = valid_functions = 0
        for function in functions:
            target_values = df[(df["function"] == function) & (df["algorithm"] == target)]["best_fitness"].to_numpy()
            other_values = df[(df["function"] == function) & (df["algorithm"] == algorithm)]["best_fitness"].to_numpy()
            n = min(target_values.size, other_values.size)
            if n < 2:
                continue
            valid_functions += 1
            target_values = target_values[:n]
            other_values = other_values[:n]
            try:
                p_value = float(wilcoxon(target_values, other_values, zero_method="wilcox", alternative="two-sided").pvalue)
            except ValueError:
                p_value = 1.0
            if p_value >= alpha:
                tie += 1
            elif np.mean(target_values) < np.mean(other_values):
                win += 1
            else:
                loss += 1
        rows.append({"target": target, "compared_algorithm": algorithm, "win": win, "tie": tie, "loss": loss, "valid_functions": valid_functions})
    return pd.DataFrame(rows)


def friedman_table(df: pd.DataFrame) -> pd.DataFrame:
    pivot = _prepare_function_algorithm_means(df).dropna(axis=1)
    if pivot.shape[1] < 2:
        raise ValueError("Friedman 检验至少需要两个算法。")
    arrays = [pivot[col].to_numpy() for col in pivot.columns]
    stat, p_value = friedmanchisquare(*arrays)
    ranks = average_rank(df)
    ranks["friedman_statistic"] = float(stat)
    ranks["friedman_p_value"] = float(p_value)
    return ranks


def holm_posthoc(df: pd.DataFrame, target: str, alpha: float) -> pd.DataFrame:
    pivot = _prepare_function_algorithm_means(df).dropna(axis=1)
    if target not in pivot.columns:
        raise ValueError(f"目标算法 {target} 不在结果文件中。")
    rows = []
    for algorithm in sorted(col for col in pivot.columns if col != target):
        target_values = pivot[target].to_numpy()
        other_values = pivot[algorithm].to_numpy()
        try:
            p_value = float(wilcoxon(target_values, other_values, zero_method="wilcox", alternative="two-sided").pvalue)
        except ValueError:
            p_value = 1.0
        rows.append(
            {
                "target": target,
                "compared_algorithm": algorithm,
                "target_mean": float(np.mean(target_values)),
                "compared_mean": float(np.mean(other_values)),
                "raw_p_value": p_value,
            }
        )

    rows.sort(key=lambda row: row["raw_p_value"])
    m = len(rows)
    previous_adjusted = 0.0
    for index, row in enumerate(rows, start=1):
        adjusted = min(1.0, (m - index + 1) * row["raw_p_value"])
        adjusted = max(previous_adjusted, adjusted)
        previous_adjusted = adjusted
        row["holm_adjusted_p_value"] = adjusted
        row["significant"] = adjusted < alpha
        row["direction"] = "target_better" if row["target_mean"] < row["compared_mean"] else "target_worse_or_equal"
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    input_path = PROJECT_ROOT / args.input
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    df = normalize_input(pd.read_csv(input_path))
    warn_low_runs(df)
    algorithms = set(df["algorithm"])

    rank_df = average_rank(df)
    friedman_df = friedman_table(df)
    stem = input_path.stem
    rank_path = output_dir / f"{stem}_average_rank.csv"
    friedman_path = output_dir / f"{stem}_friedman.csv"
    rank_df.to_csv(rank_path, index=False, encoding="utf-8-sig")
    friedman_df.to_csv(friedman_path, index=False, encoding="utf-8-sig")

    print(f"平均排名已保存: {rank_path}")
    print(f"Friedman 检验已保存: {friedman_path}")

    if args.target:
        if args.target not in algorithms:
            print(f"警告：目标算法 {args.target} 不在结果文件中，跳过 Win/Tie/Loss。")
            print(f"可用算法: {sorted(algorithms)}")
        else:
            wtl_df = win_tie_loss(df, args.target, args.alpha)
            wtl_path = output_dir / f"{stem}_{args.target}_win_tie_loss.csv"
            wtl_df.to_csv(wtl_path, index=False, encoding="utf-8-sig")
            print(f"Win/Tie/Loss 已保存: {wtl_path}")
            holm_df = holm_posthoc(df, args.target, args.alpha)
            holm_path = output_dir / f"{stem}_{args.target}_holm_posthoc.csv"
            holm_df.to_csv(holm_path, index=False, encoding="utf-8-sig")
            print(f"Holm post-hoc 已保存: {holm_path}")

    print("\n平均排名:")
    print(rank_df.to_string(index=False))


if __name__ == "__main__":
    main()
