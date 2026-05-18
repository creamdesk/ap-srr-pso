# -*- coding: utf-8 -*-
r"""
arpso_project_auditor.py

作用：
  你不需要把 1GB+ 的 CSV 上传给 ChatGPT。
  这个脚本会在你本地“全面体检”整个 ARPSO 项目，然后生成一个小体积审计包：
    - 文件大小清单
    - 最大文件排行榜
    - 所有 CSV 的列名、前 50 行、精确行数
    - raw_results / restart_details / curve_records 的压缩统计摘要
    - F20-F24，尤其 F23 的 restart 行为摘要
    - main.tex / includegraphics / input 的路径检查
    - 最终 markdown 报告
    - 自动压缩成 zip，方便上传

放置位置：
  算法改进\code\arpso_project_auditor.py

推荐运行：
  在“算法改进”根目录打开 PowerShell：

  D:\Python313\python.exe code\arpso_project_auditor.py --deep

更快但不够全面：
  D:\Python313\python.exe code\arpso_project_auditor.py --quick

输出：
  算法改进\project_audit_pack\
  算法改进\project_audit_pack.zip

说明：
  --deep 会扫描大 CSV 一遍，但不会把大 CSV 复制进输出包。
  1GB 的 ablation6_restart_details.csv 会被压缩成小型 summary，而不是整文件上传。
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd


# ============================================================
# Basic progress utilities
# ============================================================

def print_line(text: str = ""):
    print(text, flush=True)


def progress_bar(current: float, total: float, width: int = 30) -> str:
    if total <= 0:
        return "[" + "?" * width + "]"
    ratio = min(max(current / total, 0), 1)
    filled = int(width * ratio)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {ratio * 100:6.2f}%"


def show_inline(text: str):
    sys.stdout.write("\r" + text[:220].ljust(220))
    sys.stdout.flush()


def finish_inline():
    sys.stdout.write("\n")
    sys.stdout.flush()


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024


def safe_name(path: Path | str) -> str:
    return str(path).replace("\\", "__").replace("/", "__").replace(":", "")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


# ============================================================
# CSV helpers
# ============================================================

def read_csv_head(path: Path, nrows: int = 50) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030"]
    last_error = None
    for enc in encodings:
        try:
            return pd.read_csv(path, nrows=nrows, encoding=enc, low_memory=False)
        except Exception as e:
            last_error = e
    raise RuntimeError(f"CSV read failed: {path} | {last_error}")


def iter_csv_chunks(path: Path, chunksize: int):
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030"]
    last_error = None
    for enc in encodings:
        try:
            reader = pd.read_csv(path, chunksize=chunksize, encoding=enc, low_memory=False)
            for chunk in reader:
                yield chunk
            return
        except Exception as e:
            last_error = e
    raise RuntimeError(f"CSV chunk read failed: {path} | {last_error}")


def exact_line_count(path: Path, show_progress: bool = True) -> int:
    """
    精确数 CSV 行数，不解析 CSV，只按换行符统计，速度比 pandas 全读快很多。
    返回文件总行数；CSV 数据行数一般 = 总行数 - 1。
    """
    total_bytes = path.stat().st_size
    count = 0
    read_bytes = 0
    start = time.time()
    chunk_size = 8 * 1024 * 1024

    with path.open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            count += block.count(b"\n")
            read_bytes += len(block)

            if show_progress:
                elapsed = max(time.time() - start, 1e-6)
                speed = read_bytes / 1024 / 1024 / elapsed
                show_inline(
                    f"      line count {progress_bar(read_bytes, total_bytes)} | "
                    f"{read_bytes/1024/1024:.1f}/{total_bytes/1024/1024:.1f} MB | {speed:.1f} MB/s"
                )

    if show_progress:
        finish_inline()

    # 如果文件最后一行没有换行符，也算一行
    try:
        with path.open("rb") as f:
            f.seek(max(total_bytes - 1, 0))
            last = f.read(1)
        if total_bytes > 0 and last != b"\n":
            count += 1
    except OSError:
        pass

    return count


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def find_col(cols: Iterable[str], patterns: Iterable[str]) -> Optional[str]:
    cols = list(cols)
    for pat in patterns:
        rx = re.compile(pat, re.I)
        for c in cols:
            if rx.search(str(c)) or rx.search(norm(c)):
                return c
    return None


def find_cols(cols: Iterable[str], patterns: Iterable[str]) -> list[str]:
    found = []
    for c in cols:
        for pat in patterns:
            if re.search(pat, str(c), re.I) or re.search(pat, norm(c), re.I):
                found.append(c)
                break
    return found


def to_numeric_safe(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


# ============================================================
# Inventory
# ============================================================

def build_file_inventory(root: Path, out_dir: Path) -> pd.DataFrame:
    ignore_dirs = {
        "__pycache__", ".git", ".idea", ".vscode",
        "project_audit_pack", "upload_pack_for_chat", "upload_pack_fast_for_chat",
    }

    rows = []
    for cur_root, dirs, files in os.walk(root):
        cur = Path(cur_root)
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]

        for fname in files:
            p = cur / fname
            try:
                rel = p.relative_to(root)
                size = p.stat().st_size
                suffix = p.suffix.lower()
                rows.append({
                    "path": str(rel),
                    "suffix": suffix,
                    "size_bytes": size,
                    "size_mb": size / 1024 / 1024,
                    "parent": str(rel.parent),
                    "name": p.name,
                })
            except OSError:
                continue

    df = pd.DataFrame(rows).sort_values("size_bytes", ascending=False)
    df.to_csv(out_dir / "file_inventory.csv", index=False, encoding="utf-8-sig")
    df.head(100).to_csv(out_dir / "top_100_largest_files.csv", index=False, encoding="utf-8-sig")

    by_suffix = (
        df.groupby("suffix", dropna=False)
        .agg(file_count=("path", "count"), total_mb=("size_mb", "sum"), max_mb=("size_mb", "max"))
        .reset_index()
        .sort_values("total_mb", ascending=False)
    )
    by_suffix.to_csv(out_dir / "file_size_by_suffix.csv", index=False, encoding="utf-8-sig")

    return df


def write_tree(root: Path, out_dir: Path, max_files_per_dir: int = 80):
    ignore_dirs = {
        "__pycache__", ".git", ".idea", ".vscode",
        "project_audit_pack", "upload_pack_for_chat", "upload_pack_fast_for_chat",
    }
    ignore_suffixes = [".aux", ".log", ".synctex.gz"]

    lines = []
    for cur_root, dirs, files in os.walk(root):
        cur = Path(cur_root)
        rel_root = cur.relative_to(root)

        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]

        level = 0 if str(rel_root) == "." else len(rel_root.parts)
        indent = "  " * level
        lines.append(f"{indent}{rel_root if str(rel_root) != '.' else root.name}/")

        shown = 0
        for fname in sorted(files):
            if any(fname.endswith(suf) for suf in ignore_suffixes):
                continue
            shown += 1
            if shown > max_files_per_dir:
                lines.append(f"{indent}  ...")
                break
            p = cur / fname
            try:
                lines.append(f"{indent}  {fname} [{file_size_mb(p):.2f} MB]")
            except OSError:
                lines.append(f"{indent}  {fname}")

    (out_dir / "project_tree_with_sizes.txt").write_text("\n".join(lines), encoding="utf-8")


# ============================================================
# CSV catalog
# ============================================================

def profile_csvs(root: Path, out_dir: Path, inventory: pd.DataFrame, args) -> pd.DataFrame:
    schema_dir = out_dir / "csv_schemas"
    head_dir = out_dir / "csv_heads"
    sample_dir = out_dir / "csv_samples"
    ensure_dir(schema_dir)
    ensure_dir(head_dir)
    ensure_dir(sample_dir)

    csv_rows = inventory[inventory["suffix"] == ".csv"].copy()
    catalog_rows = []

    total = len(csv_rows)
    print_line("")
    print_line(f"发现 CSV 文件：{total} 个，开始建立 CSV catalog ...")

    for i, row in enumerate(csv_rows.itertuples(index=False), start=1):
        rel = Path(row.path)
        p = root / rel
        size_mb = row.size_mb

        print_line("-" * 88)
        print_line(f"CSV 进度 {progress_bar(i, total)} | {i}/{total}")
        print_line(f"当前 CSV：{rel} | {size_mb:.2f} MB")

        status = "ok"
        cols = []
        data_rows = None

        try:
            head = read_csv_head(p, nrows=args.head_rows)
            cols = list(head.columns)

            schema = pd.DataFrame({
                "column": cols,
                "dtype_from_head": [str(x) for x in head.dtypes],
                "non_null_in_head": [int(head[c].notna().sum()) for c in cols],
                "example": [
                    "" if head[c].dropna().empty else str(head[c].dropna().iloc[0])[:200]
                    for c in cols
                ],
            })
            schema.to_csv(schema_dir / f"{safe_name(rel)}__schema.csv", index=False, encoding="utf-8-sig")
            head.to_csv(head_dir / f"{safe_name(rel)}__head{args.head_rows}.csv", index=False, encoding="utf-8-sig")

            # 精确行数：只数换行，不解析，通常很快
            if args.quick and size_mb > args.quick_line_count_limit_mb:
                data_rows = None
                print_line("      quick 模式：跳过超大 CSV 精确行数")
            else:
                total_lines = exact_line_count(p, show_progress=size_mb > 50)
                data_rows = max(total_lines - 1, 0)
                print_line(f"      精确数据行数：{data_rows:,}")

            # 大 CSV 不复制，只抽前 N 行样本
            if size_mb > args.copy_limit_mb:
                sample_n = min(args.sample_rows, max(args.head_rows, args.sample_rows))
                sample = read_csv_head(p, nrows=sample_n)
                sample.to_csv(sample_dir / f"{safe_name(rel)}__sample{sample_n}.csv", index=False, encoding="utf-8-sig")

        except Exception as e:
            status = f"error: {repr(e)}"
            print_line(f"      ERROR: {status}")

        catalog_rows.append({
            "path": str(rel),
            "size_mb": size_mb,
            "data_rows_exact_or_blank": data_rows,
            "num_columns": len(cols),
            "columns": " | ".join(cols),
            "status": status,
        })

    catalog = pd.DataFrame(catalog_rows).sort_values("size_mb", ascending=False)
    catalog.to_csv(out_dir / "csv_catalog.csv", index=False, encoding="utf-8-sig")
    return catalog


# ============================================================
# Exact / compressed summaries for important CSVs
# ============================================================

def choose_group_cols(cols: Iterable[str]) -> list[str]:
    cols = list(cols)
    alg_col = find_col(cols, [r"^algorithm$", r"alg", r"method", r"variant"])
    fid_col = find_col(cols, [r"^functionid$", r"function_id", r"fid", r"f_id"])
    func_col = find_col(cols, [r"^function$", r"problem", r"func"])

    group_cols = []
    for c in [alg_col, fid_col, func_col]:
        if c and c not in group_cols:
            group_cols.append(c)
    return group_cols


def choose_numeric_cols(cols: Iterable[str]) -> list[str]:
    patterns = [
        r"best", r"error", r"fitness", r"rank", r"runtime", r"time",
        r"restart", r"particle", r"ratio", r"diversity", r"stagnation",
        r"fe$", r"fes", r"eval", r"iteration", r"iter", r"count",
        r"sigma", r"score",
    ]
    selected = []
    for c in cols:
        if any(re.search(p, str(c), re.I) or re.search(p, norm(c), re.I) for p in patterns):
            selected.append(c)
    return selected


def combine_group_stats(acc: dict, chunk_stats: pd.DataFrame):
    """
    acc 按 column 保存 sum/count/min/max。
    chunk_stats index = group_cols
    columns 格式：metric__sum, metric__count, metric__min, metric__max
    """
    if chunk_stats.empty:
        return acc

    if acc.get("df") is None:
        acc["df"] = chunk_stats.copy()
    else:
        old = acc["df"]
        combined = pd.concat([old, chunk_stats], axis=0)

        sum_cols = [c for c in combined.columns if c.endswith("__sum") or c.endswith("__count") or c == "__rows"]
        min_cols = [c for c in combined.columns if c.endswith("__min")]
        max_cols = [c for c in combined.columns if c.endswith("__max")]

        parts = []
        if sum_cols:
            parts.append(combined[sum_cols].groupby(level=list(range(combined.index.nlevels))).sum(min_count=1))
        if min_cols:
            parts.append(combined[min_cols].groupby(level=list(range(combined.index.nlevels))).min())
        if max_cols:
            parts.append(combined[max_cols].groupby(level=list(range(combined.index.nlevels))).max())

        acc["df"] = pd.concat(parts, axis=1) if parts else combined
    return acc


def exact_group_summary(
    src: Path,
    rel: Path,
    out_path: Path,
    chunksize: int,
    max_numeric_cols: int = 16,
):
    """
    对重要大 CSV 做精确压缩摘要：
      Algorithm x FunctionID x Function 级别
      输出每个数值指标的 mean/min/max/count
    """
    head = read_csv_head(src, nrows=100)
    cols = list(head.columns)
    group_cols = choose_group_cols(cols)

    if not group_cols:
        print_line("      没找到 Algorithm/Function 列，跳过 group summary")
        return

    numeric_candidates = choose_numeric_cols(cols)
    numeric_candidates = [c for c in numeric_candidates if c not in group_cols][:max_numeric_cols]

    if not numeric_candidates:
        print_line("      没找到可摘要的数值列，跳过 group summary")
        return

    total_bytes = src.stat().st_size
    start = time.time()
    read_rows = 0
    acc = {"df": None}

    print_line(f"      group summary: group_cols={group_cols}")
    print_line(f"      numeric_cols={numeric_candidates}")

    for chunk_idx, chunk in enumerate(iter_csv_chunks(src, chunksize=chunksize), start=1):
        read_rows += len(chunk)

        missing = [c for c in group_cols if c not in chunk.columns]
        if missing:
            continue

        usable_numeric = []
        temp = chunk[group_cols].copy()

        for c in numeric_candidates:
            if c in chunk.columns:
                num = pd.to_numeric(chunk[c], errors="coerce")
                if num.notna().any():
                    temp[c] = num
                    usable_numeric.append(c)

        if not usable_numeric:
            continue

        g = temp.groupby(group_cols, dropna=False)

        parts = []
        rows = g.size().rename("__rows")
        parts.append(rows)

        for c in usable_numeric:
            s = g[c].sum(min_count=1).rename(f"{c}__sum")
            cnt = g[c].count().rename(f"{c}__count")
            mn = g[c].min().rename(f"{c}__min")
            mx = g[c].max().rename(f"{c}__max")
            parts.extend([s, cnt, mn, mx])

        chunk_stats = pd.concat(parts, axis=1)
        acc = combine_group_stats(acc, chunk_stats)

        elapsed = max(time.time() - start, 1e-6)
        speed = read_rows / elapsed
        show_inline(
            f"      summarizing chunks | chunks={chunk_idx:,} | rows={read_rows:,} | "
            f"speed={speed:,.0f} rows/s"
        )

    finish_inline()

    if acc["df"] is None or acc["df"].empty:
        print_line("      group summary 没有结果")
        return

    result = acc["df"].copy()

    # 根据 sum/count 计算 mean
    for c in numeric_candidates:
        sum_c = f"{c}__sum"
        count_c = f"{c}__count"
        if sum_c in result.columns and count_c in result.columns:
            result[f"{c}__mean"] = result[sum_c] / result[count_c].replace(0, np.nan)

    result = result.reset_index()
    result.insert(0, "source_file", str(rel))
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print_line(f"      已输出摘要：{out_path}")


def curve_bin_summary(src: Path, rel: Path, out_path: Path, chunksize: int, bins_per_decade: int = 12):
    """
    对曲线文件做压缩：
      Algorithm x Function x log(FE/Iteration) bin
      输出均值，不保留所有点。
    """
    head = read_csv_head(src, nrows=100)
    cols = list(head.columns)

    alg_col = find_col(cols, [r"^algorithm$", r"alg", r"method", r"variant"])
    fid_col = find_col(cols, [r"^functionid$", r"function_id", r"fid", r"f_id"])
    func_col = find_col(cols, [r"^function$", r"problem", r"func"])
    x_col = find_col(cols, [r"^fe$", r"fes", r"eval", r"iteration", r"iter", r"step"])

    y_cols = find_cols(cols, [r"mean.*error", r"best.*error", r"meanbest", r"bestfitness", r"best"])

    group_base = [c for c in [alg_col, fid_col, func_col] if c]
    if not group_base or not x_col or not y_cols:
        print_line("      curve bin summary 条件不足，跳过")
        return

    y_cols = [c for c in y_cols if c != x_col][:8]

    acc = {"df": None}
    read_rows = 0
    start = time.time()

    print_line(f"      curve bins: x_col={x_col}, y_cols={y_cols}")

    for chunk_idx, chunk in enumerate(iter_csv_chunks(src, chunksize=chunksize), start=1):
        read_rows += len(chunk)

        temp_cols = [c for c in group_base + [x_col] + y_cols if c in chunk.columns]
        temp = chunk[temp_cols].copy()

        x = pd.to_numeric(temp[x_col], errors="coerce")
        temp[x_col] = x
        temp = temp[temp[x_col].notna()]
        if temp.empty:
            continue

        # log bin，FE 越大越稀疏，适合曲线压缩
        temp["CurveBin"] = np.floor(np.log10(temp[x_col].clip(lower=1) + 1) * bins_per_decade).astype(int)

        usable_y = []
        for c in y_cols:
            if c in temp.columns:
                temp[c] = pd.to_numeric(temp[c], errors="coerce")
                if temp[c].notna().any():
                    usable_y.append(c)

        if not usable_y:
            continue

        group_cols = group_base + ["CurveBin"]
        g = temp.groupby(group_cols, dropna=False)

        parts = [g.size().rename("__rows"), g[x_col].mean().rename(f"{x_col}__mean")]
        for c in usable_y:
            parts.append(g[c].mean().rename(f"{c}__mean"))
            parts.append(g[c].min().rename(f"{c}__min"))
            parts.append(g[c].max().rename(f"{c}__max"))

        chunk_stats = pd.concat(parts, axis=1)
        acc = combine_group_stats(acc, chunk_stats)

        elapsed = max(time.time() - start, 1e-6)
        speed = read_rows / elapsed
        show_inline(
            f"      curve binning | chunks={chunk_idx:,} | rows={read_rows:,} | speed={speed:,.0f} rows/s"
        )

    finish_inline()

    if acc["df"] is None or acc["df"].empty:
        print_line("      curve bin summary 没有结果")
        return

    result = acc["df"].reset_index()
    result.insert(0, "source_file", str(rel))
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print_line(f"      已输出曲线压缩摘要：{out_path}")


def summarize_important_csvs(root: Path, out_dir: Path, inventory: pd.DataFrame, args):
    summary_dir = out_dir / "data_summaries"
    ensure_dir(summary_dir)

    csv_paths = [Path(p) for p in inventory[inventory["suffix"] == ".csv"]["path"].tolist()]

    targets = []
    for rel in csv_paths:
        name = rel.name.lower()
        rel_str = str(rel).replace("\\", "/").lower()

        # 重要结果文件：raw/summary/restart/curve/rank/wilcoxon 都尽量摘要
        if any(key in name for key in [
            "raw_results", "restart_details", "restart_summary",
            "summary_results", "rank_detail", "average_rank",
            "wilcoxon", "friedman", "mean_curves", "curve_records",
        ]):
            targets.append(rel)

    print_line("")
    print_line(f"开始生成关键 CSV 的压缩摘要：{len(targets)} 个目标文件")

    for i, rel in enumerate(targets, start=1):
        src = root / rel
        if not src.exists():
            continue

        size_mb = file_size_mb(src)
        name = rel.name.lower()

        print_line("-" * 88)
        print_line(f"摘要进度 {progress_bar(i, len(targets))} | {i}/{len(targets)}")
        print_line(f"目标文件：{rel} | {size_mb:.2f} MB")

        # 小结果文件直接复制一份，方便我查看
        if size_mb <= args.copy_limit_mb:
            dst = summary_dir / "small_key_csvs" / rel
            ensure_dir(dst.parent)
            shutil.copy2(src, dst)

        # quick 模式下，大文件不做全量 chunk 摘要
        if args.quick and size_mb > args.quick_summary_limit_mb:
            print_line("      quick 模式：跳过该大文件的全量摘要")
            continue

        try:
            if "curve" in name:
                out = summary_dir / f"{safe_name(rel)}__curve_bins.csv"
                curve_bin_summary(src, rel, out, chunksize=args.chunksize)
            else:
                out = summary_dir / f"{safe_name(rel)}__group_summary.csv"
                exact_group_summary(src, rel, out, chunksize=args.chunksize)
        except Exception as e:
            error_path = summary_dir / f"{safe_name(rel)}__summary_error.txt"
            error_path.write_text(repr(e), encoding="utf-8")
            print_line(f"      摘要失败：{repr(e)}")


# ============================================================
# Focused F23 restart summary
# ============================================================

def f23_restart_summary(root: Path, out_dir: Path, inventory: pd.DataFrame, args):
    focus_dir = out_dir / "f23_restart_focus"
    ensure_dir(focus_dir)

    restart_files = []
    for p in inventory["path"].tolist():
        rel = Path(p)
        name = rel.name.lower()
        if "restart" in name and "details" in name and rel.suffix.lower() == ".csv":
            restart_files.append(rel)

    if not restart_files:
        return

    print_line("")
    print_line("开始生成 F20-F24 / F23 restart 行为摘要 ...")

    target_ids = {20, 21, 22, 23, 24}

    for rel in restart_files:
        src = root / rel
        size_mb = file_size_mb(src)

        print_line("-" * 88)
        print_line(f"restart focus：{rel} | {size_mb:.2f} MB")

        if args.quick and size_mb > args.quick_summary_limit_mb:
            print_line("      quick 模式：跳过大 restart details 的 F23 深度扫描")
            continue

        try:
            head = read_csv_head(src, nrows=100)
            cols = list(head.columns)

            alg_col = find_col(cols, [r"^algorithm$", r"alg", r"method", r"variant"])
            fid_col = find_col(cols, [r"^functionid$", r"function_id", r"fid", r"f_id"])
            func_col = find_col(cols, [r"^function$", r"problem", r"func"])
            run_col = find_col(cols, [r"^run$", r"trial", r"seed"])
            fe_col = find_col(cols, [r"^fe$", r"fes", r"eval", r"restartiter", r"iteration", r"iter"])

            if not alg_col or not (fid_col or func_col):
                print_line("      缺少 Algorithm/Function 信息，跳过")
                continue

            numeric_cols = choose_numeric_cols(cols)
            keep_numeric = [c for c in numeric_cols if c not in [alg_col, fid_col, func_col, run_col]][:16]

            rows_out = []
            samples = []
            read_rows = 0
            kept_rows = 0
            start = time.time()

            acc = {"df": None}

            for chunk_idx, chunk in enumerate(iter_csv_chunks(src, chunksize=args.chunksize), start=1):
                read_rows += len(chunk)

                if fid_col and fid_col in chunk.columns:
                    fid = pd.to_numeric(chunk[fid_col], errors="coerce")
                    mask = fid.isin(list(target_ids))
                else:
                    # Function 类似 F23 / CEC2017-F23
                    ftext = chunk[func_col].astype(str)
                    extracted = pd.to_numeric(ftext.str.extract(r"(\d+)", expand=False), errors="coerce")
                    mask = extracted.isin(list(target_ids))
                    chunk = chunk.copy()
                    chunk["__FunctionID_extracted"] = extracted
                    fid_col = "__FunctionID_extracted"

                part = chunk.loc[mask].copy()
                if part.empty:
                    elapsed = max(time.time() - start, 1e-6)
                    show_inline(
                        f"      scanning F20-F24 | chunks={chunk_idx:,} | rows={read_rows:,} | kept={kept_rows:,} | speed={read_rows/elapsed:,.0f} rows/s"
                    )
                    continue

                kept_rows += len(part)

                group_cols = [c for c in [alg_col, fid_col, func_col, run_col] if c and c in part.columns]
                usable_numeric = []
                temp = part[group_cols].copy()
                for c in keep_numeric:
                    if c in part.columns:
                        temp[c] = pd.to_numeric(part[c], errors="coerce")
                        if temp[c].notna().any():
                            usable_numeric.append(c)

                if usable_numeric:
                    g = temp.groupby(group_cols, dropna=False)
                    parts = [g.size().rename("__rows")]
                    for c in usable_numeric:
                        parts.extend([
                            g[c].sum(min_count=1).rename(f"{c}__sum"),
                            g[c].count().rename(f"{c}__count"),
                            g[c].min().rename(f"{c}__min"),
                            g[c].max().rename(f"{c}__max"),
                        ])
                    stats = pd.concat(parts, axis=1)
                    acc = combine_group_stats(acc, stats)

                # 保留极少量事件样本，不让输出炸掉
                if len(samples) < 20:
                    samples.append(part.head(200))

                elapsed = max(time.time() - start, 1e-6)
                show_inline(
                    f"      scanning F20-F24 | chunks={chunk_idx:,} | rows={read_rows:,} | kept={kept_rows:,} | speed={read_rows/elapsed:,.0f} rows/s"
                )

            finish_inline()

            if acc["df"] is not None and not acc["df"].empty:
                result = acc["df"].copy()
                for c in keep_numeric:
                    sum_c = f"{c}__sum"
                    count_c = f"{c}__count"
                    if sum_c in result.columns and count_c in result.columns:
                        result[f"{c}__mean"] = result[sum_c] / result[count_c].replace(0, np.nan)

                result = result.reset_index()
                result.insert(0, "source_file", str(rel))
                out = focus_dir / f"{safe_name(rel)}__F20_F24_by_algorithm_function_run.csv"
                result.to_csv(out, index=False, encoding="utf-8-sig")
                print_line(f"      F20-F24 摘要已输出：{out}")

            if samples:
                sample_df = pd.concat(samples, ignore_index=True)
                sample_out = focus_dir / f"{safe_name(rel)}__F20_F24_small_event_sample.csv"
                sample_df.to_csv(sample_out, index=False, encoding="utf-8-sig")

            note = [
                f"source={rel}",
                f"size_mb={size_mb:.2f}",
                f"algorithm_col={alg_col}",
                f"function_id_col={fid_col}",
                f"function_col={func_col}",
                f"run_col={run_col}",
                f"fe_col={fe_col}",
                f"read_rows={read_rows}",
                f"kept_F20_F24_rows={kept_rows}",
            ]
            (focus_dir / f"{safe_name(rel)}__note.txt").write_text("\n".join(note), encoding="utf-8")

        except Exception as e:
            (focus_dir / f"{safe_name(rel)}__error.txt").write_text(repr(e), encoding="utf-8")
            print_line(f"      F23 focus 失败：{repr(e)}")


# ============================================================
# TeX checks
# ============================================================

def parse_tex_assets(tex_path: Path):
    text = tex_path.read_text(encoding="utf-8", errors="ignore")

    # 去掉注释行里的内容，降低误报
    cleaned_lines = []
    for line in text.splitlines():
        idx = line.find("%")
        if idx >= 0:
            line = line[:idx]
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    graphics = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text)
    inputs = re.findall(r"\\(?:input|include)\{([^}]+)\}", text)
    biblios = re.findall(r"\\bibliography\{([^}]+)\}", text)

    return graphics, inputs, biblios


def check_tex_assets(root: Path, out_dir: Path, inventory: pd.DataFrame):
    tex_dir = out_dir / "tex_checks"
    ensure_dir(tex_dir)

    tex_files = [root / Path(p) for p in inventory["path"].tolist() if Path(p).suffix.lower() == ".tex"]
    main_tex_files = [p for p in tex_files if p.name.lower().startswith("main")]

    rows = []

    graphic_exts = [".pdf", ".png", ".jpg", ".jpeg", ".eps"]

    for tex in main_tex_files:
        try:
            graphics, inputs, biblios = parse_tex_assets(tex)
        except Exception as e:
            rows.append({
                "tex_file": str(tex.relative_to(root)),
                "asset_type": "read_error",
                "asset": "",
                "resolved": "",
                "exists": False,
                "note": repr(e),
            })
            continue

        base = tex.parent

        for g in graphics:
            raw = g.strip()
            raw_path = Path(raw)

            candidates = []
            if raw_path.suffix:
                candidates.append(base / raw_path)
                candidates.append(root / raw_path)
            else:
                for ext in graphic_exts:
                    candidates.append(base / (raw + ext))
                    candidates.append(root / (raw + ext))

            exists_path = next((c for c in candidates if c.exists()), None)
            rows.append({
                "tex_file": str(tex.relative_to(root)),
                "asset_type": "includegraphics",
                "asset": raw,
                "resolved": "" if exists_path is None else str(exists_path.relative_to(root)),
                "exists": exists_path is not None,
                "note": "",
            })

        for inp in inputs:
            raw = inp.strip()
            candidates = [base / raw, root / raw]
            if not Path(raw).suffix:
                candidates.extend([base / (raw + ".tex"), root / (raw + ".tex")])

            exists_path = next((c for c in candidates if c.exists()), None)
            rows.append({
                "tex_file": str(tex.relative_to(root)),
                "asset_type": "input/include",
                "asset": raw,
                "resolved": "" if exists_path is None else str(exists_path.relative_to(root)),
                "exists": exists_path is not None,
                "note": "",
            })

        for bib_group in biblios:
            for raw in [x.strip() for x in bib_group.split(",") if x.strip()]:
                candidates = [base / raw, root / raw]
                if not Path(raw).suffix:
                    candidates.extend([base / (raw + ".bib"), root / (raw + ".bib")])
                exists_path = next((c for c in candidates if c.exists()), None)
                rows.append({
                    "tex_file": str(tex.relative_to(root)),
                    "asset_type": "bibliography",
                    "asset": raw,
                    "resolved": "" if exists_path is None else str(exists_path.relative_to(root)),
                    "exists": exists_path is not None,
                    "note": "",
                })

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["tex_file", "asset_type", "asset", "resolved", "exists", "note"])

    df.to_csv(tex_dir / "tex_asset_check.csv", index=False, encoding="utf-8-sig")
    df[df["exists"] == False].to_csv(tex_dir / "tex_missing_assets.csv", index=False, encoding="utf-8-sig")

    main_df = pd.DataFrame({
        "main_tex_file": [str(p.relative_to(root)) for p in main_tex_files],
        "size_mb": [file_size_mb(p) for p in main_tex_files],
    })
    main_df.to_csv(tex_dir / "main_tex_files.csv", index=False, encoding="utf-8-sig")


# ============================================================
# Copy useful small files
# ============================================================

def copy_useful_small_files(root: Path, out_dir: Path, inventory: pd.DataFrame, args):
    copy_dir = out_dir / "useful_small_files"
    ensure_dir(copy_dir)

    useful_patterns = [
        r"main.*\.tex$",
        r"main.*\.pdf$",
        r"table.*\.tex$",
        r".*summary.*\.csv$",
        r".*average_rank.*\.csv$",
        r".*wilcoxon.*\.csv$",
        r".*friedman.*\.csv$",
        r".*rank_detail.*\.csv$",
        r".*runtime.*\.csv$",
        r".*restart_summary.*\.csv$",
        r".*status_report.*\.txt$",
        r".*discussion.*\.tex$",
        r".*errors.*\.log$",
    ]

    copied = []
    for row in inventory.itertuples(index=False):
        rel = Path(row.path)
        if row.size_mb > args.copy_limit_mb:
            continue
        path_str = str(rel).replace("\\", "/")
        if any(re.search(p, path_str, re.I) for p in useful_patterns):
            src = root / rel
            dst = copy_dir / rel
            ensure_dir(dst.parent)
            try:
                shutil.copy2(src, dst)
                copied.append(str(rel))
            except OSError:
                pass

    pd.DataFrame({"copied_file": copied}).to_csv(copy_dir / "copied_files_index.csv", index=False, encoding="utf-8-sig")


# ============================================================
# Markdown report
# ============================================================

def generate_markdown_report(root: Path, out_dir: Path):
    lines = []
    lines.append("# ARPSO Project Audit Report")
    lines.append("")
    lines.append(f"Project root: `{root}`")
    lines.append(f"Generated at: `{time.strftime('%Y-%m-%d %H:%M:%S')}`")
    lines.append("")

    inv_path = out_dir / "file_inventory.csv"
    csv_catalog_path = out_dir / "csv_catalog.csv"

    if inv_path.exists():
        inv = pd.read_csv(inv_path)
        total_mb = inv["size_mb"].sum()
        lines.append("## 1. File Size Overview")
        lines.append("")
        lines.append(f"- Total files scanned: **{len(inv)}**")
        lines.append(f"- Total size: **{total_mb:.2f} MB**")
        lines.append("")
        lines.append("### Top 15 largest files")
        lines.append("")
        top = inv.sort_values("size_mb", ascending=False).head(15)
        lines.append("| Rank | File | Size MB |")
        lines.append("|---:|---|---:|")
        for i, r in enumerate(top.itertuples(index=False), start=1):
            lines.append(f"| {i} | `{r.path}` | {r.size_mb:.2f} |")
        lines.append("")

    if csv_catalog_path.exists():
        cat = pd.read_csv(csv_catalog_path)
        lines.append("## 2. CSV Overview")
        lines.append("")
        lines.append(f"- CSV files: **{len(cat)}**")
        lines.append("")
        lines.append("### Top 10 largest CSV files")
        lines.append("")
        top = cat.sort_values("size_mb", ascending=False).head(10)
        lines.append("| Rank | CSV | Size MB | Rows | Columns |")
        lines.append("|---:|---|---:|---:|---:|")
        for i, r in enumerate(top.itertuples(index=False), start=1):
            rows = "" if pd.isna(r.data_rows_exact_or_blank) else int(r.data_rows_exact_or_blank)
            lines.append(f"| {i} | `{r.path}` | {r.size_mb:.2f} | {rows} | {r.num_columns} |")
        lines.append("")

    tex_missing = out_dir / "tex_checks" / "tex_missing_assets.csv"
    if tex_missing.exists():
        miss = pd.read_csv(tex_missing)
        lines.append("## 3. TeX Asset Check")
        lines.append("")
        if miss.empty:
            lines.append("- No missing assets found in checked main TeX files.")
        else:
            lines.append(f"- Missing assets found: **{len(miss)}**")
            lines.append("")
            lines.append("| TeX | Type | Asset |")
            lines.append("|---|---|---|")
            for r in miss.head(30).itertuples(index=False):
                lines.append(f"| `{r.tex_file}` | {r.asset_type} | `{r.asset}` |")
        lines.append("")

    lines.append("## 4. What to upload to ChatGPT")
    lines.append("")
    lines.append("Upload `project_audit_pack.zip`. Do not upload 1GB raw CSV files.")
    lines.append("")
    lines.append("Most useful folders inside the zip:")
    lines.append("")
    lines.append("- `data_summaries/`: compressed exact summaries for raw/restart/curve files")
    lines.append("- `f23_restart_focus/`: focused restart behavior summary for F20-F24, especially F23")
    lines.append("- `csv_catalog.csv`: all CSV sizes, columns, and row counts")
    lines.append("- `tex_checks/`: whether main.tex references missing figures/tables")
    lines.append("- `useful_small_files/`: small paper files copied directly")
    lines.append("")

    (out_dir / "PROJECT_AUDIT_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


# ============================================================
# Zip output
# ============================================================

def zip_output(root: Path, out_dir: Path, zip_path: Path):
    if zip_path.exists():
        zip_path.unlink()

    files = [p for p in out_dir.rglob("*") if p.is_file()]
    total = len(files)

    print_line("")
    print_line("开始压缩 project_audit_pack.zip ...")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for i, p in enumerate(files, start=1):
            zf.write(p, p.relative_to(root))
            show_inline(f"  zip {progress_bar(i, total)} | {i}/{total} | {p.name}")

    finish_inline()


# ============================================================
# Main
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="项目根目录。默认是当前目录，也就是“算法改进”根目录。")
    parser.add_argument("--out", default="project_audit_pack", help="输出文件夹名。")
    parser.add_argument("--copy-limit-mb", type=float, default=8.0, help="小于该大小的有用文件会复制进审计包。")
    parser.add_argument("--head-rows", type=int, default=50, help="每个 CSV 保存前多少行。")
    parser.add_argument("--sample-rows", type=int, default=3000, help="大 CSV 保存前多少行 sample。")
    parser.add_argument("--chunksize", type=int, default=100000, help="大 CSV 分块读取大小。")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true", help="快速模式：跳过超大 CSV 的深度摘要。")
    mode.add_argument("--deep", action="store_true", help="深度模式：扫描大 CSV 并生成压缩摘要。推荐。")

    parser.add_argument("--quick-line-count-limit-mb", type=float, default=500.0, help="quick 模式下超过该大小则不精确数行。")
    parser.add_argument("--quick-summary-limit-mb", type=float, default=80.0, help="quick 模式下超过该大小则不做全量摘要。")
    return parser.parse_args()


def main():
    args = parse_args()

    root = Path(args.root).resolve()
    out_dir = root / args.out
    zip_path = root / f"{args.out}.zip"

    if not args.quick and not args.deep:
        # 默认用 quick，避免用户误跑超久；你要全面就显式 --deep
        args.quick = True

    if out_dir.exists():
        shutil.rmtree(out_dir)
    ensure_dir(out_dir)

    print_line("=" * 88)
    print_line("ARPSO Project Auditor")
    print_line(f"Root: {root}")
    print_line(f"Mode: {'DEEP' if args.deep else 'QUICK'}")
    print_line(f"Output: {out_dir}")
    print_line("=" * 88)

    start_all = time.time()

    print_line("")
    print_line("Step 1/7: 生成文件清单和目录树 ...")
    inventory = build_file_inventory(root, out_dir)
    write_tree(root, out_dir)
    print_line(f"文件数：{len(inventory)}")

    print_line("")
    print_line("Step 2/7: 复制有用的小文件 ...")
    copy_useful_small_files(root, out_dir, inventory, args)

    print_line("")
    print_line("Step 3/7: 建立 CSV catalog，保存 schema/head/行数 ...")
    csv_catalog = profile_csvs(root, out_dir, inventory, args)

    print_line("")
    print_line("Step 4/7: 生成关键 CSV 压缩摘要 ...")
    summarize_important_csvs(root, out_dir, inventory, args)

    print_line("")
    print_line("Step 5/7: 生成 F23 restart focus 摘要 ...")
    f23_restart_summary(root, out_dir, inventory, args)

    print_line("")
    print_line("Step 6/7: 检查 main.tex 的 figure/input 路径 ...")
    check_tex_assets(root, out_dir, inventory)

    print_line("")
    print_line("Step 7/7: 生成 markdown 报告 ...")
    generate_markdown_report(root, out_dir)

    zip_output(root, out_dir, zip_path)

    elapsed = time.time() - start_all
    print_line("")
    print_line("=" * 88)
    print_line("审计完成。")
    print_line(f"输出文件夹：{out_dir}")
    print_line(f"压缩包：{zip_path}")
    print_line(f"压缩包大小：{file_size_mb(zip_path):.2f} MB")
    print_line(f"耗时：{elapsed:.2f} 秒")
    print_line("=" * 88)
    print_line("")
    print_line("把 project_audit_pack.zip 上传给 ChatGPT 即可。")
    print_line("不要再上传 1GB 的 ablation6_restart_details.csv 原文件。")


if __name__ == "__main__":
    main()
