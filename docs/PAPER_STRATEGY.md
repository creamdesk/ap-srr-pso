# AP-SRR-PSO Paper Strategy

This document fixes the paper direction for the AP-SRR-PSO project. Code, experiments, analysis, figures, and tables should serve this main line instead of drifting into unrelated PSO variants or over-claiming.

## 1. Title

Preferred title:

**AP-SRR-PSO: Adaptive Portfolio Search Resource Reallocation Particle Swarm Optimization for Numerical Optimization**

Alternative title:

**An Adaptive Portfolio Search Resource Reallocation Particle Swarm Optimization Algorithm for Numerical Optimization**

Avoid exaggerated wording such as "superior", "optimal", or "state-of-the-art".

## 2. Positioning

AP-SRR-PSO is intended as a reproducible numerical optimization research project with SCI Q4/Q3 potential. It is not a course demo and not a simple "restart PSO" implementation.

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

## 3. Core Problem

The core problem is not merely stagnation. The paper focuses on inefficient use of function evaluations caused by particles that contribute little after the swarm has converged or become trapped.

Existing restart-based PSO variants often use fixed or heuristic restart rules. They usually do not explicitly model:

- which particles are less productive;
- which restart operators are more useful under the current search state;
- how recent restart contribution should affect future operator selection.

## 4. Core Method

AP-SRR-PSO contains three modules:

- **IPS: Ineffective Particle Scoring**
- **ARP: Adaptive Restart Portfolio**
- **RCA: Restart Credit Assignment**

IPS scores particles by historical stagnation, personal-best quality, current fitness, and crowding/distance information. ARP reallocates selected particles using a portfolio of local, differential, global, and opposition-based restart operators. RCA updates operator preference based on recent restart contribution.

## 5. Contributions

Contribution 1: IPS identifies less productive search resources by combining pbest-fitness badness, particle stagnation, crowding or distance to gbest, and current-fitness badness.

Contribution 2: ARP uses a restart operator portfolio instead of a single fixed restart strategy. Local, differential, global, and opposition-based operators provide different exploration-exploitation trade-offs.

Contribution 3: RCA records restart success and improvement, then updates operator selection preference using feedback-driven credit assignment.

Optional engineering contribution: the repository provides a reproducible AP-SRR-PSO experimental pipeline, including CEC adapters, batch experiments, summary, statistical tests, ablation hooks, vector figures, and LaTeX-ready outputs. This should support the paper but not replace the algorithmic contribution.

## 6. Method Section Structure

3.1 Motivation and Overall Framework

Explain premature convergence, inefficient function evaluation usage, and why search resource reallocation is needed. The framework figure should show PSO iteration, state detection, IPS, restart intensity, adaptive portfolio, RCA feedback, and population update.

3.2 Ineffective Particle Scoring

Define IPS and explain rank_badness, stagnation_badness, crowding_badness, and current_badness. Particles with higher ineffective scores are regarded as less productive search resources and are prioritized for reallocation.

3.3 Adaptive Restart Intensity

Define restart ratio rho_t from global stagnation and diversity loss. Explain rho_min and rho_max. Do not overcomplicate the formula.

3.4 Adaptive Restart Portfolio

Define local perturbation, differential reallocation, global restart, and opposition-based restart. Explain their exploration-exploitation roles.

3.5 Restart Credit Assignment

Define operator credit, success, improvement, and softmax-based selection probability. RCA is feedback-driven adaptive operator selection, not reinforcement learning.

3.6 Computational Complexity

State that AP-SRR-PSO adds IPS scoring, ranking, and restart bookkeeping. The overall runtime is still dominated by function evaluations, but the method does have additional overhead.

3.7 Pseudocode

Algorithm 1 must match the implemented code: initialization, PSO update, stagnation/diversity check, IPS selection, restart operator sampling, candidate evaluation, credit update, and result recording.

## 7. Experiment Section Structure

4.1 Experimental Setup

Formal setting: CEC2017, 30D main experiments, MaxFEs = 10000 * D = 300000, 30 independent runs, fixed population size, fixed seed rule, and recorded runtime. Metrics include mean, std, best, worst, median, and runtime.

4.2 Main Comparison

Initial implemented baselines: PSO, PSO-RS, PSO-AW, ARPSO-SRR, DE, AP-SRR-PSO. Stronger baselines such as CLPSO, HPSO-TVAC, JADE/SHADE, and CMA-ES should be added or clearly marked as future work before journal submission.

4.3 Ablation Study

Fixed variants: AP-SRR-PSO, AP-SRR-PSO-NO-IPS, AP-SRR-PSO-NO-ARP, AP-SRR-PSO-NO-RCA, ARPSO-SRR, and PSO-RS.

4.4 Parameter Sensitivity

Study a small representative subset of stagnation_threshold, rho_min/rho_max, elite_ratio, local_sigma, and softmax_temperature. Avoid exhaustive parameter grid explosions.

4.5 Convergence Behavior

Use representative functions: F1, F3 or F10, F13/F20, and selected composition functions if supported. Curves must be exported as PDF/SVG.

4.6 Restart Behavior and Operator Contribution

Report restart_count, operator_usage, operator_success, operator probability evolution if available, and diversity curves where available.

4.7 Runtime Analysis

Compare average runtime and acknowledge the additional scoring/restart overhead.

4.8 Statistical Analysis

Use Wilcoxon signed-rank, Friedman average ranking, Holm post-hoc, and Win/Tie/Loss. Do not draw statistical conclusions from mini/probe results.

## 8. Ablation Design

The ablation must answer:

- Does IPS improve particle selection?
- Does the operator portfolio outperform single restart behavior?
- Does RCA improve operator preference over fixed probabilities?
- Is AP-SRR-PSO more stable than ARPSO-SRR under comparable budgets?

## 9. Parameter Sensitivity Design

Use representative CEC2017 functions and limited values for:

- stagnation_threshold;
- rho_min and rho_max;
- elite_ratio;
- local_sigma;
- softmax_temperature.

Sensitivity experiments are diagnostic, not a hidden tuning sweep for selecting only good results.

## 10. Statistical Test Design

Formal statistical outputs:

- Wilcoxon signed-rank pairwise tests against AP-SRR-PSO;
- Friedman average rank across functions;
- Holm post-hoc adjusted p-values;
- Win/Tie/Loss tables.

Runs below 5 are engineering checks only. Formal tests should use 30 independent runs.

## 11. Figure List

- Fig. 1: Overall AP-SRR-PSO framework.
- Fig. 2: Ineffective particle scoring illustration.
- Fig. 3: Convergence curves.
- Fig. 4: Friedman average ranking.
- Fig. 5: Ablation study.
- Fig. 6: Restart behavior and operator contribution.
- Fig. 7: Runtime comparison.

All formal figures must output PDF and SVG. PNG is preview only.

## 12. Table List

- Table I: Parameter settings.
- Table II: Main comparison on CEC2017, mean +/- std.
- Table III: Wilcoxon Win/Tie/Loss.
- Table IV: Friedman ranking.
- Table V: Ablation results.
- Table VI: Runtime comparison.

Tables must be generated from result CSVs. Do not hard-code winners manually.

## 13. Formal Results

Formal paper results require:

- CEC2017 formal configuration;
- 30D main setting;
- MaxFEs = 10000 * D;
- 30 independent runs;
- complete result CSV;
- statistical tests;
- reproducible seed policy;
- no cherry-picking of functions.

## 14. Engineering Validation Only

These are not formal paper results:

- smoke test;
- mini validation;
- 30D probe;
- pilot with 2 or 5 runs;
- dry-run output;
- any test used only for checking import paths, output schema, or runtime.

These can be reported in project notes, not in the paper conclusion.

## 15. Forbidden Claims

Do not claim:

- state-of-the-art;
- universally best;
- always outperforms;
- no computational overhead;
- all functions improved;
- statistical significance from 2 runs;
- superiority based on mini/probe/pilot data.

Allowed conservative wording:

- competitive performance;
- improved robustness on selected complex functions;
- stable improvement over PSO-family baselines;
- effective search resource reallocation;
- interpretable restart behavior;
- acceptable additional computational cost.

## 16. Code-to-Paper Mapping

- `algorithms/ap_srr_pso.py` and `algorithms/ap_srr_pso_v2.py`: AP-SRR-PSO modules and variants.
- `algorithms/factory.py`: canonical algorithm names for main, ablation, and probe experiments.
- `benchmarks/problem_factory.py` and `benchmarks/cec_adapter.py`: benchmark loading for CEC experiments.
- `experiments/smoke_test.py`: engineering smoke test only.
- `experiments/run_cec2017_mini_validation.py`: engineering mini validation only.
- `experiments/run_cec2017_30d_probe.py`: engineering 30D stability/runtime probe only.
- `experiments/run_experiment.py`: main reusable experiment runner for pilot/formal/ablation/sensitivity setups.
- `analysis/summarize_results.py`: summary table generation.
- `analysis/statistical_tests.py`: Wilcoxon, Friedman, Holm, and Win/Tie/Loss outputs.
- `analysis/plot_results.py`: vector figure generation and paper figure synchronization.
- `configs/cec2017_30d.yaml`: formal 30D main experiment template.
- `configs/cec2017_30d_pilot.yaml`: non-formal pilot template.
