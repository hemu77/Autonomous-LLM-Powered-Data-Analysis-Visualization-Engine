from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

SortDir = Literal["asc", "desc"]


@dataclass
class AnalysisPlan:
    target: str | None = None
    filters: list[dict[str, Any]] = field(default_factory=list)
    groupby: list[str] = field(default_factory=list)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    sort_by: str | None = None
    sort_dir: SortDir = "desc"
    limit: int = 20

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> "AnalysisPlan":
        return AnalysisPlan(
            target=payload.get("target"),
            filters=payload.get("filters", []) or [],
            groupby=payload.get("groupby", []) or [],
            metrics=payload.get("metrics", []) or [],
            sort_by=payload.get("sort_by"),
            sort_dir=payload.get("sort_dir", "desc"),
            limit=int(payload.get("limit", 20) or 20),
        )


class PlanValidator:
    @staticmethod
    def validate(plan: AnalysisPlan, df: pd.DataFrame) -> tuple[bool, list[str]]:
        errors: list[str] = []
        columns = set(df.columns)

        if plan.target and plan.target not in columns:
            errors.append(f"target column not found: {plan.target}")

        for filt in plan.filters:
            col = filt.get("col")
            op = filt.get("op")
            if col not in columns:
                errors.append(f"filter col not found: {col}")
            if op not in {"==", "!=", ">", ">=", "<", "<=", "in", "contains", "notnull", "isnull"}:
                errors.append(f"unsupported filter op: {op}")

        for group_col in plan.groupby:
            if group_col not in columns:
                errors.append(f"groupby col not found: {group_col}")

        for metric in plan.metrics:
            col = metric.get("col")
            agg = metric.get("agg")
            if col and col not in columns:
                errors.append(f"metric col not found: {col}")
            if agg not in {"count", "nunique", "mean", "sum", "min", "max", "median"}:
                errors.append(f"unsupported agg: {agg}")

        if plan.sort_dir not in {"asc", "desc"}:
            errors.append("sort_dir must be asc or desc")
        if plan.limit < 1 or plan.limit > 500:
            errors.append("limit must be 1..500")

        return len(errors) == 0, errors


def _reduce(series: pd.Series, agg: str) -> Any:
    non_null = series.dropna()
    if agg == "count":
        return int(series.notna().sum())
    if agg == "nunique":
        return int(series.nunique(dropna=True))
    if non_null.empty:
        return None
    if agg == "mean":
        return float(non_null.mean())
    if agg == "sum":
        return float(non_null.sum())
    if agg == "min":
        return float(non_null.min()) if pd.api.types.is_numeric_dtype(non_null) else non_null.min()
    if agg == "max":
        return float(non_null.max()) if pd.api.types.is_numeric_dtype(non_null) else non_null.max()
    if agg == "median":
        return float(non_null.median()) if pd.api.types.is_numeric_dtype(non_null) else None
    return None


class AnalysisExecutor:
    @staticmethod
    def execute(df: pd.DataFrame, plan: AnalysisPlan) -> pd.DataFrame:
        out = df.copy()

        for filt in plan.filters:
            col = filt["col"]
            op = filt["op"]
            value = filt.get("value")
            if op == "notnull":
                out = out[out[col].notna()]
            elif op == "isnull":
                out = out[out[col].isna()]
            elif op == "contains":
                out = out[out[col].astype(str).str.contains(str(value), na=False)]
            elif op == "in":
                values = value if isinstance(value, list) else [value]
                out = out[out[col].isin(values)]
            elif op == "==":
                out = out[out[col] == value]
            elif op == "!=":
                out = out[out[col] != value]
            elif op == ">":
                out = out[out[col] > value]
            elif op == ">=":
                out = out[out[col] >= value]
            elif op == "<":
                out = out[out[col] < value]
            elif op == "<=":
                out = out[out[col] <= value]

        if not plan.groupby and not plan.metrics:
            return out.head(plan.limit).reset_index(drop=True)

        grouped = out.groupby(plan.groupby, dropna=False) if plan.groupby else None
        agg_dict: dict[str, list[str]] = {}

        for metric in plan.metrics:
            col = metric.get("col")
            agg = metric.get("agg")
            if agg == "count" and (col is None or col == ""):
                continue
            agg_dict.setdefault(col, []).append(agg)

        if grouped is not None:
            if agg_dict:
                result = grouped.agg(agg_dict)
                result.columns = ["_".join([str(x) for x in tup if x]) for tup in result.columns.to_flat_index()]
                result = result.reset_index()
            else:
                result = grouped.size().reset_index(name="count_rows")
        else:
            row: dict[str, Any] = {}
            for metric in plan.metrics:
                col = metric.get("col")
                agg = metric.get("agg")
                alias = metric.get("as") or f"{agg}_{col or 'rows'}"
                if agg == "count" and (col is None or col == ""):
                    row[alias] = int(len(out))
                else:
                    row[alias] = _reduce(out[col], agg)
            result = pd.DataFrame([row])

        if plan.sort_by and plan.sort_by in result.columns:
            result = result.sort_values(plan.sort_by, ascending=(plan.sort_dir == "asc"))
        return result.head(plan.limit).reset_index(drop=True)
