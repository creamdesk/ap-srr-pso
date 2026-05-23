from experiments.result_writer import RAW_FIELDS, SUMMARY_FIELDS


def test_raw_schema_contains_required_fields():
    for field in ['benchmark', 'function_id', 'dimension', 'algorithm', 'run', 'seed', 'best_fitness', 'status', 'error']:
        assert field in RAW_FIELDS


def test_summary_schema_contains_required_fields():
    for field in ['benchmark', 'function_id', 'dimension', 'algorithm', 'runs', 'mean_best', 'success_count', 'failure_count']:
        assert field in SUMMARY_FIELDS
