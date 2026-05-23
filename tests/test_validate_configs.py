from pathlib import Path

from experiments.validate_configs import validate_config


def test_mini_validation_config_is_valid():
    errors = validate_config(Path('configs/mini_validation.yaml'))
    assert errors == []
