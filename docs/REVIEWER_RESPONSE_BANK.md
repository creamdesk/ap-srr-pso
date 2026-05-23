# Reviewer Response Bank

This document records likely reviewer questions and recommended response directions. It is not a final rebuttal; it is a preparation bank for manuscript improvement.

## Q1. Is this just another restart PSO?

Response direction:

AP-SRR-PSO is not framed as a simple restart rule. It addresses four coupled decisions:

1. which particles are less productive;
2. how many particles should be reallocated;
3. which restart operator should be used;
4. how operator preference should be updated according to recent contribution.

The method combines IPS, ARP, and RCA, so the restart process is selective, portfolio-based, and feedback-driven.

## Q2. Why are stronger baselines missing?

Response direction:

A journal-level version should add or justify stronger baselines such as CLPSO, HPSO-TVAC, JADE/SHADE, and CMA-ES. If these are not included, the claim must be narrowed to PSO-family improvement and competitive behavior against selected evolutionary baselines.

## Q3. Does AP-SRR-PSO increase runtime?

Response direction:

Yes. IPS scoring, restart bookkeeping, and credit update introduce additional overhead. The paper should not claim zero overhead. Runtime analysis should quantify the practical cost and discuss whether the robustness improvement is worth it.

## Q4. Are the results statistically significant?

Response direction:

Only formal 30-run experiments can support statistical claims. Smoke tests, mini validation, 30D probe, and pilot experiments are engineering checks and must not be used as statistical evidence.

## Q5. Did the authors cherry-pick functions?

Response direction:

Formal experiments should report all available CEC2017 functions. Any unavailable function caused by benchmark package limitations must be explicitly recorded using the availability checker.

## Q6. Are the parameters over-tuned?

Response direction:

Use parameter sensitivity analysis on representative functions. The goal is to show that the method is not extremely sensitive to narrow parameter choices, not to hide a large tuning sweep.

## Q7. What is the main novelty?

Response direction:

The novelty is the resource-reallocation view: less productive particles are identified and reallocated using an adaptive restart portfolio with credit feedback. This is more structured than fixed restart or random mutation.

## Q8. Why not claim state-of-the-art?

Response direction:

The safe claim is that AP-SRR-PSO improves robustness over PSO-family baselines and can be competitive on selected complex functions. Universal dominance is unrealistic and should not be claimed.
