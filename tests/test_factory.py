from algorithms.factory import build_optimizer


def test_factory_core_algorithms():
    for name in ["AP-SRR-PSO", "ARPSO-SRR", "PSO", "PSO-RS", "PSO-AW", "DE"]:
        opt = build_optimizer(name, population_size=8, seed=2026)
        assert hasattr(opt, "optimize")
