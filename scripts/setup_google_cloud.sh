#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y \
  git wget curl unzip zip htop tmux tree \
  build-essential python3 python3-pip python3-venv \
  libopenblas-dev liblapack-dev gfortran

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "环境安装完成。下一步运行：python experiments/smoke_test.py"
