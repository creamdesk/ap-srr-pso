# FINAL_FILE_DECISION

## Final manuscript

Use only:

```text
paper/main.tex
```

This file is copied from:

```text
论文/main.tex
```

Do not edit multiple `main.tex` versions in parallel.

## Final figures

Use final figure files from:

```text
paper/figures/
```

Editable TikZ/source files are kept in:

```text
paper/figure_sources/
```

Recommended final figures:

```text
framework_tikz_final.pdf
algorithm_summary_tikz_final.pdf
ablation6_landscape_tikz_final.pdf
convergence_curve_tikz_final.pdf
restart_behavior_tikz_final.pdf
```

## Final tables

Use:

```text
paper/tables/
```

Recommended tables:

```text
table_ablation6.tex
table_cec2017_friedman.tex
table_cec2017_wilcoxon_summary.tex
```

## Data rule

Do not place huge raw CSV files into `paper/`.

Use summarized data from:

```text
analysis_data/
```

Huge files intentionally excluded:

```text
ablation6_restart_details.csv
ablation6_raw_results.csv
ablation6_curve_records.csv
cec2017_raw_results.csv
full_parallel_checkpoint_*.csv
```
