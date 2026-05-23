from experiments.config_loader import load_yaml_config
from experiments.experiment_runner import run_experiment, tasks as build_tasks


def test_runner_dry_run_plans_tasks():
    cfg = load_yaml_config('configs/mini_validation.yaml')
    cfg['runs'] = 1
    cfg['functions'] = [1]
    cfg['algorithms'] = ['PSO']
    planned_tasks = build_tasks(cfg)
    assert len(planned_tasks) == 1
    result = run_experiment(cfg, dry_run=True)
    assert result['planned_tasks'] == 1
    assert result['dry_run'] is True
