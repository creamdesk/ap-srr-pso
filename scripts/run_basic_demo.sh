#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python experiments/run_experiment.py \
  --benchmark Sphere \
  --dimension 10 \
  --functions 1 \
  --algorithms PSO PSO-RS PSO-AW ARPSO-SRR AP-SRR-PSO DE \
  --runs 3 \
  --max-fes 5000 \
  --population-size 30 \
  --output results/raw/basic_demo.csv \
  --save-curves

python analysis/summarize_results.py --input results/raw/basic_demo.csv
python analysis/statistical_tests.py --input results/raw/basic_demo.csv --target AP-SRR-PSO
python analysis/plot_results.py --rank-csv results/stats/basic_demo_average_rank.csv --output results/figures/basic_demo_average_rank.pdf
