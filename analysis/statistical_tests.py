"""统计检验脚本骨架。

后续正式实验结果生成后，在这里实现：
1. Wilcoxon signed-rank test；
2. Friedman test；
3. Holm post-hoc correction；
4. 平均排名；
5. Win/Tie/Loss 汇总。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon


REQUIRED_COLUMNS = {"function", "algorithm", "run", "best_fitness"}


def read_result_csv(path: str | Path) -> pd.DataFrame:
    """读取并检查实验结果 CSV。"""
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"结果文件缺少必要字段: {sorted(missing)}")
    return df


def wilcoxon_pairwise_placeholder() -> None:
    """成对 Wilcoxon 检验占位函数。"""
    _ = wilcoxon
    raise NotImplementedError("等待正式结果格式确定后实现。")


def friedman_test_placeholder() -> None:
    """Friedman 检验占位函数。"""
    _ = friedmanchisquare
    raise NotImplementedError("等待正式结果格式确定后实现。")
