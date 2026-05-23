# Cloud Run Guide

This project is CPU-bound for CEC benchmark experiments. GPU instances are not required unless future code is rewritten for GPU vectorization.

## Recommended cloud profile

Use a Linux CPU instance:

- Ubuntu 22.04 LTS
- 8 to 32 vCPU
- 16 to 64 GB memory
- 80 to 100 GB system disk
- SSH key login

For pilot experiments, 8 vCPU / 16 GB is acceptable. For medium-scale experiments, 16 vCPU / 32 GB is preferred. For full formal experiments, use 32 vCPU / 64 GB or split the run by function groups.

## Setup commands

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip build-essential tmux htop unzip
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/creamdesk/ap-srr-pso.git
cd ap-srr-pso
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip 'setuptools<81' wheel
pip install -r requirements.txt
```

## Safe validation

```bash
python experiments/smoke_test.py
python experiments/run_cec2017_30d_probe.py --dry-run
python experiments/run_cec2017_main.py --dry-run
python experiments/check_cec2017_availability.py
python -m pytest tests -q
```

## Long-running experiments

Use tmux:

```bash
tmux new -s apsrr
source .venv/bin/activate
python experiments/run_cec2017_pilot.py --resume
```

Detach with `Ctrl+B`, then `D`. Reattach with:

```bash
tmux attach -t apsrr
```

## Backup

Do not trust a cloud VM as the only storage. After each useful batch:

```bash
tar -czf apsrr-results-$(date +%Y%m%d-%H%M).tar.gz results/
```

Download the archive or upload it to object storage. Keep code in GitHub and keep results backed up separately.

## Cost control

Stop or delete the instance after experiments. Check for unattached disks, static IPs, snapshots, and machine images. Results should be backed up before deleting any disk.
