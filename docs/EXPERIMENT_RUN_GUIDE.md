# Experiment Run Guide

This guide separates engineering checks from formal paper experiments.

## Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip wheel
.\.venv\Scripts\python -m pip install -r requirements.txt
```

`requirements.txt` pins `setuptools<81` because `opfunu` imports `pkg_resources`.

## Engineering Checks

Smoke test:

```powershell
.\.venv\Scripts\python experiments\smoke_test.py
```

Mini validation dry-run:

```powershell
.\.venv\Scripts\python experiments\run_cec2017_mini_validation.py --dry-run
```

30D probe dry-run:

```powershell
.\.venv\Scripts\python experiments\run_cec2017_30d_probe.py --dry-run
```

Main runner dry-run:

```powershell
.\.venv\Scripts\python experiments\run_experiment.py `
  --benchmark CEC2017 `
  --dimension 30 `
  --functions 1 3 5 10 13 20 `
  --algorithms PSO PSO-RS PSO-AW ARPSO-SRR AP-SRR-PSO DE `
  --runs 5 `
  --max-fes 50000 `
  --population-size 50 `
  --base-seed 20260523 `
  --output results/raw/cec2017_30d_pilot.csv `
  --dry-run
```

## Pilot

30D pilot should use a small function subset and 5 runs:

```powershell
.\.venv\Scripts\python experiments\run_experiment.py `
  --benchmark CEC2017 `
  --dimension 30 `
  --functions 1 3 5 10 13 20 `
  --algorithms PSO PSO-RS PSO-AW ARPSO-SRR AP-SRR-PSO DE `
  --runs 5 `
  --max-fes 50000 `
  --population-size 50 `
  --base-seed 20260523 `
  --output results/raw/cec2017_30d_pilot.csv `
  --n-jobs 1
```

Pilot results are not formal paper results.

## Formal 30D Main Experiment

Formal settings:

- CEC2017 F1-F30
- dimension = 30
- runs = 30
- max_fes = 300000
- population_size = 50

Use conservative local parallelism on this computer. For the current 4-core/8-thread CPU, start with `--n-jobs 1` to `--n-jobs 4`. Do not blindly use cloud-scale settings locally.

## Analysis

Summary:

```powershell
.\.venv\Scripts\python analysis\summarize_results.py --input results/raw/cec2017_30d_pilot.csv
```

Statistics:

```powershell
.\.venv\Scripts\python analysis\statistical_tests.py --input results/raw/cec2017_30d_pilot.csv --target AP-SRR-PSO
```

Average-rank vector figure:

```powershell
.\.venv\Scripts\python analysis\plot_results.py `
  --rank-csv results/stats/cec2017_30d_pilot_average_rank.csv `
  --output results/figures/average_rank.pdf
```

Formal figures must be PDF/SVG. PNG is preview only.
