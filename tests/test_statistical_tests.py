import pandas as pd

from analysis.statistical_tests import average_rank, normalize_input


def test_average_rank_from_tiny_frame():
    df = pd.DataFrame([
        {'function_id': 1, 'algorithm': 'A', 'best_fitness': 1.0, 'run': 1},
        {'function_id': 1, 'algorithm': 'B', 'best_fitness': 2.0, 'run': 1},
        {'function_id': 2, 'algorithm': 'A', 'best_fitness': 3.0, 'run': 1},
        {'function_id': 2, 'algorithm': 'B', 'best_fitness': 1.0, 'run': 1},
    ])
    out = average_rank(normalize_input(df))
    assert set(out['algorithm']) == {'A', 'B'}
    assert 'average_rank' in out.columns
