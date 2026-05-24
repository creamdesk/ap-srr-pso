# Pilot Pipeline Report

Date: 2026-05-24

This report records the real `ablation6_pilot` validation pipeline. The run is an engineering pilot only. It verifies that real optimization outputs can flow into CSV summaries, statistical CSVs, LaTeX tables, vector figures, and PGFPlots/TikZ sources. It is not a formal paper experiment.

## 1. Pilot Configuration

Config file:

- `configs/ablation6_pilot.yaml`

Effective settings:

- Benchmark: `CEC2017`
- Functions: `F1`, `F3`, `F5`
- Dimension: `10`
- Algorithms: `ARPSO-Local`, `ARPSO-SRR`, `ARPSO-EIS`, `ARPSO-Fixed`, `ARPSO-Global`, `PSO-RS`
- Runs: `2`
- Population size: `20`
- MaxFEs: `2000`
- Record interval: `20`
- Base seed: `20260523`
- Jobs: `1`

Expected task count:

- `3 functions x 6 algorithms x 2 runs = 36 runs`

## 2. Commands Executed

Smoke test:

```bash
python -m experiments.smoke_test
```

Config validation:

```bash
python -m experiments.validate_configs
```

Real pilot run:

```bash
python -m experiments.run_ablation6 --config configs/ablation6_pilot.yaml
```

Table generation:

```bash
python -m analysis.generate_tables --experiment ablation6_pilot
```

Figure generation:

```bash
python -m analysis.generate_figures --experiment ablation6_pilot --no-png
```

Tests:

```bash
python -m pytest -q
```

On Windows without an activated virtual environment, the same commands were executed with `.\.venv\Scripts\python -m ...`.

## 3. Pilot Result

Run status:

- Planned runs: `36`
- Successful runs: `36`
- Failed runs: `0`
- Raw CSV rows: `36`
- Summary CSV rows: `18`
- Sum of per-run measured runtime: approximately `2.16 seconds`

The warning from `opfunu` about `pkg_resources` is expected for this dependency family. The repository pins `setuptools<81` for compatibility.

## 4. Generated Files

Raw and summary outputs:

- `results/raw/ablation6_pilot_raw.csv`
- `results/raw/ablation6_pilot_convergence.csv`
- `results/summary/ablation6_pilot_summary.csv`
- `results/curves/ablation6_pilot_curves.jsonl`

Statistical CSV outputs:

- `results/stats/ablation6_pilot_raw_average_rank.csv`
- `results/stats/ablation6_pilot_raw_friedman.csv`
- `results/stats/ablation6_pilot_raw_ARPSO-SRR_win_tie_loss.csv`
- `results/stats/ablation6_pilot_raw_ARPSO-SRR_holm_posthoc.csv`

LaTeX table outputs:

- `results/tables/ablation6_pilot_summary.tex`
- `results/tables/ablation6_pilot_raw_average_rank.tex`
- `results/tables/ablation6_pilot_raw_friedman.tex`
- `results/tables/ablation6_pilot_raw_ARPSO-SRR_win_tie_loss.tex`
- `results/tables/ablation6_pilot_raw_ARPSO-SRR_holm_posthoc.tex`

Vector figure outputs:

- `results/figures/ablation6_pilot_convergence.pdf`
- `results/figures/ablation6_pilot_convergence.svg`
- `results/figures/ablation6_pilot_convergence.tex`
- `results/figures/ablation6_pilot_ranking.pdf`
- `results/figures/ablation6_pilot_ranking.svg`
- `results/figures/ablation6_pilot_ranking.tex`
- `results/figures/ablation6_pilot_runtime.pdf`
- `results/figures/ablation6_pilot_runtime.svg`
- `results/figures/ablation6_pilot_ablation.pdf`
- `results/figures/ablation6_pilot_ablation.svg`
- `results/figures/ablation6_pilot_restart.pdf`
- `results/figures/ablation6_pilot_restart.svg`
- `results/figures/ablation6_pilot_restart.tex`

The same generated LaTeX and vector figure artifacts are copied to:

- `paper/tables/`
- `paper/figures/`

`results/`, `paper/tables/`, and `paper/figures/` are ignored because they are generated outputs.

## 5. Unified CSV Schema

Raw result fields include:

```text
experiment_name, benchmark, function, function_id, dimension, algorithm,
run, run_id, seed, population_size, max_fes, best_fitness, error_value,
function_evaluations, runtime_seconds, restart_count, operator_usage,
operator_success, status, success_flag, error
```

Convergence CSV fields include:

```text
algorithm, function_id, run_id, fe, best_so_far
```

The analysis layer reads these fields directly for tables and figures.

## 6. Ablation6 Mechanism Differences

The six groups are mechanism-level variants exposed through `algorithms.factory.build_optimizer`, not display-name aliases.

| Variant | Restart trigger | Restart intensity | Selected particles | Global restart ratio | Local perturbation | pbest reset policy | Velocity reset policy | Boundary handling |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ARPSO-Local` | `global_stagnation >= stagnation_threshold` or diversity below threshold | Adaptive `rho_min` to `rho_max` from stagnation and diversity loss | Non-elite particles ranked by particle stagnation | `0.0` | All selected particles perturb around `gbest` with decaying sigma | pbest is updated only if the restarted candidate improves it | selected particles receive fresh uniform velocity in `[-vmax, vmax]` | positions clipped to `[lower_bound, upper_bound]` |
| `ARPSO-SRR` | Same ARPSO-SRR trigger | Adaptive `rho_min` to `rho_max` | Non-elite particles ranked by particle stagnation | About `1 - local_ratio` with default `local_ratio=0.5` | First selected subset perturbs around `gbest`; remaining subset is globally sampled | pbest is updated only on improvement | selected particles receive fresh uniform velocity | positions clipped to bounds |
| `ARPSO-EIS` | AP-SRR style stagnation/diversity trigger with `stagnation_threshold=35`, `diversity_threshold=0.04` | Adaptive `rho_min=0.05` to `rho_max=0.25` | Non-elite particles ranked by IPS ineffective score | No uniform global-only branch; factory restricts portfolio to opposition | Opposition candidate blends `gbest` with the opposite of a sampled pbest | pbest is updated only on improvement | selected particle velocity is resampled uniformly | candidates clipped to bounds |
| `ARPSO-Fixed` | Same ARPSO-SRR trigger | Fixed intensity because `rho_min=rho_max=0.20` | Non-elite particles ranked by particle stagnation | Same default split as ARPSO-SRR | Same local/global split as ARPSO-SRR | pbest is updated only on improvement | selected particles receive fresh uniform velocity | positions clipped to bounds |
| `ARPSO-Global` | Same ARPSO-SRR trigger | Adaptive `rho_min` to `rho_max` | Non-elite particles ranked by particle stagnation | `1.0` | Disabled by `local_ratio=0.0`; all selected particles are globally sampled | pbest is updated only on improvement | selected particles receive fresh uniform velocity | positions clipped to bounds |
| `PSO-RS` | `no_improve >= stagnation_threshold` | Fixed `restart_ratio` | Random sample from non-elite pbest-ranked particles | `1.0` | No local perturbation | pbest is updated only on improvement | selected particles receive fresh uniform velocity | positions clipped to bounds |

## 7. Tests Added

New/updated tests verify:

- `configs/ablation6_pilot.yaml` passes config validation.
- `configs/smoke_test.yaml` is accepted by the validator as a small smoke-style config.
- raw schema includes `run_id`, `error_value`, and `success_flag`.
- a synthetic pilot raw/summary/convergence fixture can be consumed by `analysis.generate_tables`.
- a synthetic pilot raw/summary/convergence fixture can be consumed by `analysis.generate_figures`.
- generated LaTeX and PGFPlots/TikZ files are non-empty.

Latest local test result:

```text
18 passed, 1 warning
```

## 8. Why This Is Not a Formal Paper Result

The pilot uses only:

- `3` CEC2017 functions,
- `10D`,
- `2` independent runs,
- `2000` MaxFEs.

This scale is intentionally too small for statistical claims. The generated Friedman/Wilcoxon artifacts are pipeline validation outputs only. They must not be used to claim that one algorithm is superior.

## 9. Recommended Next Formal Path

Before full formal 30-run experiments, run a larger but still controlled pilot:

```bash
python -m experiments.run_cec2017_main --config configs/cec2017_30d_pilot.yaml
python -m analysis.generate_tables --experiment cec2017_30d_pilot
python -m analysis.generate_figures --experiment cec2017_30d_pilot --no-png
```

Only after the 30D pilot produces stable CSV, tables, figures, and runtime estimates should the protected formal command be used:

```bash
python -m experiments.run_cec2017_main --config configs/cec2017_30d.yaml --confirm-formal-run
```

## 10. Commit Safety and Remote Sync

Local pilot pipeline commit:

- `f15bf9d chore: validate pilot ablation pipeline`

Safety backups created before pushing:

- `backup/0001-chore-validate-pilot-ablation-pipeline.patch`
- `backup/ap-srr-pso-f15bf9d.bundle`

Push status:

- `git push origin main` succeeded.
- `origin/main` advanced from `adb1658` to `f15bf9d`.
- No force push, rebase, reset, or GitHub API commit workaround was used.
- GitHub Actions passed on `f15bf9d`.

Follow-up hardening status:

- A local hardening commit adds `scripts/check_pilot_pipeline.py` and clean-clone documentation.
- Normal push attempts for this follow-up commit failed with GitHub HTTPS 443 connection reset / connection timeout.
- No force push or GitHub API commit workaround was used for the follow-up commit.
- A backup patch and bundle were created for the local follow-up commit under `backup/`.

## 11. Git Ignore and Paper Integration Risk

Current ignore policy:

- `results/` is ignored.
- `paper/figures/` is ignored.
- `paper/tables/` is ignored.
- pilot raw/summary/stat/table/figure outputs are generated artifacts and are not committed.

Current paper status:

- There is no tracked `paper/main.tex` in the repository.
- Therefore the current clean clone has no paper build target and no tracked LaTeX file that directly references ignored pilot figures or tables.
- The current paper build limitation is missing paper source, not missing generated figures or tables.

Future paper integration rule:

- Do not commit pilot raw results.
- For final formal paper results, either run `analysis.generate_tables` and `analysis.generate_figures` before compiling the paper, or deliberately commit the final paper-facing files under `paper/tables/` and `paper/figures/`.
- If a future `paper/main.tex` directly references `paper/tables/*.tex` or `paper/figures/*.pdf`, the CI or README must make the generation step explicit before paper compilation.

## 12. Clean Clone Reproducibility

Fresh clone reproduction sequence:

```bash
git clone https://github.com/creamdesk/ap-srr-pso.git
cd ap-srr-pso
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m experiments.smoke_test
.\.venv\Scripts\python -m experiments.validate_configs
.\.venv\Scripts\python -m experiments.run_ablation6 --config configs/ablation6_pilot.yaml
.\.venv\Scripts\python -m analysis.generate_tables --experiment ablation6_pilot
.\.venv\Scripts\python -m analysis.generate_figures --experiment ablation6_pilot --no-png
.\.venv\Scripts\python -m pytest -q
```

Manual one-command pilot artifact regeneration after dependencies are installed:

```bash
.\.venv\Scripts\python scripts\check_pilot_pipeline.py
```

The manual script moves existing `ablation6_pilot` artifacts to `results/tmp/pilot_pipeline_backup/`, regenerates raw/summary/table/figure outputs, and checks that key CSV, LaTeX, PDF, and PGFPlots/TikZ files are non-empty. It is intentionally not part of normal CI because it runs real pilot optimization.

Clean clone check performed:

- Clone directory: `D:\github repository\ap-srr-pso-clean-20260524-102725`
- The clone started with no existing `ablation6_pilot` artifacts.
- A fresh `.venv` was created.
- Dependencies were installed from `requirements.txt`; `setuptools` was downgraded to the pinned `<81` version.
- `scripts/check_pilot_pipeline.py` regenerated the pilot outputs successfully.
- `pytest -q` passed with `18 passed, 1 warning`.

## 13. Remaining Gates Before Formal Experiments

Before formal 30-run CEC2017 experiments:

- GitHub Actions must pass on the latest pushed commit.
- A clean clone must regenerate pilot outputs from an empty result state.
- The paper source must either generate ignored figure/table artifacts before compilation or commit final formal paper-facing artifacts intentionally.
- A larger non-formal pilot should be run before full formal scale, for example 10D with `F1-F10`, `runs=5`, and a controlled MaxFEs budget.
