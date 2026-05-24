"""Validate AP-SRR-PSO experiment YAML configurations without running experiments."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithms.factory import build_optimizer

REQUIRED_FIELDS = [
    "experiment_name",
    "benchmark",
    "dimension",
    "functions",
    "algorithms",
    "population_size",
    "max_fes",
    "runs",
    "base_seed",
]


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    if not isinstance(cfg, dict):
        raise ValueError(f"{path}: config must be a mapping")
    return cfg


def normalize_config(cfg: dict[str, Any]) -> dict[str, Any]:
    """Accept small smoke-style configs while validating the common experiment schema."""
    out = dict(cfg)
    if "algorithms" not in out and "algorithm" in out:
        out["algorithms"] = [out["algorithm"]]
    if "base_seed" not in out and "seed" in out:
        out["base_seed"] = out["seed"]
    if "functions" not in out and str(out.get("benchmark", "")).lower() == "sphere":
        out["functions"] = [out.get("function_id", 1)]
    return out


def _as_int(value: Any, name: str, path: Path) -> int:
    try:
        out = int(value)
    except Exception as exc:
        raise ValueError(f"{path}: {name} must be an integer, got {value!r}") from exc
    return out


def validate_config(path: Path) -> list[str]:
    cfg = normalize_config(load_config(path))
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in cfg:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors

    dimension = _as_int(cfg["dimension"], "dimension", path)
    population_size = _as_int(cfg["population_size"], "population_size", path)
    max_fes = _as_int(cfg["max_fes"], "max_fes", path)
    runs = _as_int(cfg["runs"], "runs", path)
    record_interval = _as_int(cfg.get("record_interval", 10), "record_interval", path)
    n_jobs = _as_int(cfg.get("n_jobs", 1), "n_jobs", path)

    if dimension <= 0:
        errors.append("dimension must be positive")
    if population_size <= 0:
        errors.append("population_size must be positive")
    if max_fes <= 0:
        errors.append("max_fes must be positive")
    if runs <= 0:
        errors.append("runs must be positive")
    if record_interval <= 0:
        errors.append("record_interval must be positive")
    if n_jobs <= 0:
        errors.append("n_jobs must be positive")

    functions = cfg.get("functions")
    if not isinstance(functions, list) or not functions:
        errors.append("functions must be a non-empty list")
    else:
        for fid in functions:
            try:
                fid_int = int(fid)
            except Exception:
                errors.append(f"function id must be integer-like: {fid!r}")
                continue
            if str(cfg.get("benchmark", "")).upper() == "CEC2017" and not (1 <= fid_int <= 30):
                errors.append(f"CEC2017 function id out of range: {fid_int}")

    algorithms = cfg.get("algorithms")
    if not isinstance(algorithms, list) or not algorithms:
        errors.append("algorithms must be a non-empty list")
    else:
        for name in algorithms:
            try:
                build_optimizer(str(name), population_size=min(max(population_size, 2), 8), seed=1)
            except Exception as exc:
                errors.append(f"unsupported algorithm {name!r}: {exc!r}")

    return errors


def iter_config_paths(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p) if Path(p).is_absolute() else PROJECT_ROOT / p for p in paths]
    return sorted((PROJECT_ROOT / "configs").glob("*.yaml"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate experiment YAML configs without running optimization.")
    parser.add_argument("configs", nargs="*", help="Config files. Defaults to configs/*.yaml")
    args = parser.parse_args()

    total_errors = 0
    for path in iter_config_paths(args.configs):
        errors = validate_config(path)
        if errors:
            total_errors += len(errors)
            print(f"[failed] {path.relative_to(PROJECT_ROOT)}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[ok] {path.relative_to(PROJECT_ROOT)}")

    if total_errors:
        raise SystemExit(f"config validation failed with {total_errors} error(s)")
    print("all configs passed validation")


if __name__ == "__main__":
    main()
