# CAIT IEEE compliant LaTeX framework

Compile order:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Main compliance notes:

- Uses `\documentclass[conference]{IEEEtran}`.
- Does not modify margins, column widths, line spacing, or fonts.
- Title avoids subtitle, colon, math, footnotes, and special symbols.
- Abstract avoids math and special symbols as much as possible.
- Captions and labels follow IEEE convention: table captions above tables, figure captions below figures, labels after captions.
- Template instruction text and generic acknowledgment were removed.
- References use BibTeX with IEEEtran style.

```
算法改进
├─ arpso_all_figures_final_pack
│  ├─ ablation_bar_tikz_final.aux
│  ├─ ablation_bar_tikz_final.log
│  ├─ ablation_bar_tikz_final.pdf
│  ├─ ablation_bar_tikz_final.tex
│  ├─ algorithm_block_for_main.tex
│  ├─ algorithm_summary_tikz_final.aux
│  ├─ algorithm_summary_tikz_final.log
│  ├─ algorithm_summary_tikz_final.pdf
│  ├─ algorithm_summary_tikz_final.tex
│  ├─ convergence_curve_tikz_final.aux
│  ├─ convergence_curve_tikz_final.log
│  ├─ convergence_curve_tikz_final.pdf
│  ├─ convergence_curve_tikz_final.tex
│  ├─ framework_tikz_final.aux
│  ├─ framework_tikz_final.log
│  ├─ framework_tikz_final.pdf
│  ├─ framework_tikz_final.tex
│  ├─ README_使用说明.txt
│  ├─ restart_behavior_tikz_final.aux
│  ├─ restart_behavior_tikz_final.log
│  ├─ restart_behavior_tikz_final.pdf
│  └─ restart_behavior_tikz_final.tex
├─ code
│  ├─ benchmarks.py
│  ├─ cec_adapter.py
│  ├─ common.py
│  ├─ __pycache__
│  │  ├─ cec_adapter.cpython-313.pyc
│  │  ├─ common.cpython-313.pyc
│  │  └─ 优化算法.cpython-313.pyc
│  ├─ 优化算法.py
│  ├─ 权重敏感性分析.py
│  ├─ 消融实验.py
│  ├─ 生成论文图表.py
│  ├─ 统计检验.py
│  ├─ 统计检验_CEC.py
│  ├─ 运行CEC实验.py
│  ├─ 运行CEC实验_并行版.py
│  └─ 运行实验.py
├─ figures
│  ├─ ablation_bar_tikz_final.pdf
│  ├─ algorithm_summary_tikz_final.pdf
│  ├─ arpso_srr_framework.pdf
│  ├─ convergence_curve_tikz_final.pdf
│  ├─ Framework of the proposed ARPSO-SRR.png
│  ├─ framework_tikz_final.pdf
│  ├─ restart_behavior_tikz_final.pdf
│  └─ 流程图.txt
├─ papers
│  ├─ 2004.09969v2.pdf
│  ├─ 2206.00835v1.pdf
│  ├─ 535-C037.pdf
│  ├─ a20modified20pso.pdf
│  ├─ ClercKennedyPSOExplosion-Stability.pdf
│  ├─ DefinitionsofCEC2014benchmarksuitePartA20140105.pdf
│  ├─ electronics-11-02339-v2.pdf
│  ├─ electronics-12-00491-v2.pdf
│  ├─ peerj-cs-2253.pdf
│  ├─ PoliKennedyBlackwellSI2007.pdf
│  ├─ s11831-021-09694-4.pdf
│  ├─ s40747-023-01012-8.pdf
│  ├─ _reading6 1995 particle swarming.pdf
│  └─ 说明.txt
├─ paper_figures
├─ paper_tables
├─ README.md
├─ results
│  └─ cec
│     ├─ cec2017_full_parallel_checkpoint_raw_results.csv
│     └─ cec2017_full_parallel_checkpoint_restart_details.csv
├─ sections
├─ tables
│  ├─ friedman_test_table.tex
│  ├─ main_results_table.tex
│  └─ wilcoxon_summary_table.tex
├─ 中文.txt
├─ 英文.txt
└─ 论文
   ├─ IEEEtran.cls
   ├─ main.aux
   ├─ main.log
   ├─ main.pdf
   ├─ main.synctex.gz
   ├─ main.tex
   ├─ README.md
   └─ 英文.txt

```
```
算法改进
├─ arpso_real_data_updated_latex_pack
│  ├─ ablation_bar_tikz_final.pdf
│  ├─ ablation_bar_tikz_final.tex
│  ├─ algorithm_block_for_main.tex
│  ├─ algorithm_summary_tikz_final.aux
│  ├─ algorithm_summary_tikz_final.log
│  ├─ algorithm_summary_tikz_final.pdf
│  ├─ algorithm_summary_tikz_final.tex
│  ├─ cec2017_wilcoxon_summary_ARPSO_SRR_from_raw.csv
│  ├─ convergence_curve_tikz_final.pdf
│  ├─ convergence_curve_tikz_final.tex
│  ├─ framework_tikz_final.pdf
│  ├─ framework_tikz_final.tex
│  ├─ main_ei_arpso_srr_real_data.aux
│  ├─ main_ei_arpso_srr_real_data.log
│  ├─ main_ei_arpso_srr_real_data.pdf
│  ├─ main_ei_arpso_srr_real_data.synctex.gz
│  ├─ main_ei_arpso_srr_real_data.tex
│  ├─ restart_behavior_tikz_final.pdf
│  └─ restart_behavior_tikz_final.tex
├─ code
│  ├─ auto_finalize_ablation6.py
│  ├─ benchmarks.py
│  ├─ cec_adapter.py
│  ├─ common.py
│  ├─ __pycache__
│  │  ├─ cec_adapter.cpython-313.pyc
│  │  ├─ common.cpython-313.pyc
│  │  └─ 优化算法.cpython-313.pyc
│  ├─ 优化算法.py
│  ├─ 权重敏感性分析.py
│  ├─ 消融实验.py
│  ├─ 生成论文图表.py
│  ├─ 统计检验.py
│  ├─ 统计检验_CEC.py
│  ├─ 运行CEC2017消融实验_6variants.py
│  ├─ 运行CEC实验.py
│  ├─ 运行CEC实验_并行版.py
│  └─ 运行实验.py
├─ figures
│  ├─ ablation_bar_tikz_final.pdf
│  ├─ convergence_curve_tikz_final.pdf
│  ├─ framework_tikz_final.pdf
│  ├─ restart_behavior_tikz_final.pdf
│  └─ 流程图.txt
├─ papers
│  ├─ 2004.09969v2.pdf
│  ├─ 2206.00835v1.pdf
│  ├─ 535-C037.pdf
│  ├─ a20modified20pso.pdf
│  ├─ ClercKennedyPSOExplosion-Stability.pdf
│  ├─ DefinitionsofCEC2014benchmarksuitePartA20140105.pdf
│  ├─ electronics-11-02339-v2.pdf
│  ├─ electronics-12-00491-v2.pdf
│  ├─ peerj-cs-2253.pdf
│  ├─ PoliKennedyBlackwellSI2007.pdf
│  ├─ s11831-021-09694-4.pdf
│  ├─ s40747-023-01012-8.pdf
│  ├─ _reading6 1995 particle swarming.pdf
│  └─ 说明.txt
├─ paper_auto_update
│  ├─ figures
│  │  ├─ ablation6_average_rank.pdf
│  │  ├─ ablation6_average_rank.png
│  │  └─ figure_ablation_rank.tex
│  ├─ reports
│  │  ├─ ablation6_final_summary.csv
│  │  ├─ ablation6_friedman_recomputed.csv
│  │  ├─ ablation6_rank_detail_recomputed.csv
│  │  ├─ ablation6_status_report.txt
│  │  ├─ ablation6_table_values.csv
│  │  └─ ablation6_wilcoxon_recomputed.csv
│  ├─ snippets
│  │  ├─ ablation_discussion_auto.tex
│  │  └─ restart_discussion_auto.tex
│  └─ tables
│     └─ table_ablation6.tex
├─ paper_figures
├─ paper_tables
│  ├─ table_cec2017_friedman.tex
│  └─ table_cec2017_wilcoxon_summary.tex
├─ README.md
├─ results
│  ├─ cec
│  │  ├─ cec2017_average_rank.csv
│  │  ├─ cec2017_friedman_average_rank.csv
│  │  ├─ cec2017_friedman_function_level.csv
│  │  ├─ cec2017_full_parallel_checkpoint_raw_results.csv
│  │  ├─ cec2017_full_parallel_checkpoint_restart_details.csv
│  │  ├─ cec2017_mean_curves.csv
│  │  ├─ cec2017_rank_detail.csv
│  │  ├─ cec2017_raw_results.csv
│  │  ├─ cec2017_restart_details.csv
│  │  ├─ cec2017_restart_summary.csv
│  │  ├─ cec2017_runtime_summary.csv
│  │  ├─ cec2017_summary_results.csv
│  │  ├─ cec2017_wilcoxon_per_function_details.csv
│  │  └─ cec2017_wilcoxon_summary_nsd.csv
│  └─ cec2017_ablation6
│     ├─ ablation6_average_rank.csv
│     ├─ ablation6_curve_records.csv
│     ├─ ablation6_errors.log
│     ├─ ablation6_friedman.csv
│     ├─ ablation6_group_average_rank.csv
│     ├─ ablation6_mean_curves.csv
│     ├─ ablation6_rank_detail.csv
│     ├─ ablation6_raw_results.csv
│     ├─ ablation6_restart_details.csv
│     ├─ ablation6_restart_summary.csv
│     ├─ ablation6_runtime_summary.csv
│     ├─ ablation6_summary_results.csv
│     ├─ ablation6_wilcoxon_per_function_details.csv
│     └─ ablation6_wilcoxon_summary.csv
├─ sections
├─ tables
│  ├─ friedman_test_table.tex
│  ├─ main_results_table.tex
│  └─ wilcoxon_summary_table.tex
├─ 中文.txt
├─ 英文.txt
└─ 论文
   ├─ IEEEtran.cls
   ├─ main.aux
   ├─ main.log
   ├─ main.pdf
   ├─ main.synctex.gz
   ├─ main.tex
   ├─ README.md
   └─ 英文.txt

```