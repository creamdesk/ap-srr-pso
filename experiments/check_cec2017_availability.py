"""Check CEC2017 function availability in current opfunu environment."""
from __future__ import annotations
import argparse, csv, sys, time
from pathlib import Path
import numpy as np
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from benchmarks.problem_factory import build_problem

def main() -> None:
    parser = argparse.ArgumentParser(description="Check CEC2017 F1-F30 availability.")
    parser.add_argument("--dimension", type=int, default=10)
    parser.add_argument("--output", default="results/summary/cec2017_availability.csv")
    args = parser.parse_args()
    out = PROJECT_ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for fid in range(1, 31):
        start = time.perf_counter()
        row = {"benchmark":"CEC2017", "function_id":fid, "dimension":args.dimension, "status":"failed", "value_at_zero":"", "runtime_seconds":"", "error":""}
        try:
            p = build_problem("CEC2017", function_id=fid, dimension=args.dimension)
            value = float(p.objective(np.zeros(p.dimension)))
            row.update({"status":"ok", "value_at_zero":value, "runtime_seconds":time.perf_counter()-start})
            print(f"CEC2017 F{fid}: ok value={value:.6e}")
        except Exception as exc:
            row.update({"runtime_seconds":time.perf_counter()-start, "error":repr(exc)})
            print(f"CEC2017 F{fid}: failed error={exc!r}")
        rows.append(row)
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["benchmark","function_id","dimension","status","value_at_zero","runtime_seconds","error"])
        w.writeheader(); w.writerows(rows)
    ok = sum(1 for r in rows if r["status"] == "ok")
    print(f"availability finished: ok={ok} failed={len(rows)-ok}")
    print(f"output: {out}")

if __name__ == "__main__":
    main()
