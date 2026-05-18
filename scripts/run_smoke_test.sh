#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python experiments/smoke_test.py
