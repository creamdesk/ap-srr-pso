# Codex Completion Report

Date: 2026-05-24

## 1. Modified Files

Core entry points and CI:

- `.github/workflows/tests.yml`
- `README.md`
- `algorithms/factory.py`
- `experiments/run_ablation6.py`
- `configs/ablation6.yaml`
- `analysis/generate_tables.py`
- `analysis/generate_figures.py`

Validation:

- `tests/test_factory.py`
- `tests/test_validate_configs.py`

This report:

- `docs/CODEX_COMPLETION_REPORT.md`

## 2. Fixed Problems

- Confirmed the latest GitHub Actions workflow is passing on `main`.
- Inspected recent failed GitHub Actions runs. The actionable historical failure was an import mismatch: `tests/test_pipeline_contracts.py` imported `build_tasks`, which was not available in the earlier `experiments.run_experiment` version at that commit.
- Confirmed a separate CI warning from older `actions/checkout@v4` and `actions/setup-python@v5` using deprecated Node.js 20 actions. The current workflow uses newer actions and the latest run passes.
- Added CI checks for module-based command entry points:
  - `python -m experiments.smoke_test`
  - `python -m experiments.run_ablation6 --dry-run`
  - `python -m experiments.run_cec2017_main --dry-run`
  - `python -m analysis.generate_tables`
  - `python -m analysis.generate_figures`

## 3. New Commands

Smoke test:

```bash
python -m experiments.smoke_test
```

Six-group ARPSO-SRR ablation dry-run:

```bash
python -m experiments.run_ablation6 --dry-run
```

Six-group ARPSO-SRR ablation pilot:

```bash
python -m experiments.run_ablation6
```

Protected CEC2017 main experiment dry-run:

```bash
python -m experiments.run_cec2017_main --dry-run
```

Generate paper tables from existing outputs:

```bash
python -m analysis.generate_tables --experiment cec2017_30d_probe
```

Generate paper figures from existing outputs:

```bash
python -m analysis.generate_figures --experiment cec2017_30d_probe --no-png
```

## 4. Ablation6 Definition

The six ablation groups are now configured in `configs/ablation6.yaml` and exposed via `experiments/run_ablation6.py`:

- `ARPSO-Local`: local-only reallocation through `local_ratio=1.0`.
- `ARPSO-SRR`: original adaptive local/global search resource reallocation.
- `ARPSO-EIS`: elite-guided opposition/inverse-search variant implemented through opposition-only reallocation.
- `ARPSO-Fixed`: fixed restart intensity with `rho_min=rho_max=0.20`.
- `ARPSO-Global`: global-only reallocation through `local_ratio=0.0`.
- `PSO-RS`: random restart PSO baseline.

These are mechanism-level variants, not aliases with only display-name changes.

## 5. Tests Passed

Local verification:

```bash
python -m experiments.smoke_test
pytest
```

Expected CI verification:

```bash
python -m experiments.smoke_test
python -m experiments.validate_configs configs/mini_validation.yaml configs/cec2017_30d_probe.yaml configs/cec2017_30d_pilot.yaml configs/ablation6.yaml
python -m experiments.run_ablation6 --dry-run
python -m experiments.run_cec2017_main --dry-run
python -m analysis.generate_tables --experiment ci_missing
python -m analysis.generate_figures --experiment ci_missing --no-png
python -m pytest tests -q
```

## 6. Not Fully Complete Yet

- Stronger baselines such as CLPSO, HPSO-TVAC, JADE/SHADE, and CMA-ES are not yet fully implemented.
- `ARPSO-EIS` should be reviewed against the final paper terminology before formal submission.
- Full formal CEC2017 30D experiments are intentionally not run in CI.
- Formal paper figures and tables require real pilot/formal output CSVs.
- The current ablation6 default config is a pilot-scale setting, not a 30-run formal result.

## 7. How to Run the Complete Experiment Pipeline

Recommended sequence:

1. Install dependencies.
2. Run smoke test.
3. Run ablation6 dry-run.
4. Run 30D pilot.
5. Generate summary/statistics.
6. Generate tables and figures.
7. Only then run protected formal CEC2017 main experiment.

Example:

```bash
python -m experiments.smoke_test
python -m experiments.run_ablation6 --dry-run
python -m experiments.run_cec2017_pilot
python -m analysis.generate_tables --experiment cec2017_30d_pilot
python -m analysis.generate_figures --experiment cec2017_30d_pilot --no-png
python -m experiments.run_cec2017_main --dry-run
python -m experiments.run_cec2017_main --confirm-formal-run
```

Do not treat smoke, mini, probe, or pilot outputs as formal paper evidence.
