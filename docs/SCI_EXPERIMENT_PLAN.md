# SCI Experiment Plan

This plan follows `docs/PAPER_STRATEGY.md`. The goal is to build evidence for AP-SRR-PSO as an adaptive portfolio search resource reallocation PSO, not to claim universal superiority.

## Experiment Levels

| Level | Purpose | Runs | MaxFEs | Paper status |
|---|---|---:|---:|---|
| smoke | import/output sanity check | 1 | tiny | engineering only |
| mini validation | CEC adapter and CSV pipeline | 2 | 3000 | engineering only |
| 30D probe | 30D stability and runtime estimate | 2 | 10000 | engineering only |
| 30D pilot | small multi-function pilot | 5 | 30000-50000 | engineering only |
| formal 30D | main paper evidence | 30 | 300000 | formal result |

Do not mix engineering validation outputs with formal paper conclusions.

## Main Comparison

Formal baseline set, implemented or planned:

- PSO
- PSO-RS
- PSO-AW
- ARPSO-SRR
- DE
- AP-SRR-PSO

Before journal submission, add or justify stronger baselines:

- CLPSO
- HPSO-TVAC
- JADE or SHADE
- CMA-ES if implementation cost is acceptable

## Formal CEC2017 30D Setting

- benchmark: CEC2017
- dimension: 30
- functions: F1-F30
- MaxFEs: 10000 * D = 300000
- runs: 30 independent runs
- population_size: 50 unless a baseline requires a documented setting
- output: `results/raw/cec2017_30d_main.csv`

Run this only after smoke, mini validation, 30D probe, and 30D pilot are clean.

## Ablation Study

Algorithms:

- AP-SRR-PSO
- AP-SRR-PSO-NO-IPS
- AP-SRR-PSO-NO-ARP
- AP-SRR-PSO-NO-RCA
- ARPSO-SRR
- PSO-RS

Questions:

- IPS: does ineffective particle scoring select better reallocation targets?
- ARP: does a portfolio improve over fixed restart behavior?
- RCA: does feedback-driven operator preference help?
- ARPSO-SRR comparison: is the SCI upgraded method more stable than the older resource reallocation baseline?

## Parameter Sensitivity

Study limited representative values for:

- stagnation_threshold
- rho_min/rho_max
- elite_ratio
- local_sigma
- softmax_temperature

Use selected representative functions only. Avoid exhaustive full-grid searches.

## Convergence and Behavior

Representative functions:

- unimodal: F1
- multimodal: F3 or F10
- hybrid: F13/F20
- composition: F23/F24/F29 if supported

Required behavior outputs:

- convergence curves;
- restart_count;
- operator_usage;
- operator_success;
- diversity_curve when recorded.

## Statistical Analysis

Formal statistics:

- Wilcoxon signed-rank tests;
- Friedman average ranking;
- Holm post-hoc correction;
- Win/Tie/Loss.

Do not run or report formal statistics from 2-run mini/probe data except as script validation.

## Runtime Analysis

Report mean runtime by algorithm and function. State that AP-SRR-PSO adds IPS sorting and restart bookkeeping overhead, but the total runtime is still dominated by objective evaluations.
