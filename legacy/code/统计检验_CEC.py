# -*- coding: utf-8 -*-
"""
Statistical tests for CEC experiments.

Function-level Friedman:
    each CEC function is treated as one block.

Per-function Wilcoxon:
    each function uses 30 paired runs.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata, wilcoxon

from common import safe_read_csv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "cec"
TABLE_DIR = PROJECT_ROOT / "paper_tables"

TABLE_DIR.mkdir(exist_ok=True)

CEC_YEAR = 2017
BASE_ALGORITHM = "ARPSO-EIS"

ALGORITHM_ORDER = [
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


def sci_latex(x, precision=3):
    x = float(x)

    if np.isnan(x):
        return "--"

    if x == 0:
        return "0"

    ax = abs(x)

    if ax < 1e-3 or ax >= 1e4:
        s = f"{x:.{precision}e}"
        m, e = s.split("e")
        return f"${m}\\times 10^{{{int(e)}}}$"

    return f"{x:.{precision}f}"


def p_latex(p):
    p = float(p)

    if p < 1e-4:
        return "$<10^{-4}$"

    return f"{p:.4f}"


def main():
    raw_path = RESULTS_DIR / f"cec{CEC_YEAR}_raw_results.csv"
    summary_path = RESULTS_DIR / f"cec{CEC_YEAR}_summary_results.csv"

    raw_df = safe_read_csv(raw_path)
    summary_df = safe_read_csv(summary_path)

    algorithms = [
        alg for alg in ALGORITHM_ORDER
        if alg in raw_df["Algorithm"].unique()
    ]

    functions = list(summary_df["Function"].unique())

    if BASE_ALGORITHM not in algorithms:
        raise ValueError(f"{BASE_ALGORITHM} not found in CEC results.")

    # ========================================================
    # Friedman test: one block = one CEC function
    # ========================================================
    mean_matrix = summary_df.pivot_table(
        index="Function",
        columns="Algorithm",
        values="Mean",
        aggfunc="mean",
    )

    mean_matrix = mean_matrix.loc[functions, algorithms].dropna()

    friedman_stat, friedman_p = friedmanchisquare(
        *[mean_matrix[alg].values for alg in algorithms]
    )

    rank_matrix = mean_matrix.apply(
        lambda row: pd.Series(
            rankdata(row.values, method="average"),
            index=algorithms,
        ),
        axis=1,
    )

    friedman_average_rank_df = (
        rank_matrix
        .mean(axis=0)
        .reset_index()
        .rename(columns={"index": "Algorithm", 0: "AverageRank"})
        .sort_values("AverageRank")
    )

    friedman_df = pd.DataFrame([{
        "Test": "Friedman",
        "Statistic": friedman_stat,
        "PValue": friedman_p,
        "NumBlocks": len(mean_matrix),
        "NumAlgorithms": len(algorithms),
    }])

    friedman_df.to_csv(
        RESULTS_DIR / f"cec{CEC_YEAR}_friedman_function_level.csv",
        index=False,
        encoding="utf-8-sig",
    )

    friedman_average_rank_df.to_csv(
        RESULTS_DIR / f"cec{CEC_YEAR}_friedman_average_rank.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Per-function Wilcoxon
    # ========================================================
    details = []

    for func in functions:
        for alg in algorithms:
            if alg == BASE_ALGORITHM:
                continue

            base_values = (
                raw_df[
                    (raw_df["Function"] == func)
                    & (raw_df["Algorithm"] == BASE_ALGORITHM)
                ]
                .sort_values("Run")["BestValue"]
                .values
            )

            other_values = (
                raw_df[
                    (raw_df["Function"] == func)
                    & (raw_df["Algorithm"] == alg)
                ]
                .sort_values("Run")["BestValue"]
                .values
            )

            if len(base_values) != len(other_values):
                raise ValueError(f"Run count mismatch: {func}, {BASE_ALGORITHM} vs {alg}")

            try:
                stat, p_value = wilcoxon(
                    base_values,
                    other_values,
                    alternative="two-sided",
                    zero_method="wilcox",
                )
            except ValueError:
                stat = np.nan
                p_value = 1.0

            base_mean = float(np.mean(base_values))
            other_mean = float(np.mean(other_values))

            if p_value < 0.05:
                result = "Win" if base_mean < other_mean else "Loss"
            else:
                result = "NSD"

            details.append({
                "Function": func,
                "BaseAlgorithm": BASE_ALGORITHM,
                "ComparedAlgorithm": alg,
                "BaseMean": base_mean,
                "ComparedMean": other_mean,
                "Statistic": stat,
                "PValue": p_value,
                "Result": result,
            })

    details_df = pd.DataFrame(details)

    details_df.to_csv(
        RESULTS_DIR / f"cec{CEC_YEAR}_wilcoxon_per_function_details.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary_df2 = (
        details_df
        .groupby("ComparedAlgorithm")["Result"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )

    for col in ["Win", "NSD", "Loss"]:
        if col not in summary_df2.columns:
            summary_df2[col] = 0

    summary_df2 = summary_df2[["ComparedAlgorithm", "Win", "NSD", "Loss"]]

    summary_df2.to_csv(
        RESULTS_DIR / f"cec{CEC_YEAR}_wilcoxon_summary_nsd.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # LaTeX tables
    # ========================================================
    friedman_tex = []

    friedman_tex.append(r"\begin{table}[t]")
    friedman_tex.append(r"\centering")
    friedman_tex.append(rf"\caption{{Function-level Friedman test results on CEC{CEC_YEAR}}}")
    friedman_tex.append(rf"\label{{tab:cec{CEC_YEAR}_friedman}}")
    friedman_tex.append(r"\small")
    friedman_tex.append(r"\begin{tabular}{lcccc}")
    friedman_tex.append(r"\toprule")
    friedman_tex.append(r"Test & Statistic & $p$-value & Blocks & Conclusion \\")
    friedman_tex.append(r"\midrule")

    conclusion = "Significant" if friedman_p < 0.05 else "Not significant"

    friedman_tex.append(
        f"Friedman & {sci_latex(friedman_stat)} & {p_latex(friedman_p)} & "
        f"{len(mean_matrix)} & {conclusion} \\\\"
    )

    friedman_tex.append(r"\bottomrule")
    friedman_tex.append(r"\end{tabular}")
    friedman_tex.append(r"\end{table}")

    (TABLE_DIR / f"table_cec{CEC_YEAR}_friedman.tex").write_text(
        "\n".join(friedman_tex),
        encoding="utf-8",
    )

    wilcoxon_tex = []

    wilcoxon_tex.append(r"\begin{table}[t]")
    wilcoxon_tex.append(r"\centering")
    wilcoxon_tex.append(rf"\caption{{Wilcoxon signed-rank test summary on CEC{CEC_YEAR}}}")
    wilcoxon_tex.append(rf"\label{{tab:cec{CEC_YEAR}_wilcoxon}}")
    wilcoxon_tex.append(r"\small")
    wilcoxon_tex.append(r"\begin{tabular}{lccc}")
    wilcoxon_tex.append(r"\toprule")
    wilcoxon_tex.append(r"Compared Algorithm & Win & NSD & Loss \\")
    wilcoxon_tex.append(r"\midrule")

    order = [
        alg for alg in ALGORITHM_ORDER
        if alg != BASE_ALGORITHM
        and alg in list(summary_df2["ComparedAlgorithm"])
    ]

    for alg in order:
        row = summary_df2[summary_df2["ComparedAlgorithm"] == alg].iloc[0]
        wilcoxon_tex.append(
            f"{alg} & {int(row['Win'])} & {int(row['NSD'])} & {int(row['Loss'])} \\\\"
        )

    wilcoxon_tex.append(r"\bottomrule")
    wilcoxon_tex.append(r"\end{tabular}")
    wilcoxon_tex.append(r"\end{table}")

    (TABLE_DIR / f"table_cec{CEC_YEAR}_wilcoxon_summary.tex").write_text(
        "\n".join(wilcoxon_tex),
        encoding="utf-8",
    )

    print("=" * 100)
    print(f"CEC{CEC_YEAR} statistical tests completed.")
    print("=" * 100)
    print("Friedman:")
    print(friedman_df.to_string(index=False))
    print()
    print("Average rank:")
    print(friedman_average_rank_df.to_string(index=False))
    print()
    print("Wilcoxon summary:")
    print(summary_df2.to_string(index=False))
    print("=" * 100)


if __name__ == "__main__":
    main()
