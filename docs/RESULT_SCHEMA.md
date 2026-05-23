# Result Schema

This document defines stable outputs for AP-SRR-PSO experiments.

## Raw CSV

Required fields:

- `experiment_name`
- `benchmark`
- `function`
- `function_id`
- `dimension`
- `algorithm`
- `run`
- `seed`
- `population_size`
- `max_fes`
- `best_fitness`
- `function_evaluations`
- `runtime_seconds`
- `restart_count`
- `operator_usage`
- `operator_success`
- `status`
- `error`

`operator_usage` and `operator_success` are JSON strings. Algorithms without restart metadata should leave these as `{}` or empty values.

## Summary CSV

Required fields:

- `experiment_name`
- `benchmark`
- `function`
- `function_id`
- `dimension`
- `algorithm`
- `runs`
- `mean_best`
- `std_best`
- `median_best`
- `best`
- `worst`
- `mean_runtime_seconds`
- `total_runtime_seconds`
- `success_count`
- `failure_count`

## Curves JSONL

Each line stores one run:

- `experiment_name`
- `benchmark`
- `function`
- `function_id`
- `dimension`
- `algorithm`
- `run`
- `seed`
- `convergence_curve`
- `function_evaluations`

Long convergence curves must be stored in JSONL, not embedded into raw CSV.

## Statistics CSV

Expected files under `results/stats/`:

- average rank
- Friedman test
- Wilcoxon pairwise tests
- Holm post-hoc results
- Win/Tie/Loss summaries

Statistics from fewer than 5 runs are engineering checks only. Formal significance requires 30 independent runs.

## Figures

Formal figures must be vector graphics:

- `results/figures/*.pdf`
- `results/figures/*.svg`
- synchronized copies in `paper/figures/`

PNG files are previews only.
