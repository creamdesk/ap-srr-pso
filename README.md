# AP-SRR-PSO：自适应组合搜索资源重分配粒子群优化 SCI 项目

本仓库用于整理、实现和复现实验 **AP-SRR-PSO（Adaptive Portfolio Search Resource Reallocation Particle Swarm Optimization）**。

中文名称：**自适应组合搜索资源重分配粒子群优化算法**。

项目目标不是简单改一个 PSO 代码，而是围绕 SCI 论文标准，建立一套完整的算法研究工程，包括：算法实现、CEC 基准测试、批量实验、统计检验、消融实验、收敛曲线、重启/资源重分配行为分析、运行时间分析和论文图表生成。

## 一、研究定位

AP-SRR-PSO 是在已有 ARPSO-SRR 基础上的 SCI 升级版本。核心思想是：

1. 识别低效粒子，而不是盲目重启粒子；
2. 将有限函数评价资源从低效搜索区域重新分配到更有潜力的搜索区域；
3. 使用自适应重启算子组合，而不是固定单一重启策略；
4. 根据不同重启算子的历史贡献动态分配使用概率；
5. 在保持 PSO 简洁性的基础上提升复杂函数上的鲁棒性和稳定性。

建议论文叙事主线：

```text
PSO → ARPSO-SRR → AP-SRR-PSO
```

其中：

- **PSO**：标准粒子群优化算法；
- **ARPSO-SRR**：已有的搜索资源重分配版本；
- **AP-SRR-PSO**：SCI 升级版，增加自适应组合算子与贡献度分配机制。

## 二、项目结构

```text
ap-srr-pso/
├── algorithms/              # 算法实现：PSO、ARPSO-SRR、AP-SRR-PSO 等
├── benchmarks/              # CEC2017、CEC2022 等基准函数适配器
├── experiments/             # 实验入口：主实验、消融实验、收敛实验、运行时间实验
├── analysis/                # 统计检验和图表生成脚本
├── configs/                 # YAML 实验配置文件
├── results/                 # 实验结果输出目录
│   ├── raw/                 # 原始实验结果 CSV
│   ├── summary/             # 汇总结果
│   ├── stats/               # 统计检验结果
│   └── figures/             # 论文图表 PDF/SVG
├── paper/                   # 论文相关文件
│   ├── figures/             # 论文矢量图
│   └── tables/              # 论文表格
├── scripts/                 # 一键运行脚本
├── docs/                    # 项目计划、实验规范、论文笔记
├── logs/                    # 运行日志
└── legacy/                  # 旧版 ARPSO-SRR 成果归档，不直接改动
```

## 三、计划支持的算法

基础与对比算法：

- PSO
- PSO-RS
- PSO-AW
- CLPSO
- HPSO-TVAC
- DE
- JADE / SHADE / L-SHADE（后续补充）

本文方法与变体：

- ARPSO-SRR：旧版搜索资源重分配算法
- AP-SRR-PSO：SCI 升级主方法
- AP-SRR-PSO without IPS：去掉低效粒子评分
- AP-SRR-PSO without ARP：去掉自适应重启算子组合
- AP-SRR-PSO without RCA：去掉重启贡献度分配

## 四、计划支持的基准测试

优先级从高到低：

1. CEC2017 30D：主实验；
2. CEC2017 50D：可扩展性实验；
3. CEC2022 20D：泛化验证；
4. CEC2014 / CEC2020：备选补充。

## 五、计划输出的论文证据

- Mean / Std 结果表；
- Wilcoxon signed-rank test；
- Friedman average ranking；
- Holm post-hoc correction；
- Win/Tie/Loss 统计；
- 收敛曲线；
- 重启次数与资源重分配行为图；
- 算子贡献度变化曲线；
- 运行时间分析；
- 消融实验表。

## 六、环境安装

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip "setuptools<81" wheel
pip install -r requirements.txt
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip "setuptools<81" wheel
pip install -r requirements.txt
```

`setuptools<81` is required because the current `opfunu` CEC adapter imports `pkg_resources`.

## 七、快速自检

```bash
python -m experiments.smoke_test
```

预期输出：

```text
环境检查通过
PSO 小规模测试通过
结果文件已生成
```

## 八、可复现实验入口

These commands are the supported entry points after cloning the repository:

```bash
# Smoke test; runs quickly and writes results/summary/smoke_test_result.csv.
python -m experiments.smoke_test

# Six-group ARPSO-SRR ablation dry-run; does not execute expensive optimization.
python -m experiments.run_ablation6 --dry-run

# Tiny real pilot that validates raw/summary/table/figure generation.
python -m experiments.run_ablation6 --config configs/ablation6_pilot.yaml
python -m analysis.generate_tables --experiment ablation6_pilot
python -m analysis.generate_figures --experiment ablation6_pilot --no-png

# Six-group ARPSO-SRR ablation pilot; not a formal paper result unless runs/max_fes are raised.
python -m experiments.run_ablation6

# Protected CEC2017 30D main experiment dry-run.
python -m experiments.run_cec2017_main --dry-run

# Formal run is protected and requires explicit confirmation.
python -m experiments.run_cec2017_main --confirm-formal-run

# Generate LaTeX tables from existing result CSVs.
python -m analysis.generate_tables --experiment cec2017_30d_probe

# Generate vector figures from existing result CSVs/JSONL.
python -m analysis.generate_figures --experiment cec2017_30d_probe --no-png
```

CI intentionally runs smoke tests, config validation, dry-runs, and pytest only. It does not run full CEC2017 experiments.

## 九、结果目录

```text
results/raw/       raw per-run CSV files
results/summary/   grouped mean/std/runtime summaries
results/stats/     Wilcoxon/Friedman/Holm/average-rank CSVs
results/figures/   PDF/SVG paper figures
paper/tables/      LaTeX table outputs
paper/figures/     synced paper figure outputs
```

`results/` is ignored by Git by default. Do not commit large experiment outputs unless a tiny example artifact is intentionally selected.

## 十、当前阶段任务

当前阶段不是直接投稿，而是先完成 SCI 工程化基础：

1. 迁移旧版 ARPSO-SRR 代码和结果到 `legacy/`；
2. 建立统一算法接口；
3. 建立统一 CEC benchmark adapter；
4. 实现 AP-SRR-PSO 第一版；
5. 跑 smoke test；
6. 跑 CEC2017 30D 小规模验证；
7. 扩展到完整 30 runs；
8. 自动生成统计检验和论文图表。

## 十一、命名规则

- 仓库名：`ap-srr-pso`
- 主方法：`AP-SRR-PSO`
- 旧方法：`ARPSO-SRR`
- 中文主方法：`自适应组合搜索资源重分配粒子群优化算法`
- 不再使用：`ARPSO-v4` 作为论文方法名

## 十二、GitHub Actions

The `tests` workflow installs Python dependencies, runs the smoke test, validates core configs, checks protected dry-runs, checks table/figure entry points, and runs pytest. Full CEC2017 experiments are deliberately excluded from CI.

Recent CI failures were caused by API drift between tests and `experiments.run_experiment`, plus Node 20 deprecation warnings from older GitHub actions. The workflow now uses current `actions/checkout` and `actions/setup-python` releases and validates the stable dry-run APIs.

## 十三、TODO

1. Add stronger baselines such as CLPSO, HPSO-TVAC, JADE/SHADE, and CMA-ES before journal submission.
2. Run 30D pilot before any formal 30-run experiment.
3. Review ARPSO-EIS terminology against the final paper wording.
4. Add richer convergence/restart behavior figures once formal data are available.
5. Keep engineering validation data separate from formal paper results.

## 十四、注意事项

1. `legacy/` 只做旧成果归档，不直接修改；
2. 大规模实验结果不要直接提交到 GitHub；
3. 论文图片优先输出 PDF/SVG 矢量图；
4. 所有实验必须记录随机种子；
5. 所有算法必须使用统一接口，方便批量实验和统计分析。
