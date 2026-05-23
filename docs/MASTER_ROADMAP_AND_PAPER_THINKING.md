# Master Roadmap and Paper Thinking

This document records the full AP-SRR-PSO research route, paper logic, engineering plan, and execution order. It is the highest-level roadmap for the repository.

## 1. One-sentence thesis

AP-SRR-PSO is not a random-restart PSO. It is an adaptive search-resource reallocation framework that identifies less productive particles, reallocates them through a restart operator portfolio, and updates operator preferences using restart credit assignment.

## 2. Core narrative

The paper should follow this fixed narrative:

```text
PSO premature convergence
-> less productive particles
-> wasted function evaluation budget
-> ineffective particle identification
-> adaptive search resource reallocation
-> restart operator portfolio
-> feedback-driven credit assignment
-> more robust PSO-style optimization behavior
```

The paper should not be framed as merely adding random restart to PSO.

## 3. Research problem

Standard PSO may converge prematurely on complex landscapes. Once the swarm becomes concentrated, some particles continue consuming function evaluations while contributing little improvement. Under fixed-budget benchmarks such as CEC2017, this is not only a diversity problem but also a search resource allocation problem.

AP-SRR-PSO treats particles as search resources. Particles that show weak contribution, stagnation, poor pbest quality, or redundant search behavior are selected for reallocation.

## 4. Method modules

### IPS: Ineffective Particle Scoring

IPS scores particles according to signals such as:

- pbest quality;
- current fitness quality;
- stagnation length;
- crowding or distance-related information;
- elite protection constraints.

Particles with high ineffective scores are treated as less productive search resources and are prioritized for reallocation.

### ARP: Adaptive Restart Portfolio

ARP avoids relying on one restart behavior. Candidate restart operators may include:

- local perturbation for exploitation around promising regions;
- differential reallocation for direction-aware movement;
- global restart for exploration recovery;
- opposition-based restart for escape from local regions.

The point is not to restart randomly, but to choose among restart behaviors that represent different exploration-exploitation trade-offs.

### RCA: Restart Credit Assignment

RCA updates the preference for restart operators according to recent improvement contribution. If an operator produces better pbest, better gbest, or useful improvement after reallocation, its credit increases. Operators with higher recent credit are more likely to be selected later.

RCA should be described as feedback-driven adaptive operator selection, not reinforcement learning.

## 5. Main contributions

1. A low-efficiency particle identification mechanism that explicitly models which particles are less productive under a finite function-evaluation budget.
2. An adaptive restart portfolio that reallocates selected particles using multiple complementary restart operators.
3. A restart credit assignment mechanism that updates operator preferences based on recent contribution.
4. A reproducible experiment pipeline covering CEC benchmark loading, raw result storage, summary generation, statistical tests, vector figures, LaTeX tables, dry-run protection, and documentation.

The first three are the algorithmic contributions. The fourth is an engineering/reproducibility contribution and should not overshadow the method.

## 6. Recommended title

Preferred title:

```text
AP-SRR-PSO: Adaptive Portfolio Search Resource Reallocation Particle Swarm Optimization for Numerical Optimization
```

Alternative title:

```text
An Adaptive Portfolio Search Resource Reallocation Particle Swarm Optimization Algorithm for Numerical Optimization
```

Avoid words such as superior, optimal, state-of-the-art, best, or universally dominant.

## 7. Method section outline

### 3.1 Motivation and overall framework

Explain that PSO early convergence creates not only loss of diversity, but also inefficient usage of finite function evaluations. Introduce AP-SRR-PSO as a framework that reallocates low-efficiency particles.

### 3.2 Ineffective Particle Scoring

Define particle-level ineffective score. Explain pbest badness, current-fitness badness, stagnation badness, and crowding/distance information. Emphasize elite protection.

### 3.3 Adaptive restart intensity

Define a restart ratio in a bounded interval. Restart intensity should increase under stagnation and diversity loss, and remain conservative when the swarm is still improving.

### 3.4 Adaptive Restart Portfolio

Describe local, differential, global, and opposition-based restart operators. Explain the exploration-exploitation role of each operator.

### 3.5 Restart Credit Assignment

Define operator credit and selection probability. Explain how success and improvement update future operator preferences.

### 3.6 Complexity analysis

Be honest: AP-SRR-PSO adds scoring, ranking, restart bookkeeping, and credit update overhead. However, objective evaluations still dominate most benchmark runtime.

### 3.7 Pseudocode

The pseudocode must match the implementation. It should include initialization, PSO update, pbest/gbest update, stagnation and diversity check, IPS selection, restart-operator sampling, candidate evaluation, credit update, and convergence recording.

## 8. Experiment hierarchy

The repository must clearly distinguish engineering checks from formal evidence.

| Level | Purpose | Runs | Budget | Paper status |
|---|---|---:|---:|---|
| smoke | import and output sanity check | tiny | tiny | engineering only |
| mini validation | CEC adapter and CSV pipeline | 2 | 3000 | engineering only |
| 30D probe | 30D stability and runtime estimate | 2 | 10000 | engineering only |
| pilot | small multi-function pilot | 5 | 30000-50000 | engineering only |
| formal main | paper evidence | 30 | 300000 for 30D | formal result |

Do not use smoke, mini validation, probe, or pilot results as formal paper claims.

## 9. Formal experiment setting

Formal CEC2017 main experiment:

- benchmark: CEC2017;
- dimension: 30D;
- functions: F1-F30, unless the environment explicitly cannot load a function;
- max function evaluations: 10000 * D = 300000;
- independent runs: 30;
- population size: usually 50 unless justified;
- metrics: mean, standard deviation, median, best, worst, runtime;
- statistical tests: Wilcoxon, Friedman average rank, Holm post-hoc, Win/Tie/Loss.

Failures and skipped functions must be recorded. Do not cherry-pick functions.

## 10. Baseline policy

Current engineering baselines:

- PSO;
- PSO-RS;
- PSO-AW;
- ARPSO-SRR;
- DE;
- AP-SRR-PSO.

For a stronger SCI submission, add or justify stronger baselines:

- CLPSO;
- HPSO-TVAC;
- JADE or SHADE;
- CMA-ES if dependency and runtime are manageable.

The safest claim is that AP-SRR-PSO improves PSO-family robustness and can be competitive on selected complex functions. Do not claim that it universally defeats all evolutionary algorithms.

## 11. Ablation study

Required variants:

- AP-SRR-PSO;
- AP-SRR-PSO-NO-IPS;
- AP-SRR-PSO-NO-ARP;
- AP-SRR-PSO-NO-RCA;
- ARPSO-SRR;
- PSO-RS.

The ablation should answer:

- Does IPS choose better reallocation targets?
- Does ARP improve over a fixed restart behavior?
- Does RCA improve over fixed or uniform operator selection?
- Does AP-SRR-PSO improve over the older ARPSO-SRR framing?

## 12. Parameter sensitivity

Analyze representative values only. Do not perform a giant hidden tuning sweep.

Recommended parameters:

- stagnation threshold;
- rho_min and rho_max;
- elite ratio;
- local sigma;
- softmax temperature.

Representative functions should cover unimodal, multimodal, hybrid, and composition behavior when available.

## 13. Figures

Formal figures must be vector graphics. PDF is the primary LaTeX figure format. SVG is the editable vector backup. PNG is preview only.

Required figures:

1. AP-SRR-PSO overall framework.
2. Ineffective particle scoring illustration.
3. Convergence curves.
4. Average ranking.
5. Ablation comparison.
6. Restart behavior and operator contribution.
7. Runtime comparison.

Style rules:

- no Chinese labels in formal plots;
- clean IEEE-friendly layout;
- no decorative backgrounds;
- consistent font size, line width, and marker size;
- do not hard-code winners manually.

## 14. Tables

Required tables:

1. Parameter settings.
2. Main CEC2017 comparison, mean plus standard deviation.
3. Wilcoxon Win/Tie/Loss.
4. Friedman ranking.
5. Ablation results.
6. Runtime comparison.

Tables must be generated from CSV outputs. Do not manually edit table values to make the method look better.

## 15. Writing policy

Allowed wording:

- competitive performance;
- improved robustness on selected complex functions;
- stable improvement over PSO-family baselines;
- effective search resource reallocation;
- interpretable restart behavior;
- acceptable additional computational cost.

Forbidden wording:

- state-of-the-art;
- universally best;
- always outperforms;
- no overhead;
- all functions improved;
- statistically significant from 2 runs;
- cherry-picked superiority.

## 16. Engineering pipeline

Canonical files:

- `experiments/config_loader.py`: config and CLI override loading;
- `experiments/result_writer.py`: canonical result schema and output directories;
- `experiments/experiment_runner.py`: canonical experiment runner;
- `experiments/run_experiment.py`: backward-compatible wrapper;
- `experiments/run_cec2017_main.py`: protected formal entry;
- `experiments/run_cec2017_30d_probe.py`: 30D probe;
- `experiments/run_cec2017_pilot.py`: pilot;
- `experiments/run_ablation.py`: ablation;
- `experiments/run_sensitivity.py`: sensitivity;
- `experiments/run_runtime.py`: runtime;
- `experiments/check_cec2017_availability.py`: CEC2017 F1-F30 check;
- `analysis/summarize_results.py`: canonical summary regeneration;
- `analysis/statistical_tests.py`: statistical tests;
- `analysis/plot_*.py`: vector figure scripts;
- `analysis/generate_all_figures.py`: figure orchestration;
- `analysis/generate_latex_tables.py` and `analysis/generate_paper_tables.py`: LaTeX table generation.

## 17. Immediate execution order

1. Pull latest GitHub code.
2. Run smoke test.
3. Run dry-runs for mini, probe, and protected main.
4. Run CEC2017 availability check.
5. Run pytest.
6. Fix any CI or local failures.
7. Run 30D probe.
8. Generate summary, stats, vector figures, and LaTeX tables.
9. Run pilot.
10. Decide whether AP-SRR-PSO has enough promise to justify full formal experiments.
11. Add stronger baselines.
12. Run formal 30-run experiment.
13. Write the paper.

## 18. Critical rule

A file being present in GitHub does not mean the project is correct. The project is integrated only after local or CI validation passes:

```powershell
.\.venv\Scripts\python experiments\smoke_test.py
.\.venv\Scripts\python experiments\run_cec2017_mini_validation.py --dry-run
.\.venv\Scripts\python experiments\run_cec2017_30d_probe.py --dry-run
.\.venv\Scripts\python experiments\run_cec2017_main.py --dry-run
.\.venv\Scripts\python experiments\check_cec2017_availability.py
.\.venv\Scripts\python -m pytest tests -q
```

If GitHub Actions fails, inspect the exact error first. Do not start formal experiments until the pipeline passes.
