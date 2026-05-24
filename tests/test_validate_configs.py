from pathlib import Path

from experiments.validate_configs import validate_config


def test_mini_validation_config_is_valid():
    errors = validate_config(Path('configs/mini_validation.yaml'))
    assert errors == []


def test_ablation6_config_is_valid():
    errors = validate_config(Path('configs/ablation6.yaml'))
    assert errors == []
