# -*- coding: utf-8 -*-
r"""
revise_ablation_study_fixed.py

修复版：
  - 不再依赖 tabulate
  - 自动检测上次是否已经替换过 Ablation Study
  - 如果已经替换过，只补生成报告并可编译
  - 如果还没替换，则正常备份、生成表格、替换 Ablation Study
  - SyntaxWarning 也修掉了

放置位置：
  算法改进\code\revise_ablation_study_fixed.py

运行：
  D:\Python313\python.exe code\revise_ablation_study_fixed.py --compile
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from pathlib import Path

import pandas as pd


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required CSV not found: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def fmt_rank(x: float) -> str:
    return f"{float(x):.2f}"


def fmt_one(x: float) -> str:
    return f"{float(x):.1f}"


def fmt_two(x: float) -> str:
    return f"{float(x):.2f}"


def sci_latex(x: float) -> str:
    x = float(x)
    if x == 0:
        return "0"
    text = f"{x:.2e}"
    base, exp = text.split("e")
    exp_int = int(exp)
    return rf"{base}\times 10^{{{exp_int}}}"


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    """
    不依赖 tabulate 的简易 Markdown 表格。
    """
    rows = []
    rows.append("| " + " | ".join(columns) + " |")
    rows.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for _, row in df[columns].iterrows():
        vals = []
        for col in columns:
            val = row[col]
            if isinstance(val, float):
                if "Rank" in col:
                    vals.append(f"{val:.2f}")
                elif "Runtime" in col:
                    vals.append(f"{val:.2f}")
                else:
                    vals.append(f"{val:.1f}")
            else:
                vals.append(str(val))
        rows.append("| " + " | ".join(vals) + " |")
    return "\n".join(rows)


def choose_ablation_figure(fig_dir: Path) -> str:
    candidates = [
        "ablation6_landscape_tikz_final.pdf",
        "ablation6_average_rank.pdf",
        "ablation_bar_tikz_final.pdf",
    ]
    for name in candidates:
        if (fig_dir / name).exists():
            return name
    return "ablation6_average_rank.pdf"


def build_revised_table(workspace: Path) -> tuple[str, pd.DataFrame]:
    data_dir = workspace / "analysis_data" / "ablation6"

    rank = read_csv(data_dir / "ablation6_average_rank.csv")
    restart = read_csv(data_dir / "ablation6_restart_summary.csv")
    runtime = read_csv(data_dir / "ablation6_runtime_summary.csv")

    df = (
        rank.merge(restart, on="Algorithm", how="left")
            .merge(runtime, on="Algorithm", how="left")
    )

    df = df.sort_values(["AverageRank", "Algorithm"]).reset_index(drop=True)

    lines = []
    lines.append(r"\begin{table}[!t]")
    lines.append(r"\caption{Six-Variant Ablation Results on the CEC2017 Benchmark Suite}")
    lines.append(r"\label{tab:ablation}")
    lines.append(r"\centering")
    lines.append(r"\scriptsize")
    lines.append(r"\setlength{\tabcolsep}{3pt}")
    lines.append(r"\begin{tabular}{lrrrr}")
    lines.append(r"\toprule")
    lines.append(r"Algorithm & Avg. rank & Avg. restarts & Rest. particles & Runtime (s) \\")
    lines.append(r"\midrule")

    for _, row in df.iterrows():
        alg = str(row["Algorithm"])
        lines.append(
            f"{alg} & "
            f"{fmt_rank(row['AverageRank'])} & "
            f"{fmt_one(row['AvgRestartCount'])} & "
            f"{fmt_one(row['AvgRestartedParticles'])} & "
            f"{fmt_two(row['AvgRuntime'])} \\\\"
        )

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    lines.append("")

    return "\n".join(lines), df


def build_ablation_section(workspace: Path, df: pd.DataFrame) -> str:
    data_dir = workspace / "analysis_data" / "ablation6"
    fig_name = choose_ablation_figure(workspace / "paper" / "figures")

    friedman = read_csv(data_dir / "ablation6_friedman.csv")
    wilcoxon = read_csv(data_dir / "ablation6_wilcoxon_summary.csv")

    friedman_stat = float(friedman.loc[0, "Statistic"])
    friedman_p = float(friedman.loc[0, "PValue"])
    num_blocks = int(friedman.loc[0, "NumBlocks"])
    num_algorithms = int(friedman.loc[0, "NumAlgorithms"])

    srr = df[df["Algorithm"] == "ARPSO-SRR"].iloc[0]
    local = df[df["Algorithm"] == "ARPSO-Local"].iloc[0]

    local_particle_ratio = float(local["AvgRestartedParticles"]) / float(srr["AvgRestartedParticles"])

    w_global = wilcoxon[wilcoxon["ComparedAlgorithm"] == "ARPSO-Global"].iloc[0]
    w_local = wilcoxon[wilcoxon["ComparedAlgorithm"] == "ARPSO-Local"].iloc[0]
    w_rs = wilcoxon[wilcoxon["ComparedAlgorithm"] == "PSO-RS"].iloc[0]
    w_eis = wilcoxon[wilcoxon["ComparedAlgorithm"] == "ARPSO-EIS"].iloc[0]

    section = rf"""\subsection{{Ablation Study}}
Table~\ref{{tab:ablation}} reports the complete six-variant ablation results on the CEC2017 benchmark suite. Lower average rank indicates better overall performance. ARPSO-SRR and ARPSO-Local obtain the same best average rank of {fmt_rank(srr['AverageRank'])}, followed by ARPSO-Fixed and ARPSO-EIS. This result indicates that the proposed search-resource reallocation mechanism is competitive with the more aggressive local restart strategy while preserving the simplicity of the adaptive hybrid restart framework.

\input{{tables/table_ablation6_revised.tex}}

The restart statistics further clarify the difference between ARPSO-SRR and ARPSO-Local. Although both variants reach the best average rank, ARPSO-Local triggers {fmt_one(local['AvgRestartCount'])} restart events on average and replaces {fmt_one(local['AvgRestartedParticles'])} particles, whereas ARPSO-SRR triggers {fmt_one(srr['AvgRestartCount'])} restart events and replaces {fmt_one(srr['AvgRestartedParticles'])} particles. In other words, ARPSO-Local replaces about {local_particle_ratio:.2f} times as many particles as ARPSO-SRR. This suggests that ARPSO-SRR does not simply rely on a stronger or more aggressive restart operation; instead, it controls the restart intensity and reallocates search resources in a more economical manner.

Fig.~\ref{{fig:ablation}} visualizes the ablation comparison. The figure supports the same observation as Table~\ref{{tab:ablation}}: ARPSO-SRR achieves the best overall ranking performance together with ARPSO-Local, while avoiding the substantially larger particle replacement cost of the local restart variant.

\begin{{figure}}[!t]
    \centering
    \safeincludegraphics[width=\linewidth]{{{fig_name}}}
    \caption{{Ablation comparison of the six restart variants on the CEC2017 benchmark suite. Lower average rank indicates better performance.}}
    \label{{fig:ablation}}
\end{{figure}}

The global Friedman test also confirms that the restart design has a statistically observable influence on the overall performance. Across {num_blocks} benchmark functions and {num_algorithms} variants, the Friedman statistic is {friedman_stat:.4f} with $p={sci_latex(friedman_p)}$. The pairwise Wilcoxon summary should be interpreted conservatively. ARPSO-SRR obtains {int(w_rs['Win'])}/{int(w_rs['NSD'])}/{int(w_rs['Loss'])} win/no-significant-difference/loss counts against PSO-RS, {int(w_global['Win'])}/{int(w_global['NSD'])}/{int(w_global['Loss'])} against ARPSO-Global, {int(w_eis['Win'])}/{int(w_eis['NSD'])}/{int(w_eis['Loss'])} against ARPSO-EIS, and {int(w_local['Win'])}/{int(w_local['NSD'])}/{int(w_local['Loss'])} against ARPSO-Local. Therefore, the ablation study does not suggest that ARPSO-SRR significantly dominates all restart variants on every function. Instead, it shows that ARPSO-SRR provides a favorable balance between ranking performance and restart cost, which is consistent with the motivation of computational resource reallocation.
"""
    return section


def section_already_revised(text: str) -> bool:
    markers = [
        "complete six-variant ablation results",
        "table_ablation6_revised.tex",
        "ARPSO-Local replaces about",
        "favorable balance between ranking performance and restart cost",
    ]
    return all(m in text for m in markers[:2])


def replace_ablation_section(main_tex: Path, new_section: str) -> tuple[str, bool]:
    text = main_tex.read_text(encoding="utf-8", errors="ignore")

    start_marker = r"\subsection{Ablation Study}"
    next_marker = r"\subsection{Overall Performance}"

    start = text.find(start_marker)
    if start < 0:
        raise ValueError(r"Cannot find \subsection{Ablation Study} in main.tex")

    end = text.find(next_marker, start)
    if end < 0:
        raise ValueError(r"Cannot find next subsection \subsection{Overall Performance} after Ablation Study")

    old_section = text[start:end]

    if section_already_revised(old_section):
        return old_section, False

    revised = text[:start] + new_section.rstrip() + "\n\n" + text[end:]
    main_tex.write_text(revised, encoding="utf-8")
    return old_section, True


def compile_paper(workspace: Path) -> tuple[bool, str]:
    paper_dir = workspace / "paper"
    cmd = ["pdflatex", "-interaction=nonstopmode", "main.tex"]

    logs = []
    ok = True

    for round_idx in range(1, 3):
        try:
            result = subprocess.run(
                cmd,
                cwd=str(paper_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=180,
            )
            logs.append(f"===== pdflatex round {round_idx} | returncode={result.returncode} =====")
            logs.append(result.stdout)
            if result.returncode != 0:
                ok = False
        except Exception as e:
            ok = False
            logs.append(f"Compilation failed in round {round_idx}: {repr(e)}")
            break

    return ok, "\n".join(logs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="项目根目录，默认当前目录")
    parser.add_argument("--workspace", default="arpso_curated_workspace", help="整理后的 workspace 目录名")
    parser.add_argument("--compile", action="store_true", help="替换后自动运行 pdflatex 两遍")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace = root / args.workspace

    if not workspace.exists():
        raise FileNotFoundError(f"Workspace not found: {workspace}")

    paper_dir = workspace / "paper"
    docs_dir = workspace / "docs"
    table_dir = paper_dir / "tables"

    main_tex = paper_dir / "main.tex"
    if not main_tex.exists():
        raise FileNotFoundError(f"main.tex not found: {main_tex}")

    docs_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # 即使上次已替换，也再备份一次当前 main.tex，安全第一
    backup_path = paper_dir / f"main_before_ablation_revision_fixed_{timestamp}.tex"
    shutil.copy2(main_tex, backup_path)

    table_tex, df = build_revised_table(workspace)
    table_path = table_dir / "table_ablation6_revised.tex"
    table_path.write_text(table_tex, encoding="utf-8")

    new_section = build_ablation_section(workspace, df)
    old_section, changed = replace_ablation_section(main_tex, new_section)

    old_section_path = docs_dir / f"OLD_ABLATION_SECTION_FIXED_{timestamp}.tex"
    old_section_path.write_text(old_section, encoding="utf-8")

    report_lines = []
    report_lines.append("# ABLATION_REVISION_REPORT_FIXED")
    report_lines.append("")
    report_lines.append(f"Generated at: `{time.strftime('%Y-%m-%d %H:%M:%S')}`")
    report_lines.append("")
    report_lines.append("## Status")
    report_lines.append("")
    report_lines.append(f"- Main section changed in this run: `{changed}`")
    if not changed:
        report_lines.append("- The Ablation Study section already looked revised, so this script did not replace it again.")
    report_lines.append("")
    report_lines.append("## Files")
    report_lines.append("")
    report_lines.append(f"- Main file: `{main_tex}`")
    report_lines.append(f"- Backup file: `{backup_path}`")
    report_lines.append(f"- Old/current ablation section copy: `{old_section_path}`")
    report_lines.append(f"- Generated table: `{table_path}`")
    report_lines.append("")
    report_lines.append("## New ablation table values")
    report_lines.append("")
    report_lines.append(markdown_table(df, ["Algorithm", "AverageRank", "AvgRestartCount", "AvgRestartedParticles", "AvgRuntime"]))
    report_lines.append("")
    report_lines.append("## Main claim")
    report_lines.append("")
    report_lines.append("ARPSO-SRR and ARPSO-Local obtain the same best average rank, but ARPSO-Local uses substantially more restarted particles. The revised text frames ARPSO-SRR as a more economical computational resource reallocation strategy rather than an aggressive restart method.")
    report_lines.append("")

    if args.compile:
        ok, log_text = compile_paper(workspace)
        compile_log = docs_dir / f"ABLATION_REVISION_COMPILE_LOG_FIXED_{timestamp}.txt"
        compile_log.write_text(log_text, encoding="utf-8", errors="ignore")
        report_lines.append("## Compile result")
        report_lines.append("")
        report_lines.append(f"- Compile success: `{ok}`")
        report_lines.append(f"- Compile log: `{compile_log}`")
        report_lines.append("")

    report_path = docs_dir / "ABLATION_REVISION_REPORT_FIXED.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print("=" * 88)
    print("Ablation Study revision fixed script finished.")
    print(f"Workspace:       {workspace}")
    print(f"Main tex:        {main_tex}")
    print(f"Backup:          {backup_path}")
    print(f"Generated table: {table_path}")
    print(f"Report:          {report_path}")
    if args.compile:
        print("Compile:         see report")
    print("=" * 88)


if __name__ == "__main__":
    main()
