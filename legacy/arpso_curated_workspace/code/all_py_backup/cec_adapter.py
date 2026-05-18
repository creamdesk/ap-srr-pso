# -*- coding: utf-8 -*-
"""
CEC benchmark adapter based on OPFUNU.

Recommended environment:
    Python 3.11
    pip install opfunu==1.0.4

Important note for CEC2017:
    In many OPFUNU versions, CEC2017 is implemented as F12017-F292017.
    The commonly used CEC2017 setting excludes official F2 and uses 29
    functions: F1 and F3-F30.

    Therefore this adapter maps official CEC2017 IDs as follows:
        official F1  -> OPFUNU F12017
        official F3  -> OPFUNU F22017
        official F4  -> OPFUNU F32017
        ...
        official F30 -> OPFUNU F292017

    This fixes the old problem where F30 was skipped because OPFUNU has no
    class named F302017.
"""

import importlib
import platform
import sys
from collections import OrderedDict

import numpy as np


CEC2017_OFFICIAL_IDS = [1] + list(range(3, 31))
CEC2022_OFFICIAL_IDS = list(range(1, 13))


def _to_float_scalar(value, default=0.0, name="value"):
    """Convert OPFUNU scalar/array attributes to a Python float safely."""
    if value is None:
        return float(default)

    arr = np.asarray(value, dtype=float)
    if arr.size == 0:
        return float(default)

    arr = arr.reshape(-1)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return float(default)

    # Most attributes such as f_global/f_bias are scalars. If a library version
    # returns a length-1 array, use that single value. If it unexpectedly returns
    # a vector, use the first finite value and keep running with debug metadata.
    return float(finite[0])


def _to_float_bound(value, default, mode, name="bound"):
    """Convert OPFUNU lb/ub attributes to scalar bounds.

    OPFUNU 1.0.x may store lb/ub as arrays, e.g. [-100, ..., -100].
    The optimization code in this project expects scalar bounds, so lower bounds
    use min(array) and upper bounds use max(array).
    """
    if value is None:
        return float(default)

    arr = np.asarray(value, dtype=float)
    if arr.size == 0:
        return float(default)

    arr = arr.reshape(-1)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return float(default)

    if mode == "lower":
        return float(np.min(finite))
    if mode == "upper":
        return float(np.max(finite))

    raise ValueError(f"Unknown bound conversion mode: {mode}")


def get_environment_info():
    """Return basic runtime information for debugging."""
    info = {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "numpy": getattr(np, "__version__", "unknown"),
    }

    try:
        import opfunu  # pylint: disable=import-outside-toplevel
        info["opfunu"] = getattr(opfunu, "__version__", "unknown")
    except Exception as exc:  # pragma: no cover - only for diagnostics
        info["opfunu"] = f"not importable: {exc}"

    return info


def _import_cec_module(year):
    module_name = f"opfunu.cec_based.cec{year}"

    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise ImportError(
            "Cannot import OPFUNU CEC module. Please install OPFUNU first:\n"
            "    pip install opfunu==1.0.4\n"
            "If Python 3.13 causes dependency problems, use Python 3.11.\n"
            f"Failed module: {module_name}\n"
            f"Original error: {exc}"
        ) from exc


def _cec2017_internal_fid(official_fid):
    """
    Convert official CEC2017 function ID to OPFUNU internal class ID.

    Official CEC2017 experimental practice usually uses 29 functions:
    F1 and F3-F30. Official F2 is excluded.
    """
    if official_fid == 1:
        return 1

    if official_fid == 2:
        raise ValueError(
            "Official CEC2017 F2 is excluded in the common 29-function setup. "
            "Please use function_ids=[1]+list(range(3,31))."
        )

    if 3 <= official_fid <= 30:
        return official_fid - 1

    raise ValueError(f"Illegal official CEC2017 function ID: F{official_fid}")


def _resolve_cec_class(year, official_fid, debug=False):
    """
    Resolve a CEC function class.

    Returns
    -------
    cls : type
        OPFUNU class.
    meta : dict
        Debug metadata including module/class names and ID mapping.
    """
    module = _import_cec_module(year)
    module_name = module.__name__

    candidates = []

    if year == 2017:
        internal_fid = _cec2017_internal_fid(official_fid)
        candidates.append((internal_fid, "mapped"))

        # Fallback for unusual OPFUNU versions that directly expose official IDs.
        if internal_fid != official_fid:
            candidates.append((official_fid, "direct-fallback"))
    else:
        candidates.append((official_fid, "direct"))

    tried = []
    for internal_fid, mode in candidates:
        class_name = f"F{internal_fid}{year}"
        tried.append(class_name)

        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            meta = {
                "year": year,
                "official_fid": official_fid,
                "internal_fid": internal_fid,
                "module_name": module_name,
                "class_name": class_name,
                "mapping_mode": mode,
            }
            if debug:
                print(
                    f"[CEC-LOAD] CEC{year}-F{official_fid:<2d} -> "
                    f"{module_name}.{class_name} ({mode})"
                )
            return cls, meta

    raise ValueError(
        f"Cannot find implementation for CEC{year}-F{official_fid}. "
        f"Tried classes: {', '.join(tried)} in {module_name}."
    )


def _instantiate_problem(cls, dim, official_fid=None):
    """Instantiate an OPFUNU problem, trying to preserve the official bias."""
    # Official CEC bias is usually 100 * FID. For subtract_bias=True this is not
    # essential, but setting it when supported makes raw objective values cleaner.
    official_bias = None
    if official_fid is not None:
        official_bias = float(100 * official_fid)

    if official_bias is not None:
        try:
            return cls(ndim=dim, f_bias=official_bias)
        except TypeError:
            pass

    problem = cls(ndim=dim)

    # Some older OPFUNU classes expose f_global/f_bias as writable attributes.
    if official_bias is not None:
        for attr in ("f_bias", "f_global"):
            if hasattr(problem, attr):
                try:
                    setattr(problem, attr, official_bias)
                except Exception:
                    # Not all OPFUNU versions allow assignment. It is safe to ignore.
                    pass

    return problem


def make_cec_function(year, fid, dim=30, subtract_bias=True, debug=False):
    """
    Create a CEC benchmark function.

    Parameters
    ----------
    year : int
        CEC benchmark year, such as 2017 or 2022.
    fid : int
        Official function ID. For CEC2017, use F1 and F3-F30.
    dim : int
        Problem dimension.
    subtract_bias : bool
        If True, return error value f(x) - f_global.
        This makes the optimum error equal to 0.
    debug : bool
        If True, print detailed OPFUNU class mapping information.

    Returns
    -------
    func : callable
        Batch-evaluation function. Input shape: (n, dim). Output shape: (n,).
    bounds : tuple
        Search range, usually (-100, 100).
    optimum : float
        0 if subtract_bias=True, otherwise the original global optimum bias.
    name : str
        Official benchmark name, e.g., CEC2017-F30.
    meta : dict
        Debug metadata.
    """
    cls, meta = _resolve_cec_class(year, fid, debug=debug)
    problem = _instantiate_problem(cls, dim=dim, official_fid=fid)

    raw_lb = getattr(problem, "lb", -100.0)
    raw_ub = getattr(problem, "ub", 100.0)

    lower = _to_float_bound(raw_lb, default=-100.0, mode="lower", name="lb")
    upper = _to_float_bound(raw_ub, default=100.0, mode="upper", name="ub")

    if not lower < upper:
        raise ValueError(
            f"Invalid bounds for CEC{year}-F{fid}: lower={lower}, upper={upper}, "
            f"raw_lb={raw_lb}, raw_ub={raw_ub}"
        )

    # OPFUNU usually stores the global optimum bias as f_global.
    f_global = _to_float_scalar(getattr(problem, "f_global", 0.0), default=0.0, name="f_global")
    f_bias = _to_float_scalar(getattr(problem, "f_bias", f_global), default=f_global, name="f_bias")

    # Prefer f_global because this is the value used as the known optimum.
    bias_to_subtract = f_global

    meta.update({
        "dim": dim,
        "lower": lower,
        "upper": upper,
        "f_global": f_global,
        "f_bias": f_bias,
        "subtract_bias": subtract_bias,
        "raw_lb_type": type(raw_lb).__name__,
        "raw_ub_type": type(raw_ub).__name__,
        "raw_lb_shape": tuple(np.asarray(raw_lb).shape),
        "raw_ub_shape": tuple(np.asarray(raw_ub).shape),
    })

    def func(x):
        x = np.asarray(x, dtype=float)

        if x.ndim == 1:
            x = x.reshape(1, -1)

        if x.ndim != 2 or x.shape[1] != dim:
            raise ValueError(
                f"Input shape mismatch for CEC{year}-F{fid}: "
                f"expected (*, {dim}), got {x.shape}"
            )

        values = []
        for row in x:
            value = float(problem.evaluate(row))
            if subtract_bias:
                value -= bias_to_subtract
            values.append(value)

        out = np.asarray(values, dtype=float)

        if not np.all(np.isfinite(out)):
            raise FloatingPointError(
                f"Non-finite objective value detected in CEC{year}-F{fid}: {out}"
            )

        return out

    optimum = 0.0 if subtract_bias else bias_to_subtract
    name = f"CEC{year}-F{fid}"

    return func, (lower, upper), optimum, name, meta


def get_cec2022_benchmarks(dim=30, function_ids=None, subtract_bias=True, strict=True, debug=False):
    """Return selected CEC2022 benchmark functions."""
    if function_ids is None:
        function_ids = CEC2022_OFFICIAL_IDS.copy()

    benchmarks = OrderedDict()
    skipped = []

    for fid in function_ids:
        try:
            func, bounds, optimum, name, meta = make_cec_function(
                year=2022,
                fid=fid,
                dim=dim,
                subtract_bias=subtract_bias,
                debug=debug,
            )
        except Exception as exc:
            skipped.append((fid, str(exc)))
            if strict:
                raise
            continue

        benchmarks[name] = {
            "func": func,
            "bounds": bounds,
            "optimum": optimum,
            "characteristics": "CEC2022 benchmark function",
            "meta": meta,
        }

    if skipped:
        print("[Warning] Some CEC2022 functions were skipped:")
        for fid, msg in skipped:
            print(f"  F{fid}: {msg.splitlines()[0]}")

    if not benchmarks:
        raise RuntimeError("No CEC2022 benchmark function was loaded successfully.")

    return benchmarks


def get_cec2017_benchmarks(dim=30, function_ids=None, subtract_bias=True, strict=True, debug=False):
    """
    Return selected CEC2017 benchmark functions.

    Default official IDs are 29 functions: F1 and F3-F30.
    This strict default prevents silent skipping of F30.
    """
    if function_ids is None:
        function_ids = CEC2017_OFFICIAL_IDS.copy()

    if 2 in function_ids:
        raise ValueError(
            "CEC2017 F2 should not be included in this 29-function experiment. "
            "Use [1] + list(range(3, 31))."
        )

    benchmarks = OrderedDict()
    skipped = []

    for fid in function_ids:
        try:
            func, bounds, optimum, name, meta = make_cec_function(
                year=2017,
                fid=fid,
                dim=dim,
                subtract_bias=subtract_bias,
                debug=debug,
            )
        except Exception as exc:
            skipped.append((fid, str(exc)))
            if strict:
                raise
            continue

        benchmarks[name] = {
            "func": func,
            "bounds": bounds,
            "optimum": optimum,
            "characteristics": "CEC2017 benchmark function",
            "meta": meta,
        }

    if skipped:
        print("[Warning] Some CEC2017 functions were skipped:")
        for fid, msg in skipped:
            print(f"  F{fid}: {msg.splitlines()[0]}")

    if not benchmarks:
        raise RuntimeError("No CEC2017 benchmark function was loaded successfully.")

    expected = [f"CEC2017-F{fid}" for fid in CEC2017_OFFICIAL_IDS]
    loaded = list(benchmarks.keys())

    if strict and list(function_ids) == CEC2017_OFFICIAL_IDS and loaded != expected:
        missing = [name for name in expected if name not in loaded]
        extra = [name for name in loaded if name not in expected]
        raise RuntimeError(
            "CEC2017 benchmark loading is incomplete.\n"
            f"Expected 29 functions: {expected}\n"
            f"Loaded {len(loaded)} functions: {loaded}\n"
            f"Missing: {missing}\n"
            f"Extra: {extra}"
        )

    return benchmarks


if __name__ == "__main__":
    print("Environment:")
    for k, v in get_environment_info().items():
        print(f"  {k}: {v}")

    print("\nLoading CEC2017 29-function suite...")
    suite = get_cec2017_benchmarks(dim=30, debug=True, strict=True)
    print(f"Loaded {len(suite)} functions:")
    print(", ".join(suite.keys()))

    print("\nSmoke test on CEC2017-F30 at x=0:")
    f30 = suite["CEC2017-F30"]["func"]
    x0 = np.zeros((2, 30))
    print(f30(x0))
