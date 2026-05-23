# Experiment Run Guide

This guide records safe commands for the AP-SRR-PSO experiment pipeline.

## Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip "setuptools<81" wheel
pip install -r requirements.txt
```

## Safe validation

```powershell
.\.venv\Scripts\python experiments\smoke_test.py
.\.venv\Scripts\python experiments\run_cec2017_30d_probe.py --dry-run
.\.venv\Scripts\python experiments\run_cec2017_main.py --dry-run
.\.venv\Scripts\python experiments\check_cec2017_availability.py
.\.venv\Scripts\python -m pytest tests -q
```

## Mini validation

```powershell
.\.venv\Scripts\python experiments\run_cec2017_mini_validation.py
```

Mini validation is an engineering check only. It must not be cited as formal paper evidence.

## 30D probe

```powershell
.\.venv\Scripts\python experiments\run_cec2017_30d_probe.py --dry-run
.\.venv\Scripts\python experiments\run_cec2017_30d_probe.py
```

## Pilot

```powershell
.\.venv\Scripts\python experiments\run_cec2017_pilot.py --dry-run
```

## Formal experiment protection

The formal main experiment is protected:

```powershell
.\.venv\Scripts\python experiments\run_cec2017_main.py --dry-run
```

Only after probe and pilot are stable:

```powershell
.\.venv\Scripts\python experiments\run_cec2017_main.py --confirm-formal-run --resume
```

## Resume

All reusable experiment entries support `--resume`, which skips rows already marked `status=ok` in the raw CSV.

## Notes

Do not commit `results/`. Formal figures should be PDF/SVG. PNG is preview only.
