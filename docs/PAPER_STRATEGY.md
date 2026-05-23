# AP-SRR-PSO Paper Strategy

This document fixes the paper direction for the AP-SRR-PSO project. Code, experiments, analysis, figures, and tables should serve this main line instead of drifting into unrelated PSO variants or over-claiming.

## 1. Title

Preferred title:

**AP-SRR-PSO: Adaptive Portfolio Search Resource Reallocation Particle Swarm Optimization for Numerical Optimization**

Alternative title:

**An Adaptive Portfolio Search Resource Reallocation Particle Swarm Optimization Algorithm for Numerical Optimization**

Avoid exaggerated wording such as superior, optimal, or state-of-the-art.

## 2. Positioning

AP-SRR-PSO is intended as a reproducible numerical optimization research project with SCI Q4/Q3 potential. It is not a course demo and not a simple restart PSO implementation.

The paper should argue that traditional PSO can waste finite function evaluations when particles remain in less productive regions after premature convergence. AP-SRR-PSO addresses this by identifying ineffective particles and reallocating those search resources through an adaptive restart operator portfolio with feedback-driven credit assignment.

Fixed narrative:

```text
PSO premature convergence
-> ineffective particle identification
-> search resource waste
-> adaptive search resource reallocation
-> restart operator portfolio
-> credit assignment
-> more robust optimization behavior
```

## 3. Core Method

AP-SRR-PSO contains three modules:

- IPS: Ineffective Particle Scoring
- ARP: Adaptive Restart Portfolio
- RCA: Restart Credit Assignment

IPS scores particles by historical stagnation, personal-best quality, current fitness, and crowding/distance information. ARP reallocates selected particles using a portfolio of local, differential, global, and opposition-based restart operators. RCA updates operator preference based on recent restart contribution.

## 4. Contributions

1. IPS identifies less productive search resources by combining pbest-fitness badness, particle stagnation, crowding or distance to gbest, and current-fitness badness.
2. ARP uses a restart operator portfolio instead of a single fixed restart strategy.
3. RCA records restart success and improvement, then updates operator selection preference using feedback-driven credit assignment.
4. The repository provides a reproducible engineering pipeline with CEC adapters, batch experiments, summary, statistical tests, ablation hooks, vector figures, and LaTeX-ready outputs.

## 5. Method Section Structure

3.1 Motivation and Overall Framework

Explain premature convergence, inefficient function evaluation usage, and why search resource reallocation is needed.

3.2 Ineffective Particle Scoring

Define IPS and explain rank_badness, stagnation_badness, crowding_badness, and current_badness.

3.3 Adaptive Restart Intensity

Define restart ratio rho_t from global stagnation and diversity loss. Explain rho_min and rho_max.

3.4 Adaptive Restart Portfolio

Define local perturbation, differential reallocation, global restart, and opposition-based restart.

3.5 Restart Credit Assignment

Define operator credit, success, improvement, and softmax-based selection probability. RCA is feedback-driven adaptive operator selection, not reinforcement learning.

3.6 Computational Complexity

State that AP-SRR-PSO adds IPS scoring, ranking, and restart bookkeeping. The overall runtime is still dominated by function evaluations, but the method does have additional overhead.

3.7 Pseudocode

Algorithm 1 must match the implemented code: initialization, PSO update, stagnation/diversity check, IPS selection, restart operator sampling, candidate evaluation, credit update, and result recording.

## 6. Experiment Section Structure

Formal setting: CEC2017, 30D main experiments, MaxFEs = 10000 * D = 300000, 30 independent runs, fixed population size, fixed seed rule, and recorded runtime.

Implemented baselines: PSO, PSO-RS, PSO-AW, ARPSO-SRR, DE, AP-SRR-PSO.

Stronger baselines to add or justify: CLPSO, HPSO-TVAC, JADE/SHADE, and CMA-ES.

Ablation variants: AP-SRR-PSO, AP-SRR-PSO-NO-IPS, AP-SRR-PSO-NO-ARP, AP-SRR-PSO-NO-RCA, ARPSO-SRR, and PSO-RS.

## 7. Formal Results

Formal paper results require:

- CEC2017 formal configuration;
- 30D main setting;
- MaxFEs = 10000 * D;
- 30 independent runs;
- complete result CSV;
- statistical tests;
- reproducible seed policy;
- no cherry-picking of functions.

Engineering-only outputs include smoke test, mini validation, 30D probe, pilot, dry-run output, and import/schema checks.

## 8. Forbidden Claims

Do not claim state-of-the-art, universally best, always outperforms, no computational overhead, all functions improved, or statistical significance from 2 runs.

Allowed conservative wording: competitive performance, improved robustness on selected complex functions, stable improvement over PSO-family baselines, effective search resource reallocation, interpretable restart behavior, and acceptable additional computational cost.

## 9. Code-to-Paper Mapping

- `algorithms/ap_srr_pso.py` and `algorithms/ap_srr_pso_v2.py`: AP-SRR-PSO modules and variants.
- `algorithms/factory.py`: canonical algorithm names for main, ablation, sensitivity, and probe experiments.
- `benchmarks/problem_factory.py` and `benchmarks/cec_adapter.py`: benchmark loading for CEC experiments.
- `experiments/config_loader.py`: YAML config loading and command-line overrides.
- `experiments/result_writer.py`: canonical raw CSV, summary CSV, curves JSONL, and result directories.
- `experiments/experiment_runner.py`: canonical reusable experiment runner.
- `experiments/run_experiment.py`: backward-compatible wrapper that delegates to the canonical runner.
- `experiments/run_cec2017_main.py`: protected formal 30D entry point.
- `experiments/run_cec2017_30d_probe.py`: engineering 30D stability/runtime probe.
- `experiments/run_cec2017_pilot.py`: pilot entry point.
- `experiments/run_ablation.py`: ablation entry point.
- `experiments/run_sensitivity.py`: sensitivity entry point.
- `experiments/run_runtime.py`: runtime entry point.
- `experiments/check_cec2017_availability.py`: F1-F30 availability check.
- `analysis/summarize_results.py`: canonical summary regeneration.
- `analysis/statistical_tests.py`: average rank, Friedman, Holm, and Win/Tie/Loss tests.
- `analysis/plot_convergence.py`, `analysis/plot_rankings.py`, `analysis/plot_ablation.py`, `analysis/plot_runtime.py`, `analysis/plot_restart_behavior.py`: vector figure scripts.
- `analysis/generate_all_figures.py`: figure orchestration.
- `analysis/generate_latex_tables.py` and `analysis/generate_paper_tables.py`: LaTeX table generation.
- `docs/*.md`: reproducibility, strategy, run guides, baseline roadmap, and figure/table plan.

## 10. Validation Rule

A file being present in GitHub is not enough. The project is considered integrated only after the local or CI validation sequence passes:

```powershell
.\.venv\Scripts\python experiments\smoke_test.py
.\.venv\Scripts\python experiments\run_cec2017_mini_validation.py --dry-run
.\.venv\Scripts\python experiments\run_cec2017_30d_probe.py --dry-run
.\.venv\Scripts\python experiments\run_cec2017_main.py --dry-run
.\.venv\Scripts\python experiments\check_cec2017_availability.py
.\.venv\Scripts\python -m pytest tests -q
```
