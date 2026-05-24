"""Reusable experiment runner for AP-SRR-PSO experiments."""
from __future__ import annotations
import argparse, csv, json, sys, time, traceback
from pathlib import Path
import yaml
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from algorithms.factory import build_optimizer
from benchmarks.problem_factory import build_problem

RAW_FIELDS = [
    "experiment_name","benchmark","function","function_id","dimension","algorithm","run","run_id","seed",
    "population_size","max_fes","best_fitness","error_value","function_evaluations","runtime_seconds",
    "restart_count","operator_usage","operator_success","status","success_flag","error",
]
SUMMARY_FIELDS = ["experiment_name","benchmark","function","function_id","dimension","algorithm","runs","mean_best","std_best","median_best","best","worst","mean_runtime_seconds","total_runtime_seconds","success_count","failure_count"]

def _path(p):
    p = Path(p)
    return p if p.is_absolute() else PROJECT_ROOT / p

def _csv_list(v, cast=str):
    if v is None or v == "": return None
    return [cast(x.strip().lstrip("Ff")) for x in v.split(",") if x.strip()]

def load_config(path):
    with _path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def apply_overrides(cfg, a):
    cfg = dict(cfg)
    for k in ["dimension","max_fes","runs","population_size","record_interval","n_jobs","base_seed"]:
        val = getattr(a, k, None)
        if val is not None: cfg[k] = val
    fs = _csv_list(getattr(a, "functions", None), int)
    if fs is not None: cfg["functions"] = fs
    algs = _csv_list(getattr(a, "algorithms", None), str)
    if algs is not None: cfg["algorithms"] = algs
    return cfg

def seed(base, fid, ai, run):
    return int(base) + int(fid) * 100000 + int(ai) * 1000 + int(run)

def tasks(cfg):
    out=[]; algs=list(map(str,cfg.get("algorithms",["PSO","AP-SRR-PSO"])))
    for fid in map(int,cfg.get("functions",[1,3,10])):
        for ai, alg in enumerate(algs):
            for r in range(1, int(cfg.get("runs",1))+1):
                out.append(dict(experiment_name=cfg.get("experiment_name","experiment"), benchmark=cfg.get("benchmark","CEC2017"), function_id=fid, dimension=int(cfg.get("dimension",30)), algorithm=alg, run=r, seed=seed(cfg.get("base_seed",20260523),fid,ai,r), population_size=int(cfg.get("population_size",30)), max_fes=int(cfg.get("max_fes",10000)), record_interval=int(cfg.get("record_interval",10))))
    return out

def dirs():
    d = {k: PROJECT_ROOT/"results"/k for k in ["raw","summary","logs","curves","stats","figures","tables"]}
    for p in d.values(): p.mkdir(parents=True, exist_ok=True)
    return d

def row_key(row):
    return tuple(str(row.get(k,"")) for k in ["benchmark","function_id","dimension","algorithm","run"])

def read_existing(path):
    if not path.exists(): return []
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows([{k:r.get(k,"") for k in fields} for r in rows])

def jdump(x):
    try: return json.dumps(x if x is not None else {}, ensure_ascii=False, sort_keys=True)
    except TypeError: return json.dumps(str(x), ensure_ascii=False)

def run_one(t):
    st=time.perf_counter()
    base={"experiment_name":t["experiment_name"],"benchmark":t["benchmark"],"function":f"F{t['function_id']}","function_id":t["function_id"],"dimension":t["dimension"],"algorithm":t["algorithm"],"run":t["run"],"run_id":t["run"],"seed":t["seed"],"population_size":t["population_size"],"max_fes":t["max_fes"],"best_fitness":"","error_value":"","function_evaluations":"","runtime_seconds":"","restart_count":"","operator_usage":"{}","operator_success":"{}","status":"failed","success_flag":0,"error":""}
    try:
        p=build_problem(t["benchmark"], t["function_id"], t["dimension"])
        opt=build_optimizer(t["algorithm"], population_size=t["population_size"], seed=t["seed"])
        res=opt.optimize(objective=p.objective, dimension=p.dimension, lower_bound=p.lower_bound, upper_bound=p.upper_bound, max_fes=t["max_fes"], record_interval=t["record_interval"])
        meta=dict(res.metadata or {})
        error_value = ""
        if getattr(p, "optimum", None) is not None:
            error_value = float(res.best_fitness) - float(p.optimum)
        base.update({"function":p.function,"algorithm":res.algorithm,"best_fitness":res.best_fitness,"error_value":error_value,"function_evaluations":res.function_evaluations,"runtime_seconds":time.perf_counter()-st,"restart_count":meta.get("restart_count",""),"operator_usage":jdump(meta.get("operator_usage",{})),"operator_success":jdump(meta.get("operator_success",{})),"status":"ok","success_flag":1})
        curve={"experiment_name":t["experiment_name"],"benchmark":t["benchmark"],"function":p.function,"function_id":t["function_id"],"dimension":t["dimension"],"algorithm":res.algorithm,"run":t["run"],"seed":t["seed"],"convergence_curve":res.convergence_curve,"function_evaluations":res.function_evaluations}
        return base, curve
    except Exception as e:
        base.update({"runtime_seconds":time.perf_counter()-st,"error":repr(e)+" | "+traceback.format_exc(limit=5).replace("\n"," ")})
        return base, None

def summarize(rows):
    import numpy as np
    out=[]; groups={}
    for r in rows: groups.setdefault((r.get("benchmark"),r.get("function"),r.get("function_id"),r.get("dimension"),r.get("algorithm")),[]).append(r)
    for (b,f,fid,dim,alg),g in sorted(groups.items()):
        ok=[r for r in g if r.get("status")=="ok"]; vals=[float(r["best_fitness"]) for r in ok if str(r.get("best_fitness","") )!=""]; rt=[float(r["runtime_seconds"]) for r in ok if str(r.get("runtime_seconds","") )!=""]
        out.append({"experiment_name":g[0].get("experiment_name",""),"benchmark":b,"function":f,"function_id":fid,"dimension":dim,"algorithm":alg,"runs":len(g),"mean_best":float(np.mean(vals)) if vals else "","std_best":float(np.std(vals,ddof=1)) if len(vals)>1 else (0.0 if vals else ""),"median_best":float(np.median(vals)) if vals else "","best":float(np.min(vals)) if vals else "","worst":float(np.max(vals)) if vals else "","mean_runtime_seconds":float(np.mean(rt)) if rt else "","total_runtime_seconds":float(np.sum(rt)) if rt else "","success_count":len(ok),"failure_count":len(g)-len(ok)})
    return out

def curve_csv_rows(curves):
    rows=[]
    for row in curves:
        curve=list(row.get("convergence_curve") or [])
        if not curve:
            continue
        total_fe=int(row.get("function_evaluations") or 0)
        denom=max(1, len(curve)-1)
        for idx, value in enumerate(curve):
            fe=int(round(total_fe * idx / denom)) if len(curve)>1 else total_fe
            rows.append({"algorithm":row.get("algorithm",""),"function_id":row.get("function_id",""),"run_id":row.get("run",""),"fe":fe,"best_so_far":value})
    return rows

def run_experiment(cfg, dry_run=False, resume=False, formal=False, confirm=False):
    if formal and not dry_run and not confirm: raise RuntimeError("Formal experiment is protected; pass --confirm-formal-run after pilot validation.")
    ds=dirs(); name=cfg.get("experiment_name","experiment"); ts=tasks(cfg)
    raw=ds["raw"]/f"{name}_raw.csv"; summ=ds["summary"]/f"{name}_summary.csv"; curves=ds["curves"]/f"{name}_curves.jsonl"; conv=ds["raw"]/f"{name}_convergence.csv"
    if dry_run:
        print("DRY RUN"); print(f"experiment={name} tasks={len(ts)} functions={cfg.get('functions')} algorithms={cfg.get('algorithms')} runs={cfg.get('runs')} max_fes={cfg.get('max_fes')}")
        for t in ts[:20]: print(f"task F{t['function_id']} {t['algorithm']} run={t['run']} seed={t['seed']}")
        return {"dry_run":True,"planned_tasks":len(ts)}
    existing=read_existing(raw) if resume else []; done={row_key(r) for r in existing if r.get("status")=="ok"}; rows=[]; curve_rows=[]
    if not resume and curves.exists():
        curves.unlink()
    for t in ts:
        if resume and row_key(t) in done: continue
        print(f"[{name}][F{t['function_id']}][{t['algorithm']}][run {t['run']}] running...", flush=True)
        r,c=run_one(t); print(f"status={r['status']} best={r.get('best_fitness')} time={r.get('runtime_seconds')}", flush=True); rows.append(r)
        if c: curve_rows.append(c)
    all_rows=existing+rows; write_csv(raw, all_rows, RAW_FIELDS); write_csv(summ, summarize(all_rows), SUMMARY_FIELDS)
    with curves.open("a",encoding="utf-8") as f:
        for c in curve_rows: f.write(json.dumps(c,ensure_ascii=False)+"\n")
    write_csv(conv, curve_csv_rows(curve_rows), ["algorithm","function_id","run_id","fe","best_so_far"])
    print(f"raw: {raw}\nsummary: {summ}\ncurves: {curves}\nconvergence_csv: {conv}")
    return {"dry_run":False,"planned_tasks":len(ts)}

def cli_main(default_config, description, formal=False):
    ap=argparse.ArgumentParser(description=description); ap.add_argument("--config",default=""); ap.add_argument("--dry-run",action="store_true"); ap.add_argument("--resume",action="store_true"); ap.add_argument("--max-fes",type=int); ap.add_argument("--runs",type=int); ap.add_argument("--functions"); ap.add_argument("--dimension",type=int); ap.add_argument("--algorithms"); ap.add_argument("--population-size",type=int); ap.add_argument("--record-interval",type=int); ap.add_argument("--n-jobs",type=int); ap.add_argument("--base-seed",type=int); ap.add_argument("--confirm-formal-run",action="store_true")
    a=ap.parse_args(); cfg=apply_overrides(load_config(a.config or default_config), a); run_experiment(cfg,dry_run=a.dry_run,resume=a.resume,formal=formal,confirm=a.confirm_formal_run)
