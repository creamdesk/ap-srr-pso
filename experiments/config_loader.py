"""Configuration loading utilities for AP-SRR-PSO experiments."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def parse_int_list(value: str | None) -> list[int] | None:
    if value is None or value == "":
        return None
    return [int(part.strip().lstrip("Ff")) for part in value.split(",") if part.strip()]


def parse_str_list(value: str | None) -> list[str] | None:
    if value is None or value == "":
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def load_yaml_config(config_path: str | Path) -> dict[str, Any]:
    path = project_path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def apply_cli_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    cfg = dict(config)
    for key in ["dimension", "max_fes", "runs", "population_size", "record_interval", "n_jobs", "base_seed"]:
        value = getattr(args, key, None)
        if value is not None:
            cfg[key] = value
    functions = parse_int_list(getattr(args, "functions", None))
    if functions is not None:
        cfg["functions"] = functions
    algorithms = parse_str_list(getattr(args, "algorithms", None))
    if algorithms is not None:
        cfg["algorithms"] = algorithms
    return cfg


def add_common_runner_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--config", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-fes", type=int, default=None)
    parser.add_argument("--runs", type=int, default=None)
    parser.add_argument("--functions", default=None)
    parser.add_argument("--dimension", type=int, default=None)
    parser.add_argument("--algorithms", default=None)
    parser.add_argument("--population-size", type=int, default=None)
    parser.add_argument("--record-interval", type=int, default=None)
    parser.add_argument("--n-jobs", type=int, default=None)
    parser.add_argument("--base-seed", type=int, default=None)
    parser.add_argument("--confirm-formal-run", action="store_true")
    return parser
