from __future__ import annotations

from typing import Any

import pandas as pd


GENERIC_PHRASES = (
    "grounded against computed evidence",
    "computed summary generated",
    "plot insights generated",
    "not derivable from computed evidence",
)


def _is_time_like(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("date", "month", "year", "time", "ym"))


def _format_value(value: Any, label: str = "") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    try:
        numeric = float(value)
    except Exception:
        return str(value)

    lowered = label.lower()
    if any(token in lowered for token in ("rate", "share", "pct", "percentage")) or (
        lowered.startswith("is_") and lowered.endswith("_mean")
    ):
        return f"{numeric * 100:.1f}%"
    if abs(numeric) >= 1000000:
        return f"{numeric / 1000000:.2f}M"
    if abs(numeric) >= 1000:
        return f"{numeric:,.0f}"
    if numeric.is_integer():
        return f"{int(numeric)}"
    return f"{numeric:.2f}"


def _clean_candidate_bullets(bullets: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for bullet in bullets:
        text = (bullet or "").strip()
        if not text:
            continue
        lowered = text.lower()
        if any(phrase in lowered for phrase in GENERIC_PHRASES):
            continue
        if lowered in seen:
            continue
        seen.add(lowered)
        cleaned.append(text)
    return cleaned


def _humanize_label(label: str) -> str:
    lowered = label.lower()
    replacements = {
        "invoice_no_nunique": "order count",
        "net_revenue_sum": "net revenue",
        "is_return_sum": "return count",
        "is_cancellation_sum": "cancellation count",
        "is_return_mean": "return rate",
        "is_cancellation_mean": "cancellation rate",
        "invoice_no_count": "order count",
    }
    if lowered in replacements:
        return replacements[lowered]
    if lowered.endswith("_sum"):
        lowered = lowered[: -len("_sum")]
    if lowered.endswith("_nunique"):
        lowered = lowered[: -len("_nunique")]
    return lowered.replace("_", " ")


def _pick_primary_metric(numeric_cols: list[str]) -> str:
    # Prefer business-facing metrics over raw technical columns when we summarize a table.
    priorities = (
        "net_revenue",
        "return_rate",
        "cancellation_rate",
        "revenue",
        "amount",
        "value",
        "count",
    )
    lowered_map = {col.lower(): col for col in numeric_cols}
    for priority in priorities:
        for lowered, original in lowered_map.items():
            if priority in lowered:
                return original
    return numeric_cols[0]


def build_table_insights(question: str, result: pd.DataFrame, max_bullets: int = 5) -> list[str]:
    if result is None or result.empty:
        return ["Not derivable from computed evidence."]

    working = result.copy()
    # Some tables carry counts only; derive rates here so the narrative can talk in analyst language.
    if {"is_return_sum", "invoice_no_nunique"}.issubset(working.columns):
        working["return_rate"] = working["is_return_sum"] / working["invoice_no_nunique"].replace(0, pd.NA)
    if {"is_cancellation_sum", "invoice_no_nunique"}.issubset(working.columns):
        working["cancellation_rate"] = working["is_cancellation_sum"] / working["invoice_no_nunique"].replace(0, pd.NA)

    numeric_cols = working.select_dtypes(include=["number"]).columns.tolist()
    if not numeric_cols:
        return [f"Returned {len(working)} rows for '{question}'."]

    dim_cols = [col for col in working.columns if col not in numeric_cols]
    primary_metric = _pick_primary_metric(numeric_cols)
    primary_dim = dim_cols[0] if dim_cols else working.columns[0]
    bullets: list[str] = []

    if _is_time_like(primary_dim):
        ordered = working.copy()
        try:
            ordered["_sort"] = pd.to_datetime(ordered[primary_dim], errors="coerce")
            if ordered["_sort"].notna().any():
                ordered = ordered.sort_values("_sort")
            else:
                ordered = ordered.sort_values(primary_dim)
        except Exception:
            ordered = ordered.sort_values(primary_dim)

        first = ordered.iloc[0]
        last = ordered.iloc[-1]
        peak = ordered.loc[ordered[primary_metric].idxmax()]
        trough = ordered.loc[ordered[primary_metric].idxmin()]
        bullets.append(
            f"{_humanize_label(primary_metric).title()} peaks in {peak[primary_dim]} at {_format_value(peak[primary_metric], primary_metric)}."
        )
        bullets.append(
            f"The lowest point is {trough[primary_dim]} at {_format_value(trough[primary_metric], primary_metric)}."
        )
        try:
            change = float(last[primary_metric]) - float(first[primary_metric])
            pct = (change / float(first[primary_metric])) if float(first[primary_metric]) else 0.0
            direction = "up" if change >= 0 else "down"
            bullets.append(
                f"From {first[primary_dim]} to {last[primary_dim]}, the metric moves {direction} by {_format_value(abs(change), primary_metric)} ({pct * 100:.1f}%)."
            )
        except Exception:
            pass
    else:
        ordered = working.sort_values(primary_metric, ascending=False).reset_index(drop=True)
        leader = ordered.iloc[0]
        bullets.append(
            f"{leader[primary_dim]} leads on {_humanize_label(primary_metric)} at {_format_value(leader[primary_metric], primary_metric)}."
        )
        if len(ordered) > 1:
            runner_up = ordered.iloc[1]
            try:
                gap = float(leader[primary_metric]) - float(runner_up[primary_metric])
                bullets.append(
                    f"The gap from first to second place is {_format_value(gap, primary_metric)} versus {runner_up[primary_dim]}."
                )
            except Exception:
                pass
        positive_total = ordered[primary_metric].clip(lower=0).sum()
        if len(ordered) >= 5 and positive_total:
            top_five_share = ordered.head(5)[primary_metric].clip(lower=0).sum() / positive_total
            bullets.append(
                f"The top five entries account for {top_five_share * 100:.1f}% of the shown total, indicating concentration."
            )
        elif len(ordered) >= 3 and positive_total:
            top_three_share = ordered.head(3)[primary_metric].clip(lower=0).sum() / positive_total
            bullets.append(
                f"The top three entries account for {top_three_share * 100:.1f}% of the shown total, indicating concentration."
            )
        if len(ordered) > 1:
            tail = ordered.iloc[-1]
            bullets.append(
                f"The weakest shown entry is {tail[primary_dim]} at {_format_value(tail[primary_metric], primary_metric)}."
            )

    if len(numeric_cols) > 1:
        secondary_candidates = [col for col in numeric_cols if col != primary_metric]
        secondary_metric = _pick_primary_metric(secondary_candidates) if secondary_candidates else primary_metric
        top_secondary = working.loc[working[secondary_metric].idxmax()]
        bullets.append(
            f"{top_secondary[primary_dim]} is highest on {_humanize_label(secondary_metric)} at {_format_value(top_secondary[secondary_metric], secondary_metric)}."
        )

    if {"is_return_sum", "invoice_no_nunique"}.issubset(result.columns):
        overall_rate = result["is_return_sum"].sum() / result["invoice_no_nunique"].sum()
        bullets.append(f"Across the shown markets, the blended return rate is {_format_value(overall_rate, 'return_rate')}.")
    if {"is_cancellation_sum", "invoice_no_nunique"}.issubset(result.columns):
        overall_cancel_rate = result["is_cancellation_sum"].sum() / result["invoice_no_nunique"].sum()
        bullets.append(
            f"Across the shown markets, the blended cancellation rate is {_format_value(overall_cancel_rate, 'cancellation_rate')}."
        )

    return _clean_candidate_bullets(bullets)[:max_bullets]


def build_plot_insights(goal: str, plot_table: pd.DataFrame, max_bullets: int = 5) -> list[str]:
    working = plot_table.copy()
    for col in list(working.columns):
        if col.startswith("is_"):
            series = pd.to_numeric(working[col], errors="coerce")
            if series.notna().any() and series.min() >= 0 and series.max() <= 1:
                working = working.rename(columns={col: f"{col[3:]}_rate"})
    return build_table_insights(goal, working, max_bullets=max_bullets)


def strengthen_bullets(llm_bullets: list[str], fallback_bullets: list[str], min_count: int = 4) -> list[str]:
    merged = _clean_candidate_bullets(fallback_bullets)
    seen = {bullet.lower() for bullet in merged}
    for bullet in _clean_candidate_bullets(llm_bullets):
        if len(merged) >= max(min_count, len(_clean_candidate_bullets(fallback_bullets))):
            break
        if bullet.lower() not in seen:
            merged.append(bullet)
            seen.add(bullet.lower())
    if not merged:
        return ["Not derivable from computed evidence."]
    return merged
