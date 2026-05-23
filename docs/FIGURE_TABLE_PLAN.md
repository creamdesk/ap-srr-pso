# Figure and Table Plan

All formal paper figures must be vector graphics. Use PDF for LaTeX inclusion and SVG for later editing. PNG is preview only.

## Figures

1. Overall framework of AP-SRR-PSO
   - show PSO iteration, state detection, IPS, restart intensity, adaptive portfolio, RCA feedback, and population update.

2. Ineffective particle scoring illustration
   - show productive particles, less productive particles, protected elites, and reallocated particles.

3. Convergence curves
   - use representative functions such as F1, F3/F10, F13/F20, and composition functions if supported.

4. Average ranking
   - generated from statistical rank CSV.

5. Ablation study
   - compare AP-SRR-PSO, NO-IPS, NO-ARP, NO-RCA, ARPSO-SRR, and PSO-RS.

6. Restart behavior
   - show restart_count, operator_usage, and operator_success.

7. Runtime comparison
   - report average wall-clock runtime by algorithm.

## Tables

1. Parameter settings
2. Main comparison, mean plus standard deviation
3. Wilcoxon Win/Tie/Loss
4. Friedman average ranking
5. Ablation results
6. Runtime comparison

## Style rules

- no Chinese labels in formal plots;
- no decorative backgrounds;
- consistent font sizes and line widths;
- IEEE double-column friendly sizes;
- do not hard-code winners manually;
- generate tables from CSV outputs.
