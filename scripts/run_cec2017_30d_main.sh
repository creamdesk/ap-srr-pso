#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Google Cloud 多核 CPU 正式实验示例。
# n-jobs 不要盲目开满，建议先从 8 开始观察 htop 和内存。
python experiments/run_experiment.py \
  --benchmark CEC2017 \
  --dimension 30 \
  --functions 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 \
  --algorithms PSO PSO-RS PSO-AW ARPSO-SRR AP-SRR-PSO AP-SRR-PSO-no-IPS AP-SRR-PSO-no-ARP AP-SRR-PSO-no-RCA DE \
  --runs 30 \
  --max-fes 300000 \
  --population-size 50 \
  --output results/raw/cec2017_30d_main.csv \
  --n-jobs 8

python analysis/summarize_results.py --input results/raw/cec2017_30d_main.csv
python analysis/statistical_tests.py --input results/raw/cec2017_30d_main.csv --target AP-SRR-PSO
