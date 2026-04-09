from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from automated_llm_pred.data import prepare_online_retail_business_view
from automated_llm_pred.pipeline import run_case_study


class MockRouter:
    def ask_analysis(self, prompt: str, question: str = "") -> str:
        if '"metrics"' in prompt and '"groupby"' in prompt and "Return ONLY valid JSON" in prompt:
            return json.dumps(
                {
                    "groupby": ["country"],
                    "metrics": [{"col": "net_revenue", "agg": "sum", "as": "country_revenue"}],
                    "sort_by": "net_revenue_sum",
                    "sort_dir": "desc",
                    "limit": 10,
                }
            )
        return "- Revenue is concentrated in a few countries."

    def ask_plot(self, prompt: str, goal: str = "") -> str:
        if '"kind"' in prompt and "Return ONLY valid JSON" in prompt:
            return json.dumps(
                {
                    "kind": "bar",
                    "x": "country",
                    "y": "net_revenue",
                    "agg": "sum",
                    "top_k": 10,
                    "title": "Country Revenue",
                    "x_label": "Country",
                    "y_label": "Net Revenue",
                }
            )
        return "- UK and France are the top contributors."

    def ask_critic(self, prompt: str, context: str = "") -> str:
        return "- Output validated against computed evidence."


def test_run_case_study_generates_all_artifacts(tmp_path: Path):
    raw = pd.DataFrame(
        {
            "InvoiceNo": ["10001", "10002", "10003", "C10003", "10004"],
            "StockCode": ["A", "A", "B", "B", "C"],
            "Description": ["Item A", "Item A", "Item B", "Item B", "Item C"],
            "Quantity": [10, 2, 6, -1, 5],
            "InvoiceDate": [
                "2011-01-01 10:00:00",
                "2011-01-10 12:00:00",
                "2011-02-01 09:00:00",
                "2011-02-02 09:00:00",
                "2011-03-03 09:00:00",
            ],
            "UnitPrice": [2.5, 2.5, 4.0, 4.0, 1.0],
            "CustomerID": [11111, 11111, 22222, 22222, 33333],
            "Country": ["United Kingdom", "United Kingdom", "France", "France", "Germany"],
        }
    )
    df = prepare_online_retail_business_view(raw)
    paths = run_case_study(
        df=df,
        out_dir=str(tmp_path),
        title="Test Case Study",
        questions=[],
        plot_goals=[],
        router=MockRouter(),
    )

    for key in ("html", "pdf", "executive_summary", "technical_appendix", "benchmark_json"):
        assert Path(paths[key]).exists()
