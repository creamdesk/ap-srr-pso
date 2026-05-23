# Next Steps

This roadmap follows `docs/PAPER_STRATEGY.md`.

## Current Status

- Local environment works.
- `setuptools<81` is pinned for `opfunu/pkg_resources` compatibility.
- Smoke test passed.
- Factory check passed for AP-SRR-PSO, ARPSO-SRR, PSO, PSO-RS, PSO-AW, and DE.
- CEC2017 F1/F3/F10 can be loaded and evaluated.
- Mini validation passed with 30 ok / 0 failed.
- 30D probe passed with 30 ok / 0 failed.

These are engineering validations, not formal paper results.

## Immediate Engineering Tasks

1. Commit the paper strategy and engineering framework once reviewed.
2. Keep `results/` ignored unless intentionally adding a tiny example artifact.
3. Run dry-runs before any pilot or formal batch.
4. Add stronger baselines or document their implementation plan.
5. Add table generation for LaTeX-ready paper tables.
6. Add convergence-curve and restart-behavior figure scripts.

## Next Experiment

Run a 30D pilot only after dry-runs are clean:

- functions: F1, F3, F5, F10, F13, F20
- algorithms: PSO, PSO-RS, PSO-AW, ARPSO-SRR, AP-SRR-PSO, DE
- runs: 5
- max_fes: 30000 or 50000
- population_size: 50

Pilot results are for pipeline and runtime assessment only.

## Before Formal Experiment

Do not start 30-run formal experiments until:

- raw/summary/stats/figures all work on pilot data;
- low-run warning is documented;
- AP-SRR-PSO ablation variants are checked;
- stronger baselines are implemented or explicitly planned;
- output schema is stable;
- runtime is acceptable locally or cloud execution is prepared.

## Suggested Commit

Recommended commit message after review:

```text
docs: fix AP-SRR-PSO paper strategy and experiment roadmap
```

If including scripts and schema changes:

```text
chore: align experiment pipeline with AP-SRR-PSO paper strategy
```
