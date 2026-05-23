# Paper Draft Skeleton

This document gives a direct writing skeleton for the AP-SRR-PSO paper. It should guide the first full manuscript draft.

## Title

AP-SRR-PSO: Adaptive Portfolio Search Resource Reallocation Particle Swarm Optimization for Numerical Optimization

## Abstract structure

1. Background: PSO is simple and efficient, but premature convergence limits performance on complex landscapes.
2. Problem: stagnated or redundant particles continue consuming finite function evaluations with limited contribution.
3. Gap: existing restart PSO variants often use fixed or heuristic restart rules and do not jointly answer which particles to reallocate, how to reallocate them, and which operator is recently useful.
4. Method: AP-SRR-PSO integrates Ineffective Particle Scoring, Adaptive Restart Portfolio, and Restart Credit Assignment.
5. Experiment: evaluate on CEC2017 with main comparison, ablation, statistics, convergence, restart behavior, and runtime.
6. Claim: AP-SRR-PSO aims for competitive and robust PSO-family improvement, not universal dominance over all evolutionary algorithms.

## 1 Introduction

### Paragraph 1: PSO background

Particle swarm optimization is widely used because of its simple structure, few control parameters, and efficient population-based search behavior.

### Paragraph 2: limitation

On complex multimodal, hybrid, and composition functions, the swarm may lose diversity and converge prematurely.

### Paragraph 3: reinterpretation

This paper interprets premature convergence as a search-resource allocation problem. Less productive particles may keep consuming function evaluations without generating useful improvements.

### Paragraph 4: gap in restart methods

Restart methods can restore diversity, but fixed or random restart does not explicitly model which particles should be restarted or which restart behavior is beneficial in the current search state.

### Paragraph 5: our method and contributions

AP-SRR-PSO is proposed to identify less productive particles, reallocate them through an adaptive restart portfolio, and update operator preferences using restart credit assignment.

## 2 Related Work

### 2.1 PSO and adaptive PSO variants

Discuss inertia weight, acceleration coefficients, adaptive PSO, CLPSO, HPSO-TVAC, and PSO diversity maintenance.

### 2.2 Restart and diversity maintenance

Discuss random restart, mutation-based PSO, adaptive restart, opposition learning, and diversity preservation.

### 2.3 Operator adaptation and resource allocation

Discuss adaptive operator selection, contribution feedback, and resource allocation in evolutionary computation.

## 3 Proposed Method

### 3.1 Motivation and framework

Main idea: particles are search resources. Less productive particles are selected and reallocated instead of allowing them to repeatedly spend function evaluations in low-value regions.

### 3.2 IPS

Define ineffective score. Explain pbest quality, current fitness, stagnation, crowding or distance, and elite protection.

### 3.3 Adaptive restart intensity

Define bounded restart ratio. Restart intensity increases under stagnation and diversity loss and remains conservative when search progress is still observed.

### 3.4 ARP

Define local perturbation, differential reallocation, global restart, and opposition-based restart.

### 3.5 RCA

Define credit update and probability update. Describe it as feedback-driven adaptive operator selection.

### 3.6 Complexity

State honestly that scoring and bookkeeping introduce overhead. Runtime analysis must measure the practical cost.

### 3.7 Pseudocode

Algorithm 1 should match the implementation exactly.

## 4 Experiments

### 4.1 Setup

CEC2017, 30D, MaxFEs = 300000, 30 independent runs, population size 50, fixed seed rule, mean/std/median/best/worst/runtime.

### 4.2 Main comparison

Compare against PSO, PSO-RS, PSO-AW, ARPSO-SRR, DE, and stronger baselines when implemented.

### 4.3 Ablation

Compare full AP-SRR-PSO against NO-IPS, NO-ARP, NO-RCA, ARPSO-SRR, and PSO-RS.

### 4.4 Sensitivity

Analyze stagnation threshold, rho_min/rho_max, elite ratio, local sigma, and softmax temperature.

### 4.5 Convergence

Use representative unimodal, multimodal, hybrid, and composition functions.

### 4.6 Restart behavior

Analyze restart count, operator usage, operator success, and credit behavior.

### 4.7 Runtime

Compare practical runtime and discuss overhead.

### 4.8 Statistics

Report Wilcoxon, Friedman ranking, Holm correction, and Win/Tie/Loss. Do not use 2-run or pilot experiments as formal statistical evidence.

## 5 Discussion

Discuss where AP-SRR-PSO helps, where it does not, why it may not dominate DE/SHADE/CMA-ES, and how the resource-reallocation view explains the behavior.

## 6 Conclusion

Conclude conservatively: AP-SRR-PSO improves PSO-family robustness by reallocating less productive search resources through an adaptive restart portfolio and contribution feedback.
