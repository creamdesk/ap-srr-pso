# Local Run Guide

The current local machine profile is suitable for engineering validation and small pilots, not for the full formal experiment in one shot.

## Suitable local tasks

- smoke test
- factory checks
- CEC2017 availability check
- mini validation
- 30D probe
- small 30D pilot
- plotting, table generation, and statistical script validation

## Not recommended locally

Do not start the full formal configuration locally without careful planning:

```text
CEC2017 F1-F30 * 30 runs * multiple algorithms * 300000 FEs
```

This is a large CPU-bound workload. It may take a long time on a 4-core/8-thread laptop and can be interrupted by sleep, overheating, or system updates.

## Local validation sequence

```powershell
cd "D:\github repository\ap-srr-pso"
.\.venv\Scripts\python experiments\smoke_test.py
.\.venv\Scripts\python experiments\run_cec2017_mini_validation.py --dry-run
.\.venv\Scripts\python experiments\run_cec2017_30d_probe.py --dry-run
.\.venv\Scripts\python experiments\run_cec2017_main.py --dry-run
.\.venv\Scripts\python experiments\check_cec2017_availability.py
.\.venv\Scripts\python -m pytest tests -q
```

## Local parallelism

Start with `n_jobs=1`. If stable, try `n_jobs=2`. Avoid blindly using all logical threads on a thin laptop.

## Disk usage

Keep results on the D drive. Do not write large experiment outputs to the C drive. Keep `results/` ignored by Git.

## Practical sequence

1. Run dry-runs.
2. Run CEC2017 availability check.
3. Run 30D probe.
4. Inspect raw and summary CSV.
5. Generate vector figures from probe data.
6. Only then run 30D pilot.
