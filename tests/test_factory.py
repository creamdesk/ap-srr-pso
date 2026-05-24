from algorithms.factory import build_optimizer


def test_factory_core_algorithms():
    for name in ["AP-SRR-PSO", "ARPSO-SRR", "PSO", "PSO-RS", "PSO-AW", "DE"]:
        opt = build_optimizer(name, population_size=8, seed=2026)
        assert hasattr(opt, "optimize")


def test_factory_ablation6_algorithms_are_distinct():
    expected = {
        "ARPSO-Local": "ARPSO-Local",
        "ARPSO-SRR": "ARPSO-SRR",
        "ARPSO-EIS": "ARPSO-EIS",
        "ARPSO-Fixed": "ARPSO-Fixed",
        "ARPSO-Global": "ARPSO-Global",
        "PSO-RS": "PSO-RS",
    }
    for name, display_name in expected.items():
        opt = build_optimizer(name, population_size=8, seed=2026)
        assert hasattr(opt, "optimize")
        assert opt.name == display_name
