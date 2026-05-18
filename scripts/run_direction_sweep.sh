#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# 多方向小规模筛选，不是正式论文实验。
# 目标：快速判断哪种 AP-SRR-PSO 改法值得继续放大。
python experiments/run_experiment.py \
  --benchmark CEC2017 \
  --dimension 10 \
  --functions 1 3 10 15 23 \
  --algorithms \
    PSO \
    ARPSO-SRR \
    DE \
    AP-SRR-PSO-LOCAL \
    AP-SRR-PSO-DIFF \
    AP-SRR-PSO-RARE \
    AP-SRR-PSO-PORTFOLIO \
    AP-SRR-PSO-EXPLORE \
  --runs 5 \
  --max-fes 50000 \
  --population-size 30 \
  --output results/raw/direction_sweep_cec2017_10d.csv \
  --n-jobs 2 \
  --save-curves

python analysis/summarize_results.py --input results/raw/direction_sweep_cec2017_10d.csv
python analysis/statistical_tests.py --input results/raw/direction_sweep_cec2017_10d.csv --target AP-SRR-PSO
python analysis/plot_results.py --rank-csv results/stats/direction_sweep_cec2017_10d_average_rank.csv --output results/figures/direction_sweep_average_rank.pdf

echo "方向筛选完成。重点查看："
echo "results/summary/direction_sweep_cec2017_10d_summary.csv"
echo "results/stats/direction_sweep_cec2017_10d_average_rank.csv"
echo "results/figures/direction_sweep_average_rank.pdf"
