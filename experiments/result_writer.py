"""Result writing, JSON serialization, and summary helpers."""
from __future__ import annotations

import csv
import json
import logging
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_FIELDS = [
    "experiment_name", "benchmark", "function", "function_id", "dimension",
    "algorithm", "run", "run_id", "seed", "population_size", "max_fes",
    "best_fitness", "error_value", "function_evaluations", "runtime_seconds",
    "restart_count", "operator_usage", "operator_success", "status", "success_flag", "error",
]
SUMMARY_FIELDS = [
    "experiment_name", "benchmark", "function", "function_id", "dimension",
    "algorithm", "runs", "mean_best", "std_best", "median_best", "best", "worst",
    "mean_runtime_seconds", "total_runtime_seconds", "success_count", "failure_count",
]


def ensure_result_dirs(project_root: Path = PROJECT_ROOT) -> dict[str, Path]:
    folders = {
        "raw": project_root / "results" / "raw",
        "summary": project_root / "results" / "summary",
        "logs": project_root / "results" / "logs",
        "curves": project_root / "results" / "curves",
        "stats": project_root / "results" / "stats",
        "figures": project_root / "results" / "figures",
        "tables": project_root / "results" / "tables",
    }
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    return folders


def json_safe(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        v = float(value)
        return None if not math.isfinite(v) else v
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def json_dumps(value: Any) -> str:
    if value in (None, ""):
        return "{}"
    return json.dumps(json_safe(value), ensure_ascii=False, sort_keys=True)


def task_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("benchmark", "")),
        str(row.get("function_id", "")),
        str(row.get("dimension", "")),
        str(row.get("algorithm", "")),
        str(row.get("run", "")),
    )


def load_existing_rows(raw_file: Path) -> list[dict[str, str]]:
    if not raw_file.exists():
        return []
    with raw_file.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_completed_tasks(raw_file: Path) -> set[tuple[str, str, str, str, str]]:
    return {task_key(row) for row in load_existing_rows(raw_file) if row.get("status") == "ok"}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(normalized)


def append_curve_jsonl(curve_file: Path, curve_rows: list[dict[str, Any]]) -> None:
    curve_file.parent.mkdir(parents=True, exist_ok=True)
    with curve_file.open("a", encoding="utf-8") as f:
        for row in curve_rows:
            f.write(json.dumps(json_safe(row), ensure_ascii=False, sort_keys=True) + "\n")


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        fid = int(row.get("function_id") or 0)
        dim = int(row.get("dimension") or 0)
        key = (str(row.get("benchmark", "")), str(row.get("function", f"F{fid}")), dim, str(row.get("algorithm", "")))
        groups[key].append(row)
    summary: list[dict[str, Any]] = []
    for (benchmark, function, dimension, algorithm), group in sorted(groups.items()):
        successes = [r for r in group if r.get("status") == "ok"]
        failures = [r for r in group if r.get("status") != "ok"]
        best_values = [float(r["best_fitness"]) for r in successes if str(r.get("best_fitness", "")) != ""]
        runtimes = [float(r["runtime_seconds"]) for r in successes if str(r.get("runtime_seconds", "")) != ""]
        fid = int(str(function).lstrip("Ff")) if str(function).lstrip("Ff").isdigit() else ""
        summary.append({
            "experiment_name": group[0].get("experiment_name", ""),
            "benchmark": benchmark,
            "function": function,
            "function_id": fid,
            "dimension": dimension,
            "algorithm": algorithm,
            "runs": len(group),
            "mean_best": float(np.mean(best_values)) if best_values else "",
            "std_best": float(np.std(best_values, ddof=1)) if len(best_values) > 1 else (0.0 if best_values else ""),
            "median_best": float(np.median(best_values)) if best_values else "",
            "best": float(np.min(best_values)) if best_values else "",
            "worst": float(np.max(best_values)) if best_values else "",
            "mean_runtime_seconds": float(np.mean(runtimes)) if runtimes else "",
            "total_runtime_seconds": float(np.sum(runtimes)) if runtimes else "",
            "success_count": len(successes),
            "failure_count": len(failures),
        })
    return summary


def configure_logger(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(log_file.stem)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(sh)
    return logger
