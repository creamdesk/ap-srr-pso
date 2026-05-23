"""Audit experiment result files for schema, failure, and numeric-quality issues."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RAW_REQUIRED = [
    "experiment_name",
    "benchmark",
    "function",
    "function_id",
    "dimension",
    "algorithm",
    "run",
    "seed",
    "population_size",
    "max_fes",
    "best_fitness",
    "function_evaluations",
    "runtime_seconds",
    "status",
    "error",
]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def audit_raw(path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "file": _rel(path),
        "exists": path.exists(),
        "kind": "raw",
        "rows": 0,
        "ok_rows": 0,
        "failed_rows": 0,
        "missing_columns": [],
        "nan_best_fitness": 0,
        "inf_best_fitness": 0,
        "nan_runtime": 0,
        "duplicate_tasks": 0,
        "status": "failed",
        "errors": [],
    }
    if not path.exists():
        report["errors"].append("file does not exist")
        return report
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        report["errors"].append(f"cannot read csv: {exc!r}")
        return report

    report["rows"] = int(len(df))
    missing = [col for col in RAW_REQUIRED if col not in df.columns]
    report["missing_columns"] = missing
    if missing:
        report["errors"].append("missing required columns")
        return report

    status = df["status"].fillna("failed").astype(str)
    report["ok_rows"] = int((status == "ok").sum())
    report["failed_rows"] = int((status != "ok").sum())

    best = pd.to_numeric(df["best_fitness"], errors="coerce")
    runtime = pd.to_numeric(df["runtime_seconds"], errors="coerce")
    report["nan_best_fitness"] = int(best.isna().sum())
    report["inf_best_fitness"] = int((best.apply(lambda x: isinstance(x, float) and math.isinf(x))).sum())
    report["nan_runtime"] = int(runtime.isna().sum())

    key_cols = ["benchmark", "function_id", "dimension", "algorithm", "run"]
    report["duplicate_tasks"] = int(df.duplicated(subset=key_cols).sum())

    if report["rows"] == 0:
        report["errors"].append("empty raw csv")
    if report["duplicate_tasks"]:
        report["errors"].append("duplicate task rows detected")
    if report["ok_rows"] == 0:
        report["errors"].append("no successful rows")

    report["status"] = "ok" if not report["errors"] else "warning"
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit AP-SRR-PSO result CSV files.")
    parser.add_argument("--input", required=True, help="Raw CSV path relative to repository root.")
    parser.add_argument("--output", default="", help="Optional JSON report output path.")
    args = parser.parse_args()

    input_path = PROJECT_ROOT / args.input
    report = audit_raw(input_path)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text)

    if args.output:
        out = PROJECT_ROOT / args.output
    else:
        out = PROJECT_ROOT / "results" / "summary" / f"{input_path.stem}_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text + "\n", encoding="utf-8")
    print(f"audit report saved: {out}")

    if report["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
