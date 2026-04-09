import pandas as pd

from automated_llm_pred.analysis import AnalysisExecutor, AnalysisPlan


def test_analysis_executor_groupby_sum_and_sort():
    df = pd.DataFrame(
        {
            "country": ["UK", "UK", "FR", "FR"],
            "net_revenue": [100.0, 50.0, 80.0, 10.0],
        }
    )
    plan = AnalysisPlan(
        groupby=["country"],
        metrics=[{"col": "net_revenue", "agg": "sum", "as": "country_revenue"}],
        sort_by="net_revenue_sum",
        sort_dir="desc",
        limit=5,
    )
    out = AnalysisExecutor.execute(df, plan)
    assert list(out.columns) == ["country", "net_revenue_sum"]
    assert out.iloc[0]["country"] == "UK"
    assert float(out.iloc[0]["net_revenue_sum"]) == 150.0
