# -*- coding: utf-8 -*-
r"""
curate_arpso_workspace_final.py

把“算法改进”项目整理成你指定的最终结构：

arpso_curated_workspace
├─ paper
│  ├─ main.tex
│  ├─ main.pdf
│  ├─ IEEEtran.cls
│  ├─ figures
│  ├─ figure_sources
│  ├─ tables
│  └─ old_versions
├─ analysis_data
│  ├─ ablation6
│  ├─ cec_main
│  ├─ audit_data_summaries
│  ├─ f23_restart_focus
│  ├─ csv_schemas
│  └─ csv_heads
├─ code
├─ docs
│  ├─ FINAL_FILE_DECISION.md
│  ├─ NEXT_REVISION_PLAN.md
│  └─ PROJECT_AUDIT_REPORT.md
└─ compile_paper.bat

特点：
  - 只复制，不移动，不删除原文件
  - 自动跳过 raw_results / restart_details / curve_records 等超大原始 CSV
  - 默认选择 论文\main.tex 作为最终主论文
  - 自动生成 docs 说明文件和 compile_paper.bat

用法：
  1. 把本文件放到：算法改进\code\curate_arpso_workspace_final.py
  2. 在“算法改进”根目录运行：
     D:\Python313\python.exe code\curate_arpso_workspace_final.py --overwrite
  3. 如果要压缩：
     D:\Python313\python.exe code\curate_arpso_workspace_final.py --overwrite --zip
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path


OUT_NAME = "arpso_curated_workspace"
MAX_COPY_MB = 30.0

SKIP_SUFFIXES = {".aux", ".log", ".out", ".toc", ".gz", ".pyc"}
HEAVY_KEYWORDS = [
    "raw_results",
    "restart_details",
    "curve_records",
    "full_parallel_checkpoint",
    ".synctex",
]
IGNORE_DIRS = {
    "__pycache__", ".git", ".idea", ".vscode",
    "arpso_curated_workspace",
    "arpso_paper_clean_workspace",
    "project_audit_pack",
    "upload_pack_for_chat",
    "upload_pack_fast_for_chat",
}


def p(msg: str = ""):
    print(msg, flush=True)


def bar(i: int, n: int, width: int = 26) -> str:
    if n <= 0:
        return "[" + "?" * width + "]"
    r = min(max(i / n, 0), 1)
    f = int(width * r)
    return "[" + "#" * f + "-" * (width - f) + f"] {r * 100:6.2f}%"


def inline(msg: str):
    sys.stdout.write("\r" + msg[:180].ljust(180))
    sys.stdout.flush()


def endl():
    sys.stdout.write("\n")
    sys.stdout.flush()


def mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024


def mkdir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def should_skip(path: Path, max_copy_mb: float) -> tuple[bool, str]:
    low = str(path).replace("\\", "/").lower()
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True, f"skip suffix {path.suffix}"
    if any(k.lower() in low for k in HEAVY_KEYWORDS):
        return True, "heavy raw/intermediate file"
    if path.exists() and path.is_file() and mb(path) > max_copy_mb:
        return True, f"too large: {mb(path):.2f} MB > {max_copy_mb:.2f} MB"
    return False, ""


class Recorder:
    def __init__(self):
        self.copied = []
        self.skipped = []
        self.missing = []

    def add_copied(self, cat: str, src: Path, dst: Path, root: Path, out: Path):
        self.copied.append({
            "category": cat,
            "src": rel(src, root),
            "dst": rel(dst, out),
            "size_mb": f"{mb(dst):.4f}",
        })

    def add_skipped(self, cat: str, src: Path, reason: str, root: Path):
        self.skipped.append({
            "category": cat,
            "src": rel(src, root),
            "reason": reason,
            "size_mb": f"{mb(src):.4f}" if src.exists() and src.is_file() else "",
        })

    def add_missing(self, cat: str, item: str):
        self.missing.append({"category": cat, "path": item})


def unique_dst(dst: Path) -> Path:
    if not dst.exists():
        return dst
    for i in range(2, 1000):
        cand = dst.with_name(f"{dst.stem}_{i}{dst.suffix}")
        if not cand.exists():
            return cand
    raise RuntimeError(f"Too many duplicate files: {dst}")


def copy_one(
    src: Path,
    dst: Path,
    root: Path,
    out: Path,
    rec: Recorder,
    cat: str,
    max_copy_mb: float,
    overwrite: bool = False,
    allow_heavy: bool = False,
):
    if not src.exists():
        rec.add_missing(cat, str(src))
        return None
    if not src.is_file():
        rec.add_skipped(cat, src, "not a file", root)
        return None
    if not allow_heavy:
        skip, reason = should_skip(src, max_copy_mb)
        if skip:
            rec.add_skipped(cat, src, reason, root)
            return None

    mkdir(dst.parent)
    final = dst if overwrite else unique_dst(dst)
    shutil.copy2(src, final)
    rec.add_copied(cat, src, final, root, out)
    return final


def copy_first(root: Path, candidates: list[str], dst: Path, out: Path, rec: Recorder, cat: str, max_copy_mb: float):
    for c in candidates:
        src = root / c
        if src.exists():
            return copy_one(src, dst, root, out, rec, cat, max_copy_mb, overwrite=True)
    rec.add_missing(cat, " | ".join(candidates))
    return None


def glob_files(root: Path, patterns: list[str]) -> list[Path]:
    seen = set()
    files = []
    for pat in patterns:
        for f in root.glob(pat):
            if f.is_file() and f not in seen:
                seen.add(f)
                files.append(f)
    return sorted(files)


def copy_globs(
    root: Path,
    patterns: list[str],
    dst_dir: Path,
    out: Path,
    rec: Recorder,
    cat: str,
    max_copy_mb: float,
    suffixes: set[str] | None = None,
    keywords: list[str] | None = None,
):
    files = glob_files(root, patterns)
    selected = []
    for f in files:
        if suffixes and f.suffix.lower() not in suffixes:
            continue
        if keywords:
            low = rel(f, root).lower()
            if not any(k.lower() in low for k in keywords):
                continue
        selected.append(f)

    mkdir(dst_dir)
    total = len(selected)
    for i, src in enumerate(selected, 1):
        copy_one(src, dst_dir / src.name, root, out, rec, cat, max_copy_mb)
        inline(f"      {cat}: {bar(i, total)} | {i}/{total} | {src.name}")
    if total:
        endl()


def copy_tree(
    root: Path,
    src_rel: str,
    dst_dir: Path,
    out: Path,
    rec: Recorder,
    cat: str,
    max_copy_mb: float,
    suffixes: set[str] | None = None,
    keywords: list[str] | None = None,
    keep_subdirs: bool = False,
):
    src_dir = root / src_rel
    if not src_dir.exists():
        rec.add_missing(cat, src_rel)
        return

    files = []
    for cur, dirs, names in os.walk(src_dir):
        curp = Path(cur)
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        for name in names:
            f = curp / name
            if suffixes and f.suffix.lower() not in suffixes:
                continue
            low = rel(f, root).lower()
            if keywords and not any(k.lower() in low for k in keywords):
                continue
            files.append(f)

    total = len(files)
    for i, src in enumerate(files, 1):
        if keep_subdirs:
            dst = dst_dir / src.relative_to(src_dir)
        else:
            dst = dst_dir / src.name
        copy_one(src, dst, root, out, rec, cat, max_copy_mb)
        inline(f"      {cat}: {bar(i, total)} | {i}/{total} | {src.name}")
    if total:
        endl()


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    mkdir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def make_dirs(out: Path):
    for d in [
        "paper/figures",
        "paper/figure_sources",
        "paper/tables",
        "paper/old_versions",
        "analysis_data/ablation6",
        "analysis_data/cec_main",
        "analysis_data/audit_data_summaries",
        "analysis_data/f23_restart_focus",
        "analysis_data/csv_schemas",
        "analysis_data/csv_heads",
        "code",
        "docs",
    ]:
        mkdir(out / d)


def curate_paper(root: Path, out: Path, rec: Recorder, max_copy_mb: float):
    p("Step 1/7: 整理 paper 主文件")
    copy_first(root, ["论文/main.tex", "arpso_paper_clean_workspace/01_manuscript/main.tex",
                      "arpso_real_data_updated_latex_pack/main_ei_arpso_srr_real_data.tex"],
               out / "paper/main.tex", out, rec, "paper_main", max_copy_mb)
    copy_first(root, ["论文/main.pdf", "arpso_paper_clean_workspace/01_manuscript/main.pdf",
                      "arpso_real_data_updated_latex_pack/main_ei_arpso_srr_real_data.pdf"],
               out / "paper/main.pdf", out, rec, "paper_pdf", max_copy_mb)
    copy_first(root, ["论文/IEEEtran.cls", "arpso_paper_clean_workspace/01_manuscript/IEEEtran.cls", "IEEEtran.cls"],
               out / "paper/IEEEtran.cls", out, rec, "ieeetran", max_copy_mb)

    old = [
        "arpso_real_data_updated_latex_pack/main_ei_arpso_srr_real_data.tex",
        "arpso_real_data_updated_latex_pack/main_ei_arpso_srr_real_data.pdf",
        "arpso_all_figures_final_pack/algorithm_block_for_main.tex",
        "arpso_paper_clean_workspace/01_manuscript/alternative_versions/main_ei_arpso_srr_real_data.tex",
        "arpso_paper_clean_workspace/01_manuscript/alternative_versions/main_ei_arpso_srr_real_data.pdf",
    ]
    for item in old:
        src = root / item
        if src.exists():
            copy_one(src, out / "paper/old_versions" / src.name, root, out, rec, "old_versions", max_copy_mb)


def curate_figures(root: Path, out: Path, rec: Recorder, max_copy_mb: float):
    p("Step 2/7: 整理 figures / figure_sources")
    copy_globs(
        root,
        [
            "figures/*",
            "论文/figures/*",
            "paper_auto_update/figures/*",
            "paper_figures/*",
            "arpso_ablation_figure_pack/*.pdf",
            "arpso_ablation_figure_pack/*.png",
            "arpso_real_data_updated_latex_pack/*_final.pdf",
            "arpso_all_figures_final_pack/*_final.pdf",
        ],
        out / "paper/figures",
        out, rec, "figures", max_copy_mb,
        suffixes={".pdf", ".png", ".jpg", ".jpeg", ".eps"},
    )

    copy_globs(
        root,
        [
            "figures/*.txt",
            "paper_auto_update/figures/*.tex",
            "arpso_ablation_figure_pack/*.tex",
            "arpso_real_data_updated_latex_pack/*_final.tex",
            "arpso_real_data_updated_latex_pack/algorithm_block_for_main.tex",
            "arpso_all_figures_final_pack/*.tex",
            "code/生成论文图表.py",
        ],
        out / "paper/figure_sources",
        out, rec, "figure_sources", max_copy_mb,
        suffixes={".tex", ".txt", ".py"},
    )


def curate_tables(root: Path, out: Path, rec: Recorder, max_copy_mb: float):
    p("Step 3/7: 整理 tables")
    copy_globs(
        root,
        ["tables/*.tex", "paper_tables/*.tex", "论文/tables/*.tex",
         "paper_auto_update/tables/*.tex", "arpso_paper_clean_workspace/03_tables/**/*.tex"],
        out / "paper/tables",
        out, rec, "tables", max_copy_mb,
        suffixes={".tex"},
    )


def curate_analysis(root: Path, out: Path, rec: Recorder, max_copy_mb: float):
    p("Step 4/7: 整理 analysis_data")

    ablation_keywords = [
        "average_rank", "friedman", "group_average_rank", "mean_curves", "rank_detail",
        "restart_summary", "runtime_summary", "summary_results", "wilcoxon",
        "errors", "final_summary", "table_values", "status_report",
    ]
    cec_keywords = [
        "average_rank", "friedman", "mean_curves", "rank_detail", "restart_summary",
        "runtime_summary", "summary_results", "wilcoxon",
    ]

    copy_tree(root, "results/cec2017_ablation6", out / "analysis_data/ablation6",
              out, rec, "analysis_ablation6", max_copy_mb,
              suffixes={".csv", ".txt", ".log"}, keywords=ablation_keywords, keep_subdirs=False)
    copy_tree(root, "paper_auto_update/reports", out / "analysis_data/ablation6/paper_auto_update_reports",
              out, rec, "analysis_ablation6_reports", max_copy_mb,
              suffixes={".csv", ".txt"}, keywords=ablation_keywords, keep_subdirs=False)
    copy_tree(root, "results/cec", out / "analysis_data/cec_main",
              out, rec, "analysis_cec_main", max_copy_mb,
              suffixes={".csv", ".txt"}, keywords=cec_keywords, keep_subdirs=False)

    copy_tree(root, "project_audit_pack/data_summaries", out / "analysis_data/audit_data_summaries",
              out, rec, "audit_summaries", max_copy_mb,
              suffixes={".csv", ".txt", ".md"}, keep_subdirs=True)
    copy_tree(root, "project_audit_pack/f23_restart_focus", out / "analysis_data/f23_restart_focus",
              out, rec, "f23_restart_focus", max_copy_mb,
              suffixes={".csv", ".txt", ".md"}, keep_subdirs=True)
    copy_tree(root, "project_audit_pack/csv_schemas", out / "analysis_data/csv_schemas",
              out, rec, "csv_schemas", max_copy_mb,
              suffixes={".csv", ".txt"}, keep_subdirs=True)
    copy_tree(root, "project_audit_pack/csv_heads", out / "analysis_data/csv_heads",
              out, rec, "csv_heads", max_copy_mb,
              suffixes={".csv", ".txt"}, keep_subdirs=True)

    for item in ["csv_catalog.csv", "file_inventory.csv", "top_100_largest_files.csv", "file_size_by_suffix.csv"]:
        src = root / "project_audit_pack" / item
        if src.exists():
            copy_one(src, out / "analysis_data" / item, root, out, rec, "analysis_catalog", max_copy_mb)


def curate_code(root: Path, out: Path, rec: Recorder, max_copy_mb: float):
    p("Step 5/7: 整理 code")
    names = [
        "auto_finalize_ablation6.py", "benchmarks.py", "cec_adapter.py", "common.py",
        "优化算法.py", "权重敏感性分析.py", "消融实验.py", "生成论文图表.py",
        "统计检验.py", "统计检验_CEC.py", "运行CEC2017消融实验_6variants.py",
        "运行CEC实验.py", "运行CEC实验_并行版.py", "运行实验.py",
        "arpso_project_auditor.py", "organize_arpso_paper_files.py",
        "curate_arpso_workspace_final.py", "make_upload_pack_fast_progress.py",
    ]
    for name in names:
        src = root / "code" / name
        if src.exists():
            copy_one(src, out / "code" / name, root, out, rec, "code", max_copy_mb)
    copy_tree(root, "code", out / "code/all_py_backup", out, rec, "code_all_py",
              max_copy_mb, suffixes={".py"}, keep_subdirs=False)


def write_docs(root: Path, out: Path, rec: Recorder, max_copy_mb: float):
    p("Step 6/7: 生成 docs 和 compile_paper.bat")
    docs = out / "docs"
    mkdir(docs)

    # PROJECT_AUDIT_REPORT.md
    copied = copy_first(
        root,
        ["project_audit_pack/PROJECT_AUDIT_REPORT.md",
         "arpso_paper_clean_workspace/07_audit_reference/PROJECT_AUDIT_REPORT.md"],
        docs / "PROJECT_AUDIT_REPORT.md",
        out, rec, "docs", max_copy_mb,
    )
    if copied is None:
        (docs / "PROJECT_AUDIT_REPORT.md").write_text(
            "# PROJECT_AUDIT_REPORT\n\nNo previous audit report found.\n",
            encoding="utf-8",
        )

    final_decision = """# FINAL_FILE_DECISION

## Final manuscript

Use only:

```text
paper/main.tex
```

This file is copied from:

```text
论文/main.tex
```

Do not edit multiple `main.tex` versions in parallel.

## Final figures

Use final figure files from:

```text
paper/figures/
```

Editable TikZ/source files are kept in:

```text
paper/figure_sources/
```

Recommended final figures:

```text
framework_tikz_final.pdf
algorithm_summary_tikz_final.pdf
ablation6_landscape_tikz_final.pdf
convergence_curve_tikz_final.pdf
restart_behavior_tikz_final.pdf
```

## Final tables

Use:

```text
paper/tables/
```

Recommended tables:

```text
table_ablation6.tex
table_cec2017_friedman.tex
table_cec2017_wilcoxon_summary.tex
```

## Data rule

Do not place huge raw CSV files into `paper/`.

Use summarized data from:

```text
analysis_data/
```

Huge files intentionally excluded:

```text
ablation6_restart_details.csv
ablation6_raw_results.csv
ablation6_curve_records.csv
cec2017_raw_results.csv
full_parallel_checkpoint_*.csv
```
"""
    (docs / "FINAL_FILE_DECISION.md").write_text(final_decision, encoding="utf-8")

    next_plan = """# NEXT_REVISION_PLAN

## Step 1: Compile the curated manuscript

Run:

```text
compile_paper.bat
```

If compilation fails, first check figure/table paths in `paper/main.tex`.

## Step 2: Rewrite Ablation Study

Core claim:

```text
ARPSO-SRR and ARPSO-Local obtain the best average rank.
ARPSO-Local uses substantially more restarted particles.
ARPSO-SRR therefore provides comparable ranking performance with a more economical restart behavior.
```

Avoid claiming:

```text
SRR significantly beats all variants.
SRR is best on every function.
```

## Step 3: Rewrite Results and Discussion

Recommended structure:

```text
A. Ablation Study
B. Overall Performance on CEC2017
C. Convergence and Restart Behavior
D. Statistical Analysis
```

Use conservative wording:

```text
competitive
stable improvement
more economical search resource reallocation
```

Avoid:

```text
state-of-the-art
overall best
significantly better than all competitors
```

## Step 4: Final submission package

Final submission should contain only:

```text
main.tex
IEEEtran.cls
figures/*.pdf
tables/*.tex
refs.bib if used
```

Do not submit:

```text
analysis_data/
code/
docs/
old_versions/
raw CSV files
```
"""
    (docs / "NEXT_REVISION_PLAN.md").write_text(next_plan, encoding="utf-8")

    bat = r"""@echo off
chcp 65001 >nul
cd /d "%~dp0paper"

echo ============================================
echo Compiling ARPSO paper with pdflatex
echo Working directory: %cd%
echo ============================================

pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

echo.
echo Done. Output should be paper\main.pdf
pause
"""
    (out / "compile_paper.bat").write_text(bat, encoding="utf-8")


def write_tree(out: Path):
    lines = []
    for cur, dirs, files in os.walk(out):
        curp = Path(cur)
        r = curp.relative_to(out)
        level = 0 if str(r) == "." else len(r.parts)
        indent = "  " * level
        lines.append(f"{indent}{r if str(r) != '.' else out.name}/")
        for name in sorted(files):
            f = curp / name
            try:
                lines.append(f"{indent}  {name} [{mb(f):.2f} MB]")
            except OSError:
                lines.append(f"{indent}  {name}")
    (out / "docs/WORKSPACE_TREE.txt").write_text("\n".join(lines), encoding="utf-8")


def write_manifest(root: Path, out: Path, rec: Recorder):
    p("Step 7/7: 生成 manifest")
    docs = out / "docs"
    write_csv(docs / "COPIED_FILES.csv", rec.copied, ["category", "src", "dst", "size_mb"])
    write_csv(docs / "SKIPPED_FILES.csv", rec.skipped, ["category", "src", "reason", "size_mb"])
    write_csv(docs / "MISSING_FILES.csv", rec.missing, ["category", "path"])

    total = 0.0
    for x in rec.copied:
        try:
            total += float(x["size_mb"])
        except Exception:
            pass

    summary = f"""# CURATED_WORKSPACE_SUMMARY

Generated at: `{time.strftime('%Y-%m-%d %H:%M:%S')}`

Source project:

```text
{root}
```

Curated workspace:

```text
{out}
```

## Summary

- Copied files: **{len(rec.copied)}**
- Skipped files: **{len(rec.skipped)}**
- Missing paths: **{len(rec.missing)}**
- Total copied size: **{total:.2f} MB**

## Main decision

Use:

```text
paper/main.tex
```

as the only final manuscript.

## Compile

Run:

```text
compile_paper.bat
```

or:

```powershell
cd paper
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```
"""
    (docs / "CURATED_WORKSPACE_SUMMARY.md").write_text(summary, encoding="utf-8")
    write_tree(out)


def zip_out(out: Path):
    zpath = out.with_suffix(".zip")
    if zpath.exists():
        zpath.unlink()

    files = [f for f in out.rglob("*") if f.is_file()]
    total = len(files)
    p("开始压缩 ...")
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for i, f in enumerate(files, 1):
            zf.write(f, f.relative_to(out.parent))
            inline(f"  zip {bar(i, total)} | {i}/{total} | {f.name}")
    if total:
        endl()
    p(f"Zip: {zpath}")
    p(f"Zip size: {mb(zpath):.2f} MB")


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="项目根目录，默认当前目录")
    ap.add_argument("--out", default=OUT_NAME, help="输出目录名")
    ap.add_argument("--max-copy-mb", type=float, default=MAX_COPY_MB, help="单个文件最大复制大小")
    ap.add_argument("--overwrite", action="store_true", help="覆盖已有输出目录")
    ap.add_argument("--zip", action="store_true", help="整理后压缩成 zip")
    return ap.parse_args()


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    out = root / args.out

    if out.exists():
        if args.overwrite:
            shutil.rmtree(out)
        else:
            out = root / f"{args.out}_{time.strftime('%Y%m%d_%H%M%S')}"

    make_dirs(out)
    rec = Recorder()

    p("=" * 88)
    p("ARPSO curated workspace builder")
    p(f"Root:   {root}")
    p(f"Output: {out}")
    p("=" * 88)

    curate_paper(root, out, rec, args.max_copy_mb)
    curate_figures(root, out, rec, args.max_copy_mb)
    curate_tables(root, out, rec, args.max_copy_mb)
    curate_analysis(root, out, rec, args.max_copy_mb)
    curate_code(root, out, rec, args.max_copy_mb)
    write_docs(root, out, rec, args.max_copy_mb)
    write_manifest(root, out, rec)

    if args.zip:
        zip_out(out)

    p("")
    p("=" * 88)
    p("整理完成。")
    p(f"最终目录：{out}")
    p(f"主论文：{out / 'paper' / 'main.tex'}")
    p(f"说明文件：{out / 'docs' / 'FINAL_FILE_DECISION.md'}")
    p("=" * 88)


if __name__ == "__main__":
    main()
