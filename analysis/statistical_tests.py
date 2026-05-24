"""Statistical tests for AP-SRR-PSO experiment outputs."""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Statistical tests for optimizer comparisons")
    p.add_argument("--input", required=True)
    p.add_argument("--target", default="AP-SRR-PSO")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--output-dir", default="results/stats")
    return p.parse_args()


def normalize_input(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "function" not in df.columns and "function_id" in df.columns:
        df["function"] = df["function_id"].apply(lambda x: f"F{int(x)}")
    missing = {"function", "algorithm", "best_fitness"} - set(df.columns)
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")
    if "status" in df.columns:
        df = df[df["status"].fillna("ok") == "ok"].copy()
    df["best_fitness"] = pd.to_numeric(df["best_fitness"], errors="coerce")
    return df.dropna(subset=["best_fitness"])


def warn_low_runs(df: pd.DataFrame) -> None:
    if "run" not in df.columns:
        warnings.warn("No run column found; pairwise tests cannot verify aligned independent runs.", RuntimeWarning)
        return
    counts = df.groupby(["function", "algorithm"])["run"].nunique()
    min_runs = int(counts.min()) if not counts.empty else 0
    if min_runs < 5:
        warnings.warn(f"Only {min_runs} run(s) in at least one group. Treat as engineering validation, not formal evidence.", RuntimeWarning)


def function_algorithm_means(df: pd.DataFrame) -> pd.DataFrame:
    means = df.groupby(["function", "algorithm"], as_index=False)["best_fitness"].mean()
    return means.pivot(index="function", columns="algorithm", values="best_fitness")


def average_rank(df: pd.DataFrame) -> pd.DataFrame:
    pivot = function_algorithm_means(df)
    ranks = pivot.rank(axis=1, method="average", ascending=True)
    return ranks.mean(axis=0).sort_values().rename("average_rank").reset_index()


def aligned_values(df: pd.DataFrame, function: str, target: str, other: str) -> tuple[np.ndarray, np.ndarray, bool]:
    a = df[(df["function"] == function) & (df["algorithm"] == target)].copy()
    b = df[(df["function"] == function) & (df["algorithm"] == other)].copy()
    if "run" in df.columns:
        merged = a[["run", "best_fitness"]].merge(b[["run", "best_fitness"]], on="run", suffixes=("_target", "_other"))
        aligned = len(merged) == len(a) == len(b)
        return merged["best_fitness_target"].to_numpy(), merged["best_fitness_other"].to_numpy(), aligned
    n = min(len(a), len(b))
    return a["best_fitness"].to_numpy()[:n], b["best_fitness"].to_numpy()[:n], False


def win_tie_loss(df: pd.DataFrame, target: str, alpha: float) -> pd.DataFrame:
    rows = []
    for alg in sorted(a for a in df["algorithm"].unique() if a != target):
        win = tie = loss = valid = unaligned = 0
        for fun in sorted(df["function"].unique()):
            tv, ov, aligned = aligned_values(df, fun, target, alg)
            if not aligned:
                unaligned += 1
            if min(tv.size, ov.size) < 2:
                continue
            valid += 1
            try:
                p_value = float(wilcoxon(tv, ov, zero_method="wilcox", alternative="two-sided").pvalue)
            except ValueError:
                p_value = 1.0
            if p_value >= alpha:
                tie += 1
            elif float(np.mean(tv)) < float(np.mean(ov)):
                win += 1
            else:
                loss += 1
        rows.append({"target": target, "compared_algorithm": alg, "win": win, "tie": tie, "loss": loss, "valid_functions": valid, "unaligned_functions": unaligned})
    return pd.DataFrame(rows)


def friedman_table(df: pd.DataFrame) -> pd.DataFrame:
    pivot = function_algorithm_means(df).dropna(axis=1)
    out = average_rank(df)
    if pivot.shape[1] < 3:
        warnings.warn("Friedman test requires at least three algorithms; writing rank-only fallback.", RuntimeWarning)
        out["friedman_statistic"] = ""
        out["friedman_p_value"] = ""
        out["friedman_status"] = "skipped_less_than_three_algorithms"
        return out
    stat, p_value = friedmanchisquare(*[pivot[c].to_numpy() for c in pivot.columns])
    out["friedman_statistic"] = float(stat)
    out["friedman_p_value"] = float(p_value)
    out["friedman_status"] = "ok"
    return out


def holm_posthoc(df: pd.DataFrame, target: str, alpha: float) -> pd.DataFrame:
    pivot = function_algorithm_means(df).dropna(axis=1)
    if target not in pivot.columns:
        raise ValueError(f"Target algorithm not found: {target}")
    rows = []
    for alg in sorted(c for c in pivot.columns if c != target):
        tv = pivot[target].to_numpy()
        ov = pivot[alg].to_numpy()
        try:
            p_value = float(wilcoxon(tv, ov, zero_method="wilcox", alternative="two-sided").pvalue)
        except ValueError:
            p_value = 1.0
        rows.append({"target": target, "compared_algorithm": alg, "target_mean": float(np.mean(tv)), "compared_mean": float(np.mean(ov)), "raw_p_value": p_value})
    rows.sort(key=lambda r: r["raw_p_value"])
    prev = 0.0
    m = len(rows)
    for i, row in enumerate(rows, start=1):
        adj = max(prev, min(1.0, (m - i + 1) * row["raw_p_value"]))
        prev = adj
        row["holm_adjusted_p_value"] = adj
        row["significant"] = adj < alpha
        row["direction"] = "target_better" if row["target_mean"] < row["compared_mean"] else "target_worse_or_equal"
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    input_path = PROJECT_ROOT / args.input
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    df = normalize_input(pd.read_csv(input_path))
    warn_low_runs(df)
    stem = input_path.stem
    rank = average_rank(df)
    fried = friedman_table(df)
    rank.to_csv(output_dir / f"{stem}_average_rank.csv", index=False, encoding="utf-8-sig")
    fried.to_csv(output_dir / f"{stem}_friedman.csv", index=False, encoding="utf-8-sig")
    print(rank.to_string(index=False))
    if args.target in set(df["algorithm"]):
        wtl = win_tie_loss(df, args.target, args.alpha)
        holm = holm_posthoc(df, args.target, args.alpha)
        wtl.to_csv(output_dir / f"{stem}_{args.target}_win_tie_loss.csv", index=False, encoding="utf-8-sig")
        holm.to_csv(output_dir / f"{stem}_{args.target}_holm_posthoc.csv", index=False, encoding="utf-8-sig")
        if int(wtl.get("unaligned_functions", pd.Series(dtype=int)).sum()) > 0:
            warnings.warn("Some pairwise comparisons were not perfectly run-aligned.", RuntimeWarning)
    elif args.target:
        print(f"Target algorithm not found: {args.target}")


if __name__ == "__main__":
    main()
