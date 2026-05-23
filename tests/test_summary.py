from experiments.result_writer import summarize_rows


def test_summary_rows_basic():
    rows = [
        {'experiment_name':'x','benchmark':'B','function':'F1','function_id':1,'dimension':5,'algorithm':'A','best_fitness':1.0,'runtime_seconds':0.1,'status':'ok'},
        {'experiment_name':'x','benchmark':'B','function':'F1','function_id':1,'dimension':5,'algorithm':'A','best_fitness':3.0,'runtime_seconds':0.2,'status':'ok'},
    ]
    summary = summarize_rows(rows)
    assert len(summary) == 1
    assert summary[0]['mean_best'] == 2.0
    assert summary[0]['success_count'] == 2
