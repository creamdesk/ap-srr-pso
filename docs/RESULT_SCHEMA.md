# Result Schema

This document defines stable CSV schemas for AP-SRR-PSO experiments.

## Raw Result Fields

Required fields:

| Field | Meaning |
|---|---|
| benchmark | Benchmark family, e.g. CEC2017 |
| function_id | Numeric function id when available |
| function | Function label, e.g. F1 |
| dimension | Problem dimension |
| algorithm | Canonical algorithm name |
| run | Independent run index |
| seed | Random seed |
| population_size | Population size if recorded |
| max_fes | Function-evaluation budget if recorded |
| best_fitness | Best objective value found |
| function_evaluations | Actual function evaluations |
| runtime_seconds | Wall-clock runtime |
| restart_count | Number of reallocated/restarted particles or events |
| operator_usage | JSON dict for AP-SRR-PSO restart operators |
| operator_success | JSON dict for operator success |
| metadata | JSON dict for extra non-tabular fields |
| status | ok or failed |
| error | Error text for failed runs |

Engineering validation scripts may omit some formal fields, but formal experiment outputs should keep them stable.

## Summary Fields

Required summary fields:

| Field | Meaning |
|---|---|
| benchmark | Benchmark family |
| function_id/function | Function id or label |
| dimension | Problem dimension |
| algorithm | Canonical algorithm name |
| runs | Number of successful runs used in summary |
| mean_best | Mean best_fitness |
| std_best | Standard deviation |
| median | Median best_fitness when generated |
| best | Minimum best_fitness |
| worst | Maximum best_fitness |
| mean_runtime_seconds | Mean runtime |
| total_runtime_seconds | Total runtime when generated |
| success_count | Successful runs |
| failure_count | Failed runs |
| rank | Average rank within the function/dimension group |

## Statistics Outputs

Expected files under `results/stats/`:

- `*_average_rank.csv`
- `*_friedman.csv`
- `*_AP-SRR-PSO_win_tie_loss.csv`
- `*_AP-SRR-PSO_holm_posthoc.csv`

Statistics from fewer than 5 runs must be treated as script validation only. Formal significance requires 30 independent runs.

## Figure Outputs

Formal figures:

- `results/figures/*.pdf`
- `results/figures/*.svg`
- synchronized copies in `paper/figures/`

Optional preview:

- `results/figures/*.png`

Do not use Chinese titles or decorative backgrounds in formal figures.
