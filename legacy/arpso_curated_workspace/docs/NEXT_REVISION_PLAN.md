# NEXT_REVISION_PLAN

## Step 1: Compile the curated manuscript

Run:

```text
compile_paper.bat
```

If compilation fails, first check figure/table paths in `paper/main.tex`.

## Step 2: Rewrite Ablation Study

Core claim:

```text
ARPSO-SRR and ARPSO-Local obtain the best average rank.
ARPSO-Local uses substantially more restarted particles.
ARPSO-SRR therefore provides comparable ranking performance with a more economical restart behavior.
```

Avoid claiming:

```text
SRR significantly beats all variants.
SRR is best on every function.
```

## Step 3: Rewrite Results and Discussion

Recommended structure:

```text
A. Ablation Study
B. Overall Performance on CEC2017
C. Convergence and Restart Behavior
D. Statistical Analysis
```

Use conservative wording:

```text
competitive
stable improvement
more economical search resource reallocation
```

Avoid:

```text
state-of-the-art
overall best
significantly better than all competitors
```

## Step 4: Final submission package

Final submission should contain only:

```text
main.tex
IEEEtran.cls
figures/*.pdf
tables/*.tex
refs.bib if used
```

Do not submit:

```text
analysis_data/
code/
docs/
old_versions/
raw CSV files
```
