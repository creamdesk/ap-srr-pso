from experiments.config_loader import load_yaml_config

def test_mini_config_loads():
    cfg = load_yaml_config('configs/mini_validation.yaml')
    assert cfg['benchmark'] == 'CEC2017'
