# -*- coding: utf-8 -*-
r"""
organize_arpso_paper_files.py

用途：
  把 ARPSO/PSO 论文修改真正需要的文件，集中复制到一个干净工作目录里。
  不移动、不删除原项目文件，只复制。
  自动跳过超大 CSV，例如 ablation6_restart_details.csv 这种 1GB 文件。
  会生成 MANIFEST.md、跳过文件清单、目录树，方便后续继续改论文。

放置位置：
  建议放到：算法改进\code\organize_arpso_paper_files.py

运行方式：
  在“算法改进”根目录打开 PowerShell：

  D:\Python313\python.exe code\organize_arpso_paper_files.py

输出：
  算法改进\arpso_paper_clean_workspace

如果你想覆盖旧的整理目录：
  D:\Python313\python.exe code\organize_arpso_paper_files.py --overwrite

如果你想顺便压缩成 zip：
  D:\Python313\python.exe code\organize_arpso_paper_files.py --zip
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Iterable


# ============================================================
# Settings
# ============================================================

DEFAULT_OUTPUT_DIR = "arpso_paper_clean_workspace"

# 单个文件超过这个大小，默认不复制进 clean workspace
DEFAULT_MAX_COPY_MB = 20.0

# 这些大文件类型/关键词默认跳过
SKIP_NAME_KEYWORDS = [
    "raw_results",
    "restart_details",
    "curve_records",
    "full_parallel_checkpoint",
    ".synctex",
]

SKIP_SUFFIXES = {
    ".aux",
    ".log",
    ".out",
    ".toc",
    ".gz",
    ".pyc",
}

IGNORE_DIRS = {
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "arpso_paper_clean_workspace",
    "upload_pack_for_chat",
    "upload_pack_fast_for_chat",
    "project_audit_pack",
}


# ============================================================
# Console helpers
# ============================================================

def print_line(text: str = ""):
    print(text, flush=True)


def progress_bar(current: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "[" + "?" * width + "]"
    ratio = min(max(current / total, 0), 1)
    filled = int(width * ratio)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {ratio * 100:6.2f}%"


def show_inline(text: str):
    sys.stdout.write("\r" + text[:180].ljust(180))
    sys.stdout.flush()


def finish_inline():
    sys.stdout.write("\n")
    sys.stdout.flush()


def size_mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def normalize_rel(path: Path) -> str:
    return str(path).replace("\\", "/")


def should_skip_by_name(path: Path) -> bool:
    name = path.name.lower()
    full = normalize_rel(path).lower()
    return any(key.lower() in name or key.lower() in full for key in SKIP_NAME_KEYWORDS)


# ============================================================
# Copy helpers
# ============================================================

class CopyRecorder:
    def __init__(self):
        self.copied: list[dict] = []
        self.skipped: list[dict] = []
        self.missing: list[str] = []
        self.duplicates: list[dict] = []

    def add_copied(self, src: Path, dst: Path, category: str):
        self.copied.append({
            "category": category,
            "src": str(src),
            "dst": str(dst),
            "size_mb": size_mb(dst) if dst.exists() else 0,
        })

    def add_skipped(self, src: Path, reason: str, category: str = ""):
        self.skipped.append({
            "category": category,
            "src": str(src),
            "reason": reason,
            "size_mb": size_mb(src) if src.exists() else 0,
        })

    def add_missing(self, path: str):
        self.missing.append(path)

    def add_duplicate(self, src: Path, dst: Path, reason: str):
        self.duplicates.append({
            "src": str(src),
            "dst": str(dst),
            "reason": reason,
        })


def unique_dest(dst: Path) -> Path:
    """
    如果目标文件已存在，避免覆盖，自动加 _2, _3。
    """
    if not dst.exists():
        return dst

    stem = dst.stem
    suffix = dst.suffix
    parent = dst.parent

    for i in range(2, 1000):
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate

    raise RuntimeError(f"Too many duplicate files for destination: {dst}")


def copy_one(
    src: Path,
    dst: Path,
    recorder: CopyRecorder,
    category: str,
    root: Path,
    max_copy_mb: float,
    preserve_duplicates: bool = True,
):
    if not src.exists():
        recorder.add_missing(str(src))
        return

    if src.is_dir():
        recorder.add_skipped(src, "is a directory, use copy_tree_like instead", category)
        return

    if src.suffix.lower() in SKIP_SUFFIXES:
        recorder.add_skipped(src, f"skip suffix {src.suffix}", category)
        return

    if should_skip_by_name(src):
        recorder.add_skipped(src, "skip heavy/intermediate keyword", category)
        return

    mb = size_mb(src)
    if mb > max_copy_mb:
        recorder.add_skipped(src, f"file too large: {mb:.2f} MB > {max_copy_mb:.2f} MB", category)
        return

    ensure_dir(dst.parent)

    final_dst = unique_dest(dst) if preserve_duplicates else dst
    if final_dst != dst:
        recorder.add_duplicate(src, final_dst, "destination existed, renamed")

    shutil.copy2(src, final_dst)
    recorder.add_copied(src.relative_to(root), final_dst.relative_to(root), category)


def copy_if_exists(
    root: Path,
    rel: str,
    out_root: Path,
    dest_rel: str,
    recorder: CopyRecorder,
    category: str,
    max_copy_mb: float,
):
    src = root / rel
    dst = out_root / dest_rel / Path(rel).name
    if src.exists():
        copy_one(src, dst, recorder, category, root, max_copy_mb)
    else:
        recorder.add_missing(rel)


def copy_glob(
    root: Path,
    pattern: str,
    out_root: Path,
    dest_rel: str,
    recorder: CopyRecorder,
    category: str,
    max_copy_mb: float,
):
    files = sorted(root.glob(pattern))
    if not files:
        recorder.add_missing(pattern)
        return

    for src in files:
        if src.is_file():
            dst = out_root / dest_rel / src.name
            copy_one(src, dst, recorder, category, root, max_copy_mb)


def copy_tree_filtered(
    src_dir: Path,
    dst_dir: Path,
    root: Path,
    recorder: CopyRecorder,
    category: str,
    max_copy_mb: float,
    allowed_suffixes: set[str] | None = None,
    allow_keywords: list[str] | None = None,
):
    if not src_dir.exists():
        recorder.add_missing(str(src_dir.relative_to(root) if src_dir.is_absolute() else src_dir))
        return

    files = []
    for cur_root, dirs, filenames in os.walk(src_dir):
        cur = Path(cur_root)
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        for fname in filenames:
            p = cur / fname
            if allowed_suffixes is not None and p.suffix.lower() not in allowed_suffixes:
                continue
            if allow_keywords is not None:
                full_lower = normalize_rel(p.relative_to(root)).lower()
                if not any(k.lower() in full_lower for k in allow_keywords):
                    continue
            files.append(p)

    total = len(files)
    for i, src in enumerate(files, start=1):
        rel_inside = src.relative_to(src_dir)
        dst = dst_dir / rel_inside
        copy_one(src, dst, recorder, category, root, max_copy_mb)
        show_inline(f"      {category}: {progress_bar(i, total)} | {i}/{total} | {src.name}")
    if total:
        finish_inline()


# ============================================================
# TeX utility
# ============================================================

def parse_main_tex_assets(tex_path: Path):
    text = tex_path.read_text(encoding="utf-8", errors="ignore")

    cleaned_lines = []
    for line in text.splitlines():
        # 简单去掉注释，避免误判
        idx = line.find("%")
        if idx >= 0:
            line = line[:idx]
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    graphics = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text)
    inputs = re.findall(r"\\(?:input|include)\{([^}]+)\}", text)
    biblio = re.findall(r"\\bibliography\{([^}]+)\}", text)
    return graphics, inputs, biblio


def check_latex_assets(root: Path, out_root: Path, recorder: CopyRecorder):
    """
    检查主 tex 里的图片/input 是否能在原项目里找到。
    只检查，不修改。
    """
    candidates = [
        root / "论文" / "main.tex",
        root / "arpso_real_data_updated_latex_pack" / "main_ei_arpso_srr_real_data.tex",
    ]

    report_rows = []
    graphic_exts = [".pdf", ".png", ".jpg", ".jpeg", ".eps"]

    for tex in candidates:
        if not tex.exists():
            continue

        graphics, inputs, biblio = parse_main_tex_assets(tex)
        base = tex.parent

        for raw in graphics:
            raw = raw.strip()
            if raw.startswith("#"):
                # 宏参数，不是真实文件
                exists_path = None
                note = "macro argument, ignored"
                exists = True
            else:
                raw_path = Path(raw)
                candidates_paths = []
                if raw_path.suffix:
                    candidates_paths.extend([base / raw_path, root / raw_path])
                else:
                    for ext in graphic_exts:
                        candidates_paths.extend([base / (raw + ext), root / (raw + ext)])
                exists_path = next((p for p in candidates_paths if p.exists()), None)
                exists = exists_path is not None
                note = ""

            report_rows.append({
                "main_tex": normalize_rel(tex.relative_to(root)),
                "type": "includegraphics",
                "asset": raw,
                "exists": exists,
                "resolved": "" if exists_path is None else normalize_rel(exists_path.relative_to(root)),
                "note": note,
            })

        for raw in inputs:
            raw = raw.strip()
            raw_path = Path(raw)
            candidates_paths = [base / raw_path, root / raw_path]
            if not raw_path.suffix:
                candidates_paths.extend([base / (raw + ".tex"), root / (raw + ".tex")])
            exists_path = next((p for p in candidates_paths if p.exists()), None)
            report_rows.append({
                "main_tex": normalize_rel(tex.relative_to(root)),
                "type": "input/include",
                "asset": raw,
                "exists": exists_path is not None,
                "resolved": "" if exists_path is None else normalize_rel(exists_path.relative_to(root)),
                "note": "",
            })

        for group in biblio:
            for raw in [x.strip() for x in group.split(",") if x.strip()]:
                raw_path = Path(raw)
                candidates_paths = [base / raw_path, root / raw_path]
                if not raw_path.suffix:
                    candidates_paths.extend([base / (raw + ".bib"), root / (raw + ".bib")])
                exists_path = next((p for p in candidates_paths if p.exists()), None)
                report_rows.append({
                    "main_tex": normalize_rel(tex.relative_to(root)),
                    "type": "bibliography",
                    "asset": raw,
                    "exists": exists_path is not None,
                    "resolved": "" if exists_path is None else normalize_rel(exists_path.relative_to(root)),
                    "note": "",
                })

    import csv
    report_path = out_root / "00_manifest" / "latex_asset_check.csv"
    ensure_dir(report_path.parent)
    with report_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["main_tex", "type", "asset", "exists", "resolved", "note"])
        writer.writeheader()
        writer.writerows(report_rows)


# ============================================================
# Manifest / tree
# ============================================================

def write_clean_tree(out_root: Path):
    lines = []
    for cur_root, dirs, files in os.walk(out_root):
        cur = Path(cur_root)
        rel = cur.relative_to(out_root)
        level = 0 if str(rel) == "." else len(rel.parts)
        indent = "  " * level
        lines.append(f"{indent}{rel if str(rel) != '.' else out_root.name}/")

        for f in sorted(files):
            p = cur / f
            lines.append(f"{indent}  {f} [{size_mb(p):.2f} MB]")

    tree_path = out_root / "00_manifest" / "clean_workspace_tree.txt"
    ensure_dir(tree_path.parent)
    tree_path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    import csv
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(root: Path, out_root: Path, recorder: CopyRecorder, max_copy_mb: float):
    manifest_dir = out_root / "00_manifest"
    ensure_dir(manifest_dir)

    write_csv(
        manifest_dir / "copied_files.csv",
        recorder.copied,
        ["category", "src", "dst", "size_mb"],
    )
    write_csv(
        manifest_dir / "skipped_files.csv",
        recorder.skipped,
        ["category", "src", "reason", "size_mb"],
    )
    write_csv(
        manifest_dir / "duplicates_renamed.csv",
        recorder.duplicates,
        ["src", "dst", "reason"],
    )
    (manifest_dir / "missing_patterns_or_files.txt").write_text(
        "\n".join(recorder.missing),
        encoding="utf-8",
    )

    copied_count = len(recorder.copied)
    skipped_count = len(recorder.skipped)
    missing_count = len(recorder.missing)
    total_mb = sum(float(x["size_mb"]) for x in recorder.copied)

    lines = []
    lines.append("# ARPSO Paper Clean Workspace")
    lines.append("")
    lines.append(f"Generated at: `{time.strftime('%Y-%m-%d %H:%M:%S')}`")
    lines.append(f"Source project: `{root}`")
    lines.append(f"Output folder: `{out_root}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Copied files: **{copied_count}**")
    lines.append(f"- Skipped files: **{skipped_count}**")
    lines.append(f"- Missing patterns/files: **{missing_count}**")
    lines.append(f"- Total copied size: **{total_mb:.2f} MB**")
    lines.append(f"- Max copy size per file: **{max_copy_mb:.2f} MB**")
    lines.append("")
    lines.append("## Folder guide")
    lines.append("")
    lines.append("- `01_manuscript/`: main TeX/PDF and IEEEtran class.")
    lines.append("- `02_figures/`: figure PDFs/PNGs/TikZ source files copied from figure folders and generated packs.")
    lines.append("- `03_tables/`: LaTeX tables.")
    lines.append("- `04_results_summary/`: small CSV summaries used for paper tables and discussion.")
    lines.append("- `05_snippets/`: generated LaTeX discussion snippets.")
    lines.append("- `06_code_key/`: key Python scripts for algorithms, experiments, statistics, and figure generation.")
    lines.append("- `07_audit_reference/`: existing audit reports/catalogs if present.")
    lines.append("- `08_notes/`: README / Chinese-English notes / reference list.")
    lines.append("- `00_manifest/`: copied/skipped file lists and path check report.")
    lines.append("")
    lines.append("## Important rule")
    lines.append("")
    lines.append("The clean workspace intentionally does **not** copy huge raw files such as:")
    lines.append("")
    lines.append("- `ablation6_restart_details.csv`")
    lines.append("- `raw_results.csv`")
    lines.append("- `curve_records.csv`")
    lines.append("- `full_parallel_checkpoint_*.csv`")
    lines.append("")
    lines.append("Those files should stay in `results/` locally. Use summarized CSVs and audit packs for writing and sharing.")
    lines.append("")
    lines.append("## Recommended next step")
    lines.append("")
    lines.append("Use `01_manuscript/main.tex` as the final paper base. Then gradually replace figure/table paths so they point to `02_figures/` and `03_tables/`.")
    lines.append("")
    lines.append("For submission, create a smaller package from this workspace containing only:")
    lines.append("")
    lines.append("- `main.tex`")
    lines.append("- `IEEEtran.cls`")
    lines.append("- final figure PDFs")
    lines.append("- final table `.tex` files")
    lines.append("- bibliography `.bib` file if used")
    lines.append("")

    (manifest_dir / "MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")


def zip_folder(folder: Path, zip_path: Path):
    if zip_path.exists():
        zip_path.unlink()

    files = [p for p in folder.rglob("*") if p.is_file()]
    total = len(files)

    print_line("")
    print_line("开始压缩 clean workspace ...")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for i, p in enumerate(files, start=1):
            zf.write(p, p.relative_to(folder.parent))
            show_inline(f"  zip {progress_bar(i, total)} | {i}/{total} | {p.name}")
    finish_inline()


# ============================================================
# Main organize logic
# ============================================================

def organize(root: Path, out_root: Path, max_copy_mb: float, make_zip: bool, overwrite: bool):
    if out_root.exists():
        if overwrite:
            shutil.rmtree(out_root)
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            out_root = out_root.with_name(f"{out_root.name}_{timestamp}")

    ensure_dir(out_root)

    recorder = CopyRecorder()

    print_line("=" * 88)
    print_line("ARPSO paper clean workspace organizer")
    print_line(f"Project root: {root}")
    print_line(f"Output:       {out_root}")
    print_line(f"Max copy MB:  {max_copy_mb}")
    print_line("=" * 88)

    # ------------------------------------------------------------
    # 01 manuscript
    # ------------------------------------------------------------
    print_line("")
    print_line("Step 1/8: 复制论文主文件 ...")
    manuscript_targets = [
        ("论文/main.tex", "01_manuscript"),
        ("论文/main.pdf", "01_manuscript"),
        ("论文/IEEEtran.cls", "01_manuscript"),
        ("论文/README.md", "01_manuscript"),
        ("论文/英文.txt", "01_manuscript"),
        ("论文/中文.txt", "01_manuscript"),
        ("英文.txt", "01_manuscript"),
        ("中文.txt", "01_manuscript"),
        ("README.md", "01_manuscript"),
        ("arpso_real_data_updated_latex_pack/main_ei_arpso_srr_real_data.tex", "01_manuscript/alternative_versions"),
        ("arpso_real_data_updated_latex_pack/main_ei_arpso_srr_real_data.pdf", "01_manuscript/alternative_versions"),
    ]
    for rel, dest in manuscript_targets:
        src = root / rel
        if src.exists():
            copy_one(src, out_root / dest / src.name, recorder, "manuscript", root, max_copy_mb)

    # ------------------------------------------------------------
    # 02 figures
    # ------------------------------------------------------------
    print_line("")
    print_line("Step 2/8: 复制图文件和 TikZ 源码 ...")
    figure_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".eps", ".tex", ".txt"}
    figure_dirs = [
        ("figures", "02_figures/from_figures"),
        ("论文/figures", "02_figures/from_paper_figures"),
        ("paper_auto_update/figures", "02_figures/from_paper_auto_update"),
        ("paper_figures", "02_figures/from_paper_figures_root"),
        ("arpso_real_data_updated_latex_pack", "02_figures/from_real_data_latex_pack"),
        ("arpso_all_figures_final_pack", "02_figures/from_all_figures_pack"),
        ("arpso_ablation_figure_pack", "02_figures/from_ablation_figure_pack"),
    ]
    for src_rel, dst_rel in figure_dirs:
        src_dir = root / src_rel
        copy_tree_filtered(
            src_dir,
            out_root / dst_rel,
            root,
            recorder,
            "figures",
            max_copy_mb,
            allowed_suffixes=figure_suffixes,
            allow_keywords=None if src_rel in ["figures", "论文/figures", "paper_auto_update/figures", "paper_figures"] else [
                "tikz", "figure", "framework", "convergence", "restart", "ablation", "algorithm", "summary", "landscape"
            ],
        )

    # ------------------------------------------------------------
    # 03 tables
    # ------------------------------------------------------------
    print_line("")
    print_line("Step 3/8: 复制 LaTeX 表格 ...")
    table_dirs = [
        ("tables", "03_tables/from_tables"),
        ("paper_tables", "03_tables/from_paper_tables"),
        ("论文/tables", "03_tables/from_paper_tables_inside"),
        ("paper_auto_update/tables", "03_tables/from_paper_auto_update"),
    ]
    for src_rel, dst_rel in table_dirs:
        copy_tree_filtered(
            root / src_rel,
            out_root / dst_rel,
            root,
            recorder,
            "tables",
            max_copy_mb,
            allowed_suffixes={".tex", ".csv", ".txt"},
        )

    # ------------------------------------------------------------
    # 04 result summaries
    # ------------------------------------------------------------
    print_line("")
    print_line("Step 4/8: 复制小型结果摘要 CSV，跳过大原始结果 ...")
    result_dirs = [
        ("paper_auto_update/reports", "04_results_summary/paper_auto_update_reports"),
        ("results/cec", "04_results_summary/cec_main"),
        ("results/cec2017_ablation6", "04_results_summary/ablation6"),
    ]
    result_suffixes = {".csv", ".txt", ".md", ".log"}
    result_allow_keywords = [
        "summary",
        "average_rank",
        "rank_detail",
        "friedman",
        "wilcoxon",
        "runtime",
        "restart_summary",
        "status_report",
        "table_values",
        "errors",
        "mean_curves",
    ]
    for src_rel, dst_rel in result_dirs:
        copy_tree_filtered(
            root / src_rel,
            out_root / dst_rel,
            root,
            recorder,
            "results_summary",
            max_copy_mb,
            allowed_suffixes=result_suffixes,
            allow_keywords=result_allow_keywords,
        )

    # ------------------------------------------------------------
    # 05 snippets
    # ------------------------------------------------------------
    print_line("")
    print_line("Step 5/8: 复制自动生成的 LaTeX 讨论片段 ...")
    copy_tree_filtered(
        root / "paper_auto_update" / "snippets",
        out_root / "05_snippets",
        root,
        recorder,
        "snippets",
        max_copy_mb,
        allowed_suffixes={".tex", ".txt"},
    )

    # ------------------------------------------------------------
    # 06 code
    # ------------------------------------------------------------
    print_line("")
    print_line("Step 6/8: 复制关键代码 ...")
    key_code_names = [
        "auto_finalize_ablation6.py",
        "benchmarks.py",
        "cec_adapter.py",
        "common.py",
        "优化算法.py",
        "权重敏感性分析.py",
        "消融实验.py",
        "生成论文图表.py",
        "统计检验.py",
        "统计检验_CEC.py",
        "运行CEC2017消融实验_6variants.py",
        "运行CEC实验.py",
        "运行CEC实验_并行版.py",
        "运行实验.py",
        "arpso_project_auditor.py",
        "organize_arpso_paper_files.py",
        "make_upload_pack_fast_progress.py",
    ]
    for name in key_code_names:
        src = root / "code" / name
        if src.exists():
            copy_one(src, out_root / "06_code_key" / name, recorder, "code", root, max_copy_mb)

    # 顺便复制 code 目录下所有其他 py，小文件而已
    copy_tree_filtered(
        root / "code",
        out_root / "06_code_key/all_py_backup",
        root,
        recorder,
        "code_all_py",
        max_copy_mb,
        allowed_suffixes={".py"},
    )

    # ------------------------------------------------------------
    # 07 audit reference
    # ------------------------------------------------------------
    print_line("")
    print_line("Step 7/8: 复制已有审计包里的小型报告 ...")
    audit_suffixes = {".csv", ".txt", ".md"}
    audit_keywords = [
        "audit_report",
        "csv_catalog",
        "file_inventory",
        "top_100",
        "tex_asset",
        "missing",
        "copied",
        "manifest",
        "tree",
        "f23",
        "restart",
        "summary",
    ]
    copy_tree_filtered(
        root / "project_audit_pack",
        out_root / "07_audit_reference",
        root,
        recorder,
        "audit_reference",
        max_copy_mb,
        allowed_suffixes=audit_suffixes,
        allow_keywords=audit_keywords,
    )

    # ------------------------------------------------------------
    # 08 notes / references list
    # ------------------------------------------------------------
    print_line("")
    print_line("Step 8/8: 复制说明文件和生成参考文献列表 ...")
    note_targets = [
        ("papers/说明.txt", "08_notes"),
        ("figures/流程图.txt", "08_notes"),
        ("README.md", "08_notes"),
        ("中文.txt", "08_notes"),
        ("英文.txt", "08_notes"),
    ]
    for rel, dest in note_targets:
        src = root / rel
        if src.exists():
            copy_one(src, out_root / dest / src.name, recorder, "notes", root, max_copy_mb)

    # 不复制 papers/*.pdf，只生成列表，避免包太大
    papers_dir = root / "papers"
    if papers_dir.exists():
        pdfs = sorted(papers_dir.glob("*.pdf"))
        lines = ["# Reference PDFs in original project", ""]
        for p in pdfs:
            lines.append(f"- `{normalize_rel(p.relative_to(root))}` [{size_mb(p):.2f} MB]")
        ensure_dir(out_root / "08_notes")
        (out_root / "08_notes" / "reference_pdf_list.md").write_text("\n".join(lines), encoding="utf-8")

    # ------------------------------------------------------------
    # Checks and manifests
    # ------------------------------------------------------------
    print_line("")
    print_line("生成 LaTeX 路径检查、MANIFEST 和目录树 ...")
    check_latex_assets(root, out_root, recorder)
    write_manifest(root, out_root, recorder, max_copy_mb)
    write_clean_tree(out_root)

    if make_zip:
        zip_path = root / f"{out_root.name}.zip"
        zip_folder(out_root, zip_path)
        print_line(f"Zip created: {zip_path}")
        print_line(f"Zip size: {size_mb(zip_path):.2f} MB")

    print_line("")
    print_line("=" * 88)
    print_line("整理完成。")
    print_line(f"干净工作目录：{out_root}")
    print_line(f"文件清单：{out_root / '00_manifest' / 'MANIFEST.md'}")
    print_line(f"复制文件表：{out_root / '00_manifest' / 'copied_files.csv'}")
    print_line(f"跳过文件表：{out_root / '00_manifest' / 'skipped_files.csv'}")
    print_line("=" * 88)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="项目根目录，默认当前目录")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_DIR, help="输出整理目录名")
    parser.add_argument("--max-copy-mb", type=float, default=DEFAULT_MAX_COPY_MB, help="单个文件最大复制大小")
    parser.add_argument("--zip", action="store_true", help="整理后自动压缩成 zip")
    parser.add_argument("--overwrite", action="store_true", help="如果输出目录已存在，覆盖它")
    return parser.parse_args()


def main():
    args = parse_args()

    root = Path(args.root).resolve()
    out_root = root / args.out

    organize(
        root=root,
        out_root=out_root,
        max_copy_mb=args.max_copy_mb,
        make_zip=args.zip,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
