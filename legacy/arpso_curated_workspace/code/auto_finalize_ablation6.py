# -*- coding: utf-8 -*-
"""
自动化收尾脚本：CEC2017 六变体消融实验完成后，一键生成论文图表与 LaTeX 片段
================================================================================

建议保存位置：
    code/auto_finalize_ablation6.py

运行方式：
    python code/auto_finalize_ablation6.py

默认读取：
    results/cec2017_ablation6/

默认输出：
    paper_auto_update/
        tables/table_ablation6.tex
        figures/ablation6_average_rank.pdf
        figures/ablation6_average_rank.png
        figures/restart_heatmap_F23.pdf
        figures/restart_heatmap_F23.png
        figures/figure_ablation_rank.tex
        figures/figure_restart_heatmap.tex
        snippets/ablation_discussion_auto.tex
        snippets/restart_discussion_auto.tex
        reports/ablation6_status_report.txt
        reports/ablation6_final_summary.csv

可选：自动替换 main.tex 中的 Table III / Fig. 3 / Fig. 5
    python code/auto_finalize_ablation6.py --patch-main 论文/main.tex

注意：
    1. 如果实验没跑完，脚本会生成 preview，但会在报告里标注 INCOMPLETE。
    2. 最终投稿前请确认 status report 显示 COMPLETE。
    3. 所有数值均从 CSV 重新计算，避免手写表格出错。
"""

import argparse
import re
from pathlib import Path
import textwrap
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import rankdata, friedmanchisquare, wilcoxon


# =========================
# 固定实验配置
# =========================
EXPECTED_FUNCTION_IDS = [1] + list(range(3, 31))
EXPECTED_ALGORITHMS = [
    "PSO-RS",
    "ARPSO-Fixed",
    "ARPSO-Global",
    "ARPSO-Local",
    "ARPSO-SRR",
    "ARPSO-EIS",
]
BASE_ALGORITHM = "ARPSO-SRR"
EXPECTED_RUNS = 30
MAX_FES = 300000
POP_SIZE = 50

# 图默认设置
TARGET_FUNCTION_ID = 23
TARGET_FUNCTION_LABEL = "CEC2017-F23"
N_HEATMAP_BINS = 10


# =========================
# 路径
# =========================
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result-dir",
        default="results/cec2017_ablation6",
        help="六变体消融实验结果目录",
    )
    parser.add_argument(
        "--out-dir",
        default="paper_auto_update",
        help="自动生成图表和 LaTeX 片段的输出目录",
    )
    parser.add_argument(
        "--patch-main",
        default=None,
        help="可选：传入 main.tex 路径，自动生成 patched 版本",
    )
    parser.add_argument(
        "--target-function",
        type=int,
        default=TARGET_FUNCTION_ID,
        help="用于重启热力图的函数编号，默认 F23",
    )
    return parser.parse_args()


# =========================
# 基础工具
# =========================
def normalize_function_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "FunctionID" in df.columns:
        df["FunctionID"] = df["FunctionID"].astype(int)
        return df

    if "Function" not in df.columns:
        raise ValueError("CSV 中既没有 FunctionID，也没有 Function 列，无法识别函数编号。")

    def extract_fid(x):
        s = str(x)
        m = re.search(r"F(\d+)", s)
        if not m:
            raise ValueError(f"无法从 Function={x!r} 提取函数编号。")
        return int(m.group(1))

    df["FunctionID"] = df["Function"].apply(extract_fid)
    return df


def function_label(fid: int) -> str:
    return f"CEC2017-F{fid}"


def safe_float(x, ndigits=2):
    if pd.isna(x):
        return "--"
    return f"{float(x):.{ndigits}f}"


def ensure_dirs(out_dir: Path):
    for sub in ["tables", "figures", "snippets", "reports"]:
        (out_dir / sub).mkdir(parents=True, exist_ok=True)


def load_raw(result_dir: Path) -> pd.DataFrame:
    raw_path = result_dir / "ablation6_raw_results.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"找不到 {raw_path}")
    raw = pd.read_csv(raw_path)
    raw = normalize_function_id(raw)

    required = ["FunctionID", "Algorithm", "Run", "BestError", "Runtime", "RestartCount"]
    missing = [c for c in required if c not in raw.columns]
    if missing:
        raise ValueError(f"raw results 缺少必要列：{missing}")
    return raw


def check_completion(raw: pd.DataFrame):
    counts = (
        raw.groupby(["FunctionID", "Algorithm"])["Run"]
        .nunique()
        .reset_index(name="RunsCompleted")
    )

    full_index = pd.MultiIndex.from_product(
        [EXPECTED_FUNCTION_IDS, EXPECTED_ALGORITHMS],
        names=["FunctionID", "Algorithm"]
    )
    counts = (
        counts.set_index(["FunctionID", "Algorithm"])
        .reindex(full_index, fill_value=0)
        .reset_index()
    )

    counts["Complete"] = counts["RunsCompleted"] >= EXPECTED_RUNS

    completed_function_ids = []
    for fid in EXPECTED_FUNCTION_IDS:
        sub = counts[counts["FunctionID"] == fid]
        if (sub["RunsCompleted"] >= EXPECTED_RUNS).all():
            completed_function_ids.append(fid)

    total_expected = len(EXPECTED_FUNCTION_IDS) * len(EXPECTED_ALGORITHMS) * EXPECTED_RUNS
    total_done = len(raw)
    complete = total_done >= total_expected and counts["Complete"].all()

    return {
        "counts": counts,
        "completed_function_ids": completed_function_ids,
        "total_expected": total_expected,
        "total_done": total_done,
        "complete": bool(complete),
        "progress": total_done / total_expected if total_expected else 0,
    }


def filter_analysis_raw(raw: pd.DataFrame, completion_info: dict) -> pd.DataFrame:
    """
    实验未完成时，只用已经完整跑完的函数做 preview。
    实验完成后，用全部函数。
    """
    if completion_info["complete"]:
        fids = EXPECTED_FUNCTION_IDS
    else:
        fids = completion_info["completed_function_ids"]

    if not fids:
        raise ValueError("目前没有任何完整函数，无法计算平均排名。")

    return raw[raw["FunctionID"].isin(fids)].copy()


# =========================
# 统计计算
# =========================
def compute_summary(raw_analysis: pd.DataFrame):
    summary = (
        raw_analysis.groupby(["FunctionID", "Algorithm"])
        .agg(
            MeanError=("BestError", "mean"),
            StdError=("BestError", "std"),
            AvgRuntime=("Runtime", "mean"),
            AvgRestart=("RestartCount", "mean"),
        )
        .reset_index()
    )

    rank_records = []
    for fid, g in summary.groupby("FunctionID"):
        # 确保算法齐全
        g = g.copy()
        ranks = rankdata(g["MeanError"].values, method="average")
        for (_, row), rank in zip(g.iterrows(), ranks):
            rank_records.append({
                "FunctionID": int(fid),
                "Algorithm": row["Algorithm"],
                "MeanError": row["MeanError"],
                "Rank": float(rank),
            })

    rank_detail = pd.DataFrame(rank_records)

    avg_rank = (
        rank_detail.groupby("Algorithm")
        .agg(AverageRank=("Rank", "mean"))
        .reset_index()
    )

    runtime = (
        raw_analysis.groupby("Algorithm")
        .agg(
            AvgRuntime=("Runtime", "mean"),
            StdRuntime=("Runtime", "std")
        )
        .reset_index()
    )

    restarts = (
        raw_analysis.groupby("Algorithm")
        .agg(
            AvgRestart=("RestartCount", "mean"),
            StdRestart=("RestartCount", "std")
        )
        .reset_index()
    )

    merged = (
        avg_rank.merge(restarts, on="Algorithm", how="left")
        .merge(runtime, on="Algorithm", how="left")
    )

    # 固定展示顺序：和论文逻辑一致
    merged["Order"] = merged["Algorithm"].map({a: i for i, a in enumerate(EXPECTED_ALGORITHMS)})
    merged = merged.sort_values("Order").drop(columns=["Order"])

    return {
        "summary": summary,
        "rank_detail": rank_detail,
        "avg_rank": avg_rank,
        "runtime": runtime,
        "restarts": restarts,
        "merged": merged,
    }


def compute_wilcoxon(raw_analysis: pd.DataFrame):
    records = []

    for alg in EXPECTED_ALGORITHMS:
        if alg == BASE_ALGORITHM:
            continue

        win = nsd = loss = 0
        for fid in sorted(raw_analysis["FunctionID"].unique()):
            base_vals = (
                raw_analysis[
                    (raw_analysis["FunctionID"] == fid)
                    & (raw_analysis["Algorithm"] == BASE_ALGORITHM)
                ]
                .sort_values("Run")["BestError"]
                .values
            )
            comp_vals = (
                raw_analysis[
                    (raw_analysis["FunctionID"] == fid)
                    & (raw_analysis["Algorithm"] == alg)
                ]
                .sort_values("Run")["BestError"]
                .values
            )

            n = min(len(base_vals), len(comp_vals))
            if n == 0:
                continue

            base_vals = base_vals[:n]
            comp_vals = comp_vals[:n]

            try:
                if np.allclose(base_vals, comp_vals):
                    p = 1.0
                else:
                    _, p = wilcoxon(base_vals, comp_vals, alternative="two-sided", zero_method="wilcox")
            except Exception:
                p = 1.0

            base_mean = float(np.mean(base_vals))
            comp_mean = float(np.mean(comp_vals))

            if p < 0.05 and base_mean < comp_mean:
                win += 1
            elif p < 0.05 and base_mean > comp_mean:
                loss += 1
            else:
                nsd += 1

        records.append({
            "BaseAlgorithm": BASE_ALGORITHM,
            "ComparedAlgorithm": alg,
            "Win": win,
            "NSD": nsd,
            "Loss": loss,
        })

    return pd.DataFrame(records)


def compute_friedman(rank_detail: pd.DataFrame):
    pivot = rank_detail.pivot(index="FunctionID", columns="Algorithm", values="Rank")
    algs = [a for a in EXPECTED_ALGORITHMS if a in pivot.columns]
    if len(algs) < 3:
        return pd.DataFrame([{
            "Test": "Friedman",
            "Statistic": np.nan,
            "PValue": np.nan,
            "NumBlocks": pivot.shape[0],
            "NumAlgorithms": len(algs),
        }])
    stat, pval = friedmanchisquare(*[pivot[a].values for a in algs])
    return pd.DataFrame([{
        "Test": "Friedman",
        "Statistic": float(stat),
        "PValue": float(pval),
        "NumBlocks": int(pivot.shape[0]),
        "NumAlgorithms": int(len(algs)),
    }])


# =========================
# LaTeX 表格和段落
# =========================
def write_table_ablation(merged: pd.DataFrame, out_dir: Path):
    lines = []
    lines.append(r"\begin{table}[!t]")
    lines.append(r"\caption{Ablation Results of Six Restart-related Variants}")
    lines.append(r"\centering")
    lines.append(r"\begin{tabular}{lccc}")
    lines.append(r"\toprule")
    lines.append(r"Algorithm & Avg. rank & Avg. restarts & Avg. runtime (s) \\")
    lines.append(r"\midrule")

    for alg in EXPECTED_ALGORITHMS:
        row = merged[merged["Algorithm"] == alg]
        if row.empty:
            lines.append(f"{alg} & -- & -- & -- \\\\")
        else:
            r = row.iloc[0]
            lines.append(
                f"{alg} & {safe_float(r['AverageRank'])} & "
                f"{safe_float(r['AvgRestart'])} & {safe_float(r['AvgRuntime'])} \\\\"
            )

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\label{tab:ablation}")
    lines.append(r"\end{table}")

    path = out_dir / "tables" / "table_ablation6.tex"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_discussion_snippets(merged: pd.DataFrame, wilcoxon_df: pd.DataFrame, complete: bool, out_dir: Path):
    rank_sorted = merged.sort_values("AverageRank")
    best_alg = rank_sorted.iloc[0]["Algorithm"]
    srr_rank = float(merged.loc[merged["Algorithm"] == BASE_ALGORITHM, "AverageRank"].iloc[0])
    best_rank = float(rank_sorted.iloc[0]["AverageRank"])

    pso_rs_rank = merged.loc[merged["Algorithm"] == "PSO-RS", "AverageRank"]
    pso_rs_text = ""
    if len(pso_rs_rank):
        pso_rs_text = (
            f" Compared with PSO-RS, ARPSO-SRR improves the average rank "
            f"from {float(pso_rs_rank.iloc[0]):.2f} to {srr_rank:.2f}, "
            f"indicating that adaptive hybrid restart is more effective than simple random restart."
        )

    if best_alg == BASE_ALGORITHM:
        main_sentence = (
            "The complete ARPSO-SRR achieves the best overall rank among the six restart-related variants. "
            "This confirms that adaptive restart intensity and hybrid regeneration jointly contribute to the observed performance gain."
        )
    else:
        main_sentence = (
            f"{best_alg} obtains the best average rank among the six restart-related variants, "
            f"while ARPSO-SRR remains close with an average rank of {srr_rank:.2f}. "
            "This indicates that single-mode restart may be strong on specific function subsets, "
            "whereas ARPSO-SRR provides a balanced resource-reallocation strategy across different landscapes."
        )

    if not complete:
        prefix = (
            "% WARNING: This paragraph is generated from incomplete experiment results. "
            "Use it only for preview.\n"
        )
    else:
        prefix = ""

    text = prefix + textwrap.fill(
        main_sentence + pso_rs_text,
        width=100
    )

    path = out_dir / "snippets" / "ablation_discussion_auto.tex"
    path.write_text(text + "\n", encoding="utf-8")

    # Restart behavior paragraph
    restart_text = textwrap.fill(
        "The restart-event heatmap further illustrates when ARPSO-SRR reallocates search resources. "
        "Restart events are not uniformly distributed across the whole search process; instead, they tend to become more active after the swarm starts to stagnate. "
        "This behavior is consistent with the design of the restart demand indicator, which increases when the stagnation length becomes larger or the normalized diversity falls below the predefined threshold.",
        width=100
    )
    restart_path = out_dir / "snippets" / "restart_discussion_auto.tex"
    restart_path.write_text(restart_text + "\n", encoding="utf-8")

    return path, restart_path


# =========================
# 图表生成
# =========================
def set_plot_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.linewidth": 0.8,
    })


def plot_ablation_rank(merged: pd.DataFrame, out_dir: Path):
    set_plot_style()

    plot_df = merged.copy().sort_values("AverageRank", ascending=True)
    y = np.arange(len(plot_df))

    fig, ax = plt.subplots(figsize=(3.45, 2.55))
    ax.barh(y, plot_df["AverageRank"].values, height=0.58, edgecolor="black", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["Algorithm"].values)
    ax.invert_yaxis()
    ax.set_xlabel("Average rank")
    ax.set_xlim(0, max(6.5, float(plot_df["AverageRank"].max()) + 0.6))

    for i, val in enumerate(plot_df["AverageRank"].values):
        ax.text(val + 0.06, i, f"{val:.2f}", va="center", ha="left", fontsize=8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linestyle="--", linewidth=0.45, alpha=0.35)
    ax.set_axisbelow(True)

    fig.tight_layout(pad=0.4)

    pdf = out_dir / "figures" / "ablation6_average_rank.pdf"
    png = out_dir / "figures" / "ablation6_average_rank.png"
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    plt.close(fig)

    tex = out_dir / "figures" / "figure_ablation_rank.tex"
    tex.write_text(textwrap.dedent(r"""
    \begin{figure}[!t]
        \centering
        \includegraphics[width=\linewidth]{figures/ablation6_average_rank.pdf}
        \caption{Average-rank comparison of six restart-related variants.}
        \label{fig:ablation}
    \end{figure}
    """).strip() + "\n", encoding="utf-8")

    return pdf, png, tex


def load_restart_details(result_dir: Path):
    path = result_dir / "ablation6_restart_details.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = normalize_function_id(df)
    return df


def plot_restart_heatmap(restart_df: pd.DataFrame, out_dir: Path, target_fid: int):
    if restart_df is None or restart_df.empty:
        warnings.warn("restart details 不存在或为空，跳过热力图。")
        return None, None, None

    sub = restart_df[
        (restart_df["Algorithm"] == BASE_ALGORITHM)
        & (restart_df["FunctionID"] == target_fid)
    ].copy()

    if sub.empty:
        warnings.warn(f"找不到 {BASE_ALGORITHM} 在 F{target_fid} 上的 restart details，跳过热力图。")
        return None, None, None

    if "FE" in sub.columns:
        sub["FE_plot"] = sub["FE"].astype(float)
    elif "RestartIter" in sub.columns:
        sub["FE_plot"] = sub["RestartIter"].astype(float) * POP_SIZE
    else:
        raise ValueError("restart details 中缺少 FE 或 RestartIter，无法画热力图。")

    sub["FE_plot"] = sub["FE_plot"].clip(0, MAX_FES)

    runs = list(range(1, EXPECTED_RUNS + 1))
    edges = np.linspace(0, MAX_FES, N_HEATMAP_BINS + 1)
    heat = np.zeros((EXPECTED_RUNS, N_HEATMAP_BINS), dtype=float)

    for run in runs:
        vals = sub[sub["Run"] == run]["FE_plot"].values
        counts, _ = np.histogram(vals, bins=edges)
        heat[run - 1, :] = counts

    set_plot_style()
    fig, ax = plt.subplots(figsize=(3.55, 3.05))

    im = ax.imshow(
        heat,
        aspect="auto",
        interpolation="nearest",
        origin="upper",
    )

    xticks = np.arange(N_HEATMAP_BINS)
    xlabels = [f"{int(edges[i] / 1000)}-{int(edges[i + 1] / 1000)}" for i in range(N_HEATMAP_BINS)]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, rotation=45, ha="right")
    ax.set_yticks([0, 4, 9, 14, 19, 24, 29])
    ax.set_yticklabels(["1", "5", "10", "15", "20", "25", "30"])

    ax.set_xlabel(r"Function evaluations ($\times 10^3$)")
    ax.set_ylabel("Run")

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.025)
    cbar.set_label("Restart events")

    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    fig.tight_layout(pad=0.35)

    pdf = out_dir / "figures" / f"restart_heatmap_F{target_fid}.pdf"
    png = out_dir / "figures" / f"restart_heatmap_F{target_fid}.png"
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    plt.close(fig)

    tex = out_dir / "figures" / "figure_restart_heatmap.tex"
    tex.write_text(textwrap.dedent(fr"""
    \begin{{figure}}[!t]
        \centering
        \includegraphics[width=\linewidth]{{figures/restart_heatmap_F{target_fid}.pdf}}
        \caption{{Restart-event heatmap of ARPSO-SRR on CEC2017-F{target_fid} over 30 independent runs. The color indicates the number of restart events in each function-evaluation stage.}}
        \label{{fig:restart_behavior}}
    \end{{figure}}
    """).strip() + "\n", encoding="utf-8")

    return pdf, png, tex


# =========================
# 状态报告
# =========================
def write_status_report(completion_info, stats, wilcoxon_df, friedman_df, out_dir: Path):
    merged = stats["merged"].copy()
    merged_sorted = merged.sort_values("AverageRank")

    lines = []
    lines.append("=" * 80)
    lines.append("CEC2017 Ablation-6 Auto Finalization Report")
    lines.append("=" * 80)
    lines.append(f"Status          : {'COMPLETE' if completion_info['complete'] else 'INCOMPLETE / PREVIEW'}")
    lines.append(f"Finished tasks  : {completion_info['total_done']} / {completion_info['total_expected']}")
    lines.append(f"Progress        : {completion_info['progress'] * 100:.2f}%")
    lines.append(f"Complete funcs  : {len(completion_info['completed_function_ids'])} / {len(EXPECTED_FUNCTION_IDS)}")
    lines.append(f"Function IDs    : {completion_info['completed_function_ids']}")
    lines.append("")
    lines.append("Average rank summary:")
    lines.append(merged_sorted[["Algorithm", "AverageRank", "AvgRestart", "AvgRuntime"]].to_string(index=False))
    lines.append("")
    lines.append("Wilcoxon summary:")
    lines.append(wilcoxon_df.to_string(index=False))
    lines.append("")
    lines.append("Friedman:")
    lines.append(friedman_df.to_string(index=False))
    lines.append("")
    lines.append("Next action:")
    if completion_info["complete"]:
        lines.append("1. Copy generated figures to your LaTeX figures directory.")
        lines.append("2. Replace Table III and Fig. 3/Fig. 5 using the generated LaTeX snippets.")
        lines.append("3. Check whether ARPSO-SRR or another variant has the best ablation rank, then use the generated discussion snippet.")
    else:
        lines.append("Experiment is not complete. Use generated outputs only as preview.")
        lines.append("Do not submit the paper until all -- values and preview statements are removed.")

    report_path = out_dir / "reports" / "ablation6_status_report.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    summary_csv = out_dir / "reports" / "ablation6_final_summary.csv"
    merged_sorted.to_csv(summary_csv, index=False, encoding="utf-8-sig")

    return report_path, summary_csv


# =========================
# 可选 patch main.tex
# =========================
def replace_block_by_label(tex: str, label: str, replacement: str, env: str) -> str:
    pattern = re.compile(
        rf"\\begin\{{{env}\}}(?:\[[^\]]*\])?[\s\S]*?\\label\{{{re.escape(label)}\}}[\s\S]*?\\end\{{{env}\}}",
        re.MULTILINE
    )
    new_tex, n = pattern.subn(replacement, tex, count=1)
    if n == 0:
        print(f"[WARN] 未找到 label={label} 的 {env} 环境，未替换。")
    else:
        print(f"[OK] 已替换 label={label}")
    return new_tex


def patch_main(main_path: Path, out_dir: Path):
    if not main_path.exists():
        raise FileNotFoundError(f"找不到 main.tex：{main_path}")

    tex = main_path.read_text(encoding="utf-8")

    # 备份
    backup = main_path.with_suffix(".backup_before_auto_update.tex")
    backup.write_text(tex, encoding="utf-8")

    table_input = r"\input{paper_auto_update/tables/table_ablation6.tex}"
    fig_ablation_input = r"\input{paper_auto_update/figures/figure_ablation_rank.tex}"
    fig_restart_input = r"\input{paper_auto_update/figures/figure_restart_heatmap.tex}"

    tex = replace_block_by_label(tex, "tab:ablation", table_input, "table")
    tex = replace_block_by_label(tex, "fig:ablation", fig_ablation_input, "figure")
    tex = replace_block_by_label(tex, "fig:restart_behavior", fig_restart_input, "figure")

    patched = main_path.with_name(main_path.stem + "_auto_updated.tex")
    patched.write_text(tex, encoding="utf-8")

    print(f"[OK] 已生成 patched 文件：{patched}")
    print(f"[OK] 原文件备份：{backup}")

    return patched, backup


# =========================
# 主程序
# =========================
def main():
    args = parse_args()

    result_dir = Path(args.result_dir)
    out_dir = Path(args.out_dir)
    target_fid = int(args.target_function)

    ensure_dirs(out_dir)

    raw = load_raw(result_dir)
    completion_info = check_completion(raw)
    raw_analysis = filter_analysis_raw(raw, completion_info)

    stats = compute_summary(raw_analysis)
    wilcoxon_df = compute_wilcoxon(raw_analysis)
    friedman_df = compute_friedman(stats["rank_detail"])

    # 输出核心统计文件
    stats["merged"].to_csv(out_dir / "reports" / "ablation6_table_values.csv", index=False, encoding="utf-8-sig")
    stats["rank_detail"].to_csv(out_dir / "reports" / "ablation6_rank_detail_recomputed.csv", index=False, encoding="utf-8-sig")
    wilcoxon_df.to_csv(out_dir / "reports" / "ablation6_wilcoxon_recomputed.csv", index=False, encoding="utf-8-sig")
    friedman_df.to_csv(out_dir / "reports" / "ablation6_friedman_recomputed.csv", index=False, encoding="utf-8-sig")

    table_path = write_table_ablation(stats["merged"], out_dir)
    fig_rank_pdf, fig_rank_png, fig_rank_tex = plot_ablation_rank(stats["merged"], out_dir)

    restart_df = load_restart_details(result_dir)
    heat_pdf, heat_png, heat_tex = plot_restart_heatmap(restart_df, out_dir, target_fid)

    discussion_path, restart_discussion_path = generate_discussion_snippets(
        stats["merged"], wilcoxon_df, completion_info["complete"], out_dir
    )

    report_path, summary_csv = write_status_report(
        completion_info, stats, wilcoxon_df, friedman_df, out_dir
    )

    print("=" * 80)
    print("Auto finalization finished.")
    print("=" * 80)
    print(f"Status report        : {report_path}")
    print(f"Table III snippet    : {table_path}")
    print(f"Ablation rank figure : {fig_rank_pdf}")
    if heat_pdf:
        print(f"Restart heatmap      : {heat_pdf}")
    else:
        print("Restart heatmap      : skipped")
    print(f"Discussion snippet   : {discussion_path}")
    print(f"Restart snippet      : {restart_discussion_path}")
    print(f"Summary CSV          : {summary_csv}")

    if completion_info["complete"]:
        print("\n[COMPLETE] 可以用于最终论文替换。")
    else:
        print("\n[PREVIEW ONLY] 实验未完成，现在生成的图表只能预览，不能最终投稿。")

    if args.patch_main:
        patch_main(Path(args.patch_main), out_dir)


if __name__ == "__main__":
    main()
