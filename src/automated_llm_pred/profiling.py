from __future__ import annotations

import math
from typing import Any

import pandas as pd


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    except Exception:
        return None


def _safe_str(value: Any) -> str | None:
    try:
        if value is None:
            return None
        return str(value)
    except Exception:
        return None


class DataProfiler:
    @staticmethod
    def profile(df: pd.DataFrame, max_unique_preview: int = 12) -> dict[str, Any]:
        if df.empty:
            return {"shape": [0, 0], "columns": [], "notes": ["empty dataframe"]}

        profile: dict[str, Any] = {"shape": [int(df.shape[0]), int(df.shape[1])], "columns": []}
        for col in df.columns:
            series = df[col]
            info: dict[str, Any] = {
                "name": col,
                "dtype": str(series.dtype),
                "missing": int(series.isna().sum()),
                "missing_pct": float(round(series.isna().mean() * 100, 3)),
                "unique": int(series.nunique(dropna=True)),
            }

            if pd.api.types.is_bool_dtype(series):
                vc = series.value_counts(dropna=False)
                info["top_values"] = [{"value": str(k), "count": int(v)} for k, v in vc.head(max_unique_preview).items()]
            elif pd.api.types.is_numeric_dtype(series):
                desc = series.describe(percentiles=[0.05, 0.5, 0.95])
                info["numeric"] = {
                    "min": _safe_float(desc.get("min")),
                    "p05": _safe_float(desc.get("5%")),
                    "median": _safe_float(desc.get("50%")),
                    "mean": _safe_float(desc.get("mean")),
                    "p95": _safe_float(desc.get("95%")),
                    "max": _safe_float(desc.get("max")),
                    "std": _safe_float(desc.get("std")),
                }
            elif pd.api.types.is_datetime64_any_dtype(series):
                info["datetime"] = {"min": _safe_str(series.min()), "max": _safe_str(series.max())}
            else:
                vc = series.dropna().astype(str).value_counts().head(max_unique_preview)
                info["top_values"] = [{"value": str(k), "count": int(v)} for k, v in vc.items()]

            profile["columns"].append(info)
        return profile
