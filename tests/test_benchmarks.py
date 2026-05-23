import numpy as np
import pytest
from benchmarks.problem_factory import build_problem


def test_sphere_problem():
    p = build_problem("Sphere", function_id=1, dimension=5)
    assert p.dimension == 5
    assert p.objective(np.zeros(5)) == 0.0


def test_cec2017_f1_loads_or_fails_clearly():
    try:
        p = build_problem("CEC2017", function_id=1, dimension=10)
        value = p.objective(np.zeros(p.dimension))
        assert isinstance(float(value), float)
    except Exception as exc:
        pytest.fail(f"CEC2017 F1 failed to load/evaluate: {exc!r}")
