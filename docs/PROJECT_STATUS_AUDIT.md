# Project Status Audit

This file records the current engineering and paper status of the AP-SRR-PSO repository.

## Current confirmed direction

The project is an SCI-oriented numerical optimization project centered on AP-SRR-PSO, not a generic PSO demo. The paper narrative should remain:

```text
premature convergence -> ineffective particles -> wasted function evaluations -> search resource reallocation -> adaptive restart portfolio -> restart credit assignment
```

## Current implemented core

- AP-SRR-PSO and variants are created through `algorithms/factory.py`.
- CEC2017 is loaded through `benchmarks/problem_factory.py` and `benchmarks/cec_adapter.py`.
- `setuptools<81` is required because the current opfunu path still relies on `pkg_resources`.
- Results should be written under `results/` and should not be committed.

## Engineering pipeline status

Implemented or added:

- reusable config loader;
- reusable result writer;
- common experiment runner;
- protected formal main experiment entry;
- mini validation entry;
- 30D probe entry;
- pilot, ablation, sensitivity, and runtime entries;
- CEC2017 availability checker;
- statistical analysis with run-alignment warnings;
- vector plotting utilities and several plot scripts;
- LaTeX table generator;
- basic pytest coverage.

## Formal experiment status

Not yet completed. Formal paper evidence still requires:

- CEC2017 F1-F30 availability check;
- 30D probe validation;
- 30D pilot validation;
- full 30-run formal experiment only after the pipeline is stable;
- stronger baseline plan or implementation;
- completed paper figures and tables generated from CSV results.

## Important warning

Smoke, mini validation, 30D probe, and pilot experiments are engineering checks. They must not be described as statistical evidence in the paper.
