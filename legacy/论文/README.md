ARPSO-SRR CAIT IEEE LaTeX package

Files:
- main.tex: CAIT/IEEE conference manuscript draft focused on ARPSO-SRR.
- main.pdf: compiled preview.
- IEEEtran.cls: IEEE conference class file.

Compile:
  pdflatex main.tex
  pdflatex main.tex

Notes:
- This version adds a computational complexity subsection after Algorithm Procedure.
- The local perturbation parameter is written as sigma^t and bounded by sigma_min and sigma_max.
- ARPSO-EIS is positioned as an ablation/comparison variant, not the main method.
- Fig. 1 has been converted from a plain placeholder to a framework flow schematic.
- Fig. 2 and the result tables still need to be replaced with final experimental results after all runs finish.
