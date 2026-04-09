from __future__ import annotations

import json
from typing import Any

import pandas as pd


class Prompts:
    @staticmethod
    def analysis_plan(profile: dict[str, Any], question: str) -> str:
        return f"""
You are a senior analytics planner.

Return ONLY valid JSON.

DATASET PROFILE:
{json.dumps(profile, ensure_ascii=False)[:22000]}

QUESTION:
{question}

Schema:
{{
  "target": "<optional col>",
  "filters": [{{"col":"<col>","op":"==|!=|>|>=|<|<=|in|contains|notnull|isnull","value":<any>}}],
  "groupby": ["<col>", "..."],
  "metrics": [{{"col":"<col or empty for rows>","agg":"count|nunique|mean|sum|min|max|median","as":"<alias>"}}],
  "sort_by": "<column or alias or null>",
  "sort_dir": "asc|desc",
  "limit": 20
}}

Rules:
- Use existing columns only.
- Prefer grouped metrics for business questions.
- If user asks top N, use descending sort and limit N.
- Keep output deterministic and compact.
"""

    @staticmethod
    def story(profile: dict[str, Any], question: str, result: pd.DataFrame) -> str:
        return f"""
Answer the user question using only computed evidence.

QUESTION:
{question}

PROFILE:
{json.dumps(profile, ensure_ascii=False)[:18000]}

COMPUTED RESULT CSV:
{result.head(120).to_csv(index=False)}

Output format:
- Bullet points only (3 to 6 lines).
- No speculation or unverifiable claims.
- Prioritize rankings, gaps, concentration, and concrete values when they are visible.
- If evidence is insufficient, state: "Not derivable from computed evidence."
"""

    @staticmethod
    def plot_spec(profile: dict[str, Any], goal: str) -> str:
        return f"""
You are a plotting planner.

Return ONLY valid JSON.

DATASET PROFILE:
{json.dumps(profile, ensure_ascii=False)[:22000]}

PLOT GOAL:
{goal}

Schema:
{{
  "kind": "line|bar|scatter",
  "x": "<col>",
  "y": "<col or null>",
  "color": "<col or null>",
  "agg": "mean|sum|count|null",
  "top_k": <int or null>,
  "title": "<string or null>",
  "x_label": "<string or null>",
  "y_label": "<string or null>"
}}

Rules:
- Use existing columns only.
- For categorical bars, top_k should usually be 10.
- For large trends, prefer aggregated line chart.
- Prefer business-relevant views such as concentration, trend, customer value, or return hotspots.
"""

    @staticmethod
    def caption(goal: str, spec: dict[str, Any], plot_table: pd.DataFrame) -> str:
        return f"""
Write a grounded plot caption.

GOAL:
{goal}

SPEC:
{json.dumps(spec, ensure_ascii=False)}

PLOT TABLE CSV:
{plot_table.head(120).to_csv(index=False)}

Rules:
- Bullet points only (4 to 6 lines).
- Mention concrete observed patterns only.
- Include ranks, peaks, troughs, concentration, or percentage change when directly visible.
- No generic commentary.
"""
