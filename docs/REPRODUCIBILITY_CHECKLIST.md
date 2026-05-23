# Reproducibility Checklist

Record the following for every formal experiment.

## Environment

- operating system
- CPU model and core count
- memory
- Python version
- package versions
- Git commit hash

## Benchmark setup

- benchmark name
- function ids
- dimension
- lower and upper bounds
- optimum or bias if available
- MaxFEs
- population size
- independent runs

## Randomness

- base seed
- seed derivation rule
- seed for every run

## Algorithm setup

- canonical algorithm name
- all algorithm parameters
- restart parameters for AP-SRR-PSO
- ablation variant switches

## Outputs

- raw CSV
- summary CSV
- curves JSONL
- logs
- statistical CSVs
- PDF/SVG figures
- LaTeX tables

## Failures

- skipped functions
- failed runs
- exact error text
- opfunu compatibility notes

Engineering checks such as smoke, mini validation, probe, and pilot must not be reported as formal paper evidence.
