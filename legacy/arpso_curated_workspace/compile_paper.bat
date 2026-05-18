@echo off
chcp 65001 >nul
cd /d "%~dp0paper"

echo ============================================
echo Compiling ARPSO paper with pdflatex
echo Working directory: %cd%
echo ============================================

pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

echo.
echo Done. Output should be paper\main.pdf
pause
