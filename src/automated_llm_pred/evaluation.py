from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from automated_llm_pred.analysis import AnalysisExecutor, AnalysisPlan


def grounding_score(result_df: pd.DataFrame, bullets: list[str]) -> dict[str, Any]:
    if result_df.empty:
        return {"pass": False, "checked": len(bullets), "grounded": 0, "ratio": 0.0}

    corpus = result_df.head(200).to_csv(index=False).lower()
    grounded = 0
    for bullet in bullets:
        numbers = re.findall(r"-?\d+(?:\.\d+)?", bullet)
        if not numbers:
            continue
        if any(num.lower() in corpus for num in numbers):
            grounded += 1
    checked = len([b for b in bullets if re.findall(r"-?\d+(?:\.\d+)?", b)])
    ratio = grounded / checked if checked else 1.0
    return {"pass": ratio >= 0.7, "checked": checked, "grounded": grounded, "ratio": round(ratio, 4)}


@dataclass
class BenchmarkCase:
    name: str
    plan: AnalysisPlan
    required_columns: list[str]


def core_benchmark_cases() -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            name="country_revenue",
            plan=AnalysisPlan(
                groupby=["country"],
                metrics=[{"col": "net_revenue", "agg": "sum", "as": "country_revenue"}],
                sort_by="net_revenue_sum",
                sort_dir="desc",
                limit=10,
            ),
            required_columns=["country", "net_revenue_sum"],
        ),
        BenchmarkCase(
            name="monthly_revenue",
            plan=AnalysisPlan(
                groupby=["invoice_ym"],
                metrics=[{"col": "net_revenue", "agg": "sum", "as": "monthly_revenue"}],
                sort_by="invoice_ym",
                sort_dir="asc",
                limit=200,
            ),
            required_columns=["invoice_ym", "net_revenue_sum"],
        ),
        BenchmarkCase(
            name="return_rate",
            plan=AnalysisPlan(
                groupby=["is_return"],
                metrics=[{"col": "", "agg": "count", "as": "rows"}],
                sort_by="rows",
                sort_dir="desc",
                limit=10,
            ),
            required_columns=["is_return", "count_rows"],
        ),
    ]


def run_core_benchmark(df: pd.DataFrame) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    passes = 0
    for case in core_benchmark_cases():
        out = AnalysisExecutor.execute(df, case.plan)
        columns = list(out.columns)
        ok = all(col in columns for col in case.required_columns) and len(out) > 0
        results.append(
            {
                "name": case.name,
                "pass": ok,
                "rows": int(len(out)),
                "columns": columns,
            }
        )
        if ok:
            passes += 1
    total = len(results)
    return {
        "pass_rate": round(passes / total if total else 0, 4),
        "passed": passes,
        "total": total,
        "cases": results,
    }


def save_benchmark_report(benchmark: dict[str, Any], out_dir: str, out_name: str = "benchmark.json") -> Path:
    path = Path(out_dir) / out_name
    path.write_text(json.dumps(benchmark, indent=2), encoding="utf-8")
    return path
