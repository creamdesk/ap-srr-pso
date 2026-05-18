#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python experiments/run_experiment.py \
  --benchmark CEC2017 \
  --dimension 10 \
  --functions 1 3 10 \
  --algorithms PSO ARPSO-SRR AP-SRR-PSO DE \
  --runs 3 \
  --max-fes 10000 \
  --population-size 30 \
  --output results/raw/cec2017_smoke.csv \
  --n-jobs 1 \
  --save-curves

python analysis/summarize_results.py --input results/raw/cec2017_smoke.csv
python analysis/statistical_tests.py --input results/raw/cec2017_smoke.csv --target AP-SRR-PSO
