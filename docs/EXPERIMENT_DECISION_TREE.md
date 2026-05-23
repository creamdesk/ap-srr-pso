# Experiment Decision Tree

This document defines when to continue, stop, debug, or scale experiments.

## Step 1: CI and dry-run

Proceed only if all are true:

- GitHub Actions pytest is green;
- smoke test passes;
- main experiment dry-run prints a plan and does not run formal experiments;
- CEC2017 availability check produces a CSV.

If any fail, fix engineering before running optimization experiments.

## Step 2: 30D probe

Run `run_cec2017_30d_probe.py` only after dry-run succeeds.

Continue to pilot if:

- all planned runs complete;
- no NaN or Inf values appear;
- raw CSV, summary CSV, and curves JSONL are generated;
- runtime is acceptable for local or cloud execution;
- AP-SRR-PSO produces valid results on all selected functions.

Stop and debug if:

- any algorithm fails construction;
- any benchmark function fails unexpectedly;
- results contain NaN or Inf;
- curves are empty;
- runtime is clearly abnormal.

## Step 3: pilot

Pilot is still engineering evidence. It is used to decide whether formal experiments are worth the cost.

Continue to formal experiments only if:

- AP-SRR-PSO is at least competitive on some representative functions;
- ablation variants behave plausibly;
- runtime is manageable;
- result generation, statistics, figures, and tables work end-to-end.

If AP-SRR-PSO is consistently worse than PSO-family baselines, do not run formal experiments. Revisit IPS, ARP, RCA, or paper positioning.

## Step 4: stronger baselines

Before a serious SCI submission, decide whether to add CLPSO, HPSO-TVAC, JADE/SHADE, or CMA-ES.

If stronger baselines are not included, limit the claim to PSO-family improvement and avoid broad evolutionary algorithm dominance claims.

## Step 5: formal run

Only run the formal configuration after probe and pilot are stable.

Formal run requirements:

- 30 independent runs;
- full available CEC2017 function set;
- MaxFEs = 10000 * D;
- raw CSV saved;
- summary CSV saved;
- statistical tests saved;
- vector figures generated;
- LaTeX tables generated;
- failed/skipped functions recorded.

## Step 6: paper writing

Write results after formal outputs are available. Do not write conclusions first and then search for evidence.
