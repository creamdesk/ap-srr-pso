# -*- coding: utf-8 -*-
r"""
repair_curated_workspace.py

作用：
  修补已经生成的 arpso_curated_workspace。
  主要修复：
    1. analysis_data/f23_restart_focus 为空的问题
    2. 小型 audit summary 因文件名含 raw_results/restart_details 被误跳过的问题
    3. ablation6_errors.log 因 .log 后缀被误跳过的问题

放置位置：
  算法改进\code\repair_curated_workspace.py

运行方式：
  在“算法改进”根目录运行：

  D:\Python313\python.exe code\repair_curated_workspace.py

如果你整理目录不是默认名：
  D:\Python313\python.exe code\repair_curated_workspace.py --workspace arpso_curated_workspace
"""

from __future__ import annotations

import argparse
import os
import shutil
import time
from pathlib import Path


MAX_COPY_MB = 30.0


def mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024


def mkdir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path, copied: list[str], skipped: list[str]):
    if not src.exists() or not src.is_file():
        skipped.append(f"MISSING: {src}")
        return

    if mb(src) > MAX_COPY_MB:
        skipped.append(f"TOO LARGE: {src} [{mb(src):.2f} MB]")
        return

    mkdir(dst.parent)
    shutil.copy2(src, dst)
    copied.append(f"{src} -> {dst} [{mb(dst):.2f} MB]")


def copy_tree_small(src_dir: Path, dst_dir: Path, copied: list[str], skipped: list[str], suffixes=None):
    if not src_dir.exists():
        skipped.append(f"MISSING DIR: {src_dir}")
        return

    for root, _, files in os.walk(src_dir):
        rootp = Path(root)
        for name in files:
            src = rootp / name
            if suffixes is not None and src.suffix.lower() not in suffixes:
                continue
            rel = src.relative_to(src_dir)
            dst = dst_dir / rel
            copy_file(src, dst, copied, skipped)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="项目根目录，默认当前目录")
    parser.add_argument("--workspace", default="arpso_curated_workspace", help="整理目录名")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workspace = root / args.workspace

    copied: list[str] = []
    skipped: list[str] = []

    if not workspace.exists():
        raise FileNotFoundError(f"找不到 workspace: {workspace}")

    # 1. 修复 f23_restart_focus
    copy_tree_small(
        root / "project_audit_pack" / "f23_restart_focus",
        workspace / "analysis_data" / "f23_restart_focus",
        copied,
        skipped,
        suffixes={".csv", ".txt", ".md"},
    )

    # 2. 修复 audit_data_summaries：这些是小型摘要，即使文件名含 restart_details/raw_results，也应该复制
    copy_tree_small(
        root / "project_audit_pack" / "data_summaries",
        workspace / "analysis_data" / "audit_data_summaries",
        copied,
        skipped,
        suffixes={".csv", ".txt", ".md"},
    )

    # 3. 复制 ablation6_errors.log
    copy_file(
        root / "results" / "cec2017_ablation6" / "ablation6_errors.log",
        workspace / "analysis_data" / "ablation6" / "ablation6_errors.log",
        copied,
        skipped,
    )

    # 4. 如果你之前生成过高级 ablation landscape 图，也顺手复制
    possible_landscape_files = [
        root / "arpso_ablation_figure_pack" / "ablation6_landscape_tikz_final.pdf",
        root / "arpso_ablation_figure_pack" / "ablation6_landscape_tikz_final.png",
        root / "arpso_ablation_figure_pack" / "ablation6_landscape_tikz_final.tex",
        root / "arpso_ablation_figure_pack" / "ablation6_landscape_tikz_block.tex",
    ]

    for src in possible_landscape_files:
        if src.exists():
            if src.suffix.lower() == ".pdf" or src.suffix.lower() == ".png":
                dst = workspace / "paper" / "figures" / src.name
            else:
                dst = workspace / "paper" / "figure_sources" / src.name
            copy_file(src, dst, copied, skipped)

    # 5. 写修复报告
    docs = workspace / "docs"
    mkdir(docs)

    report = []
    report.append("# REPAIR_REPORT")
    report.append("")
    report.append(f"Generated at: `{time.strftime('%Y-%m-%d %H:%M:%S')}`")
    report.append("")
    report.append("## Copied")
    report.append("")
    if copied:
        for x in copied:
            report.append(f"- `{x}`")
    else:
        report.append("- Nothing copied.")
    report.append("")
    report.append("## Skipped / Missing")
    report.append("")
    if skipped:
        for x in skipped:
            report.append(f"- `{x}`")
    else:
        report.append("- Nothing skipped.")
    report.append("")
    report.append("## Result")
    report.append("")
    report.append("The curated workspace now contains repaired analysis summaries, especially `analysis_data/f23_restart_focus` if the source audit folder exists.")
    report.append("")

    (docs / "REPAIR_REPORT.md").write_text("\n".join(report), encoding="utf-8")

    print("=" * 88)
    print("Repair finished.")
    print(f"Workspace: {workspace}")
    print(f"Copied:    {len(copied)}")
    print(f"Skipped:   {len(skipped)}")
    print(f"Report:    {docs / 'REPAIR_REPORT.md'}")
    print("=" * 88)


if __name__ == "__main__":
    main()
