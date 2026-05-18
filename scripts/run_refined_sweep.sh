#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# 第二轮精筛：围绕第一轮胜出的 RARE 和 DIFF 做细粒度筛选。
# 不是正式论文实验，目标是选出下一版主算法候选。
python experiments/run_experiment.py \
  --benchmark CEC2017 \
  --dimension 10 \
  --functions 1 3 5 7 10 15 20 23 25 29 \
  --algorithms \
    PSO \
    ARPSO-SRR \
    DE \
    AP-SRR-PSO-RARE \
    AP-SRR-PSO-DIFF \
    AP-SRR-PSO-RD \
    AP-SRR-PSO-RD-C \
    AP-SRR-PSO-RD-M \
    AP-SRR-PSO-RD-E \
  --runs 10 \
  --max-fes 100000 \
  --population-size 30 \
  --output results/raw/refined_sweep_cec2017_10d.csv \
  --n-jobs 2

python analysis/summarize_results.py --input results/raw/refined_sweep_cec2017_10d.csv
python analysis/statistical_tests.py --input results/raw/refined_sweep_cec2017_10d.csv
python analysis/plot_results.py --rank-csv results/stats/refined_sweep_cec2017_10d_average_rank.csv --output results/figures/refined_sweep_average_rank.pdf

echo "精筛完成。重点查看："
echo "results/summary/refined_sweep_cec2017_10d_summary.csv"
echo "results/stats/refined_sweep_cec2017_10d_average_rank.csv"
echo "results/figures/refined_sweep_average_rank.pdf"
