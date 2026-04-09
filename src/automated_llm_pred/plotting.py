from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_col,
    geom_line,
    geom_point,
    ggplot,
    labs,
    theme,
    theme_minimal,
)

PlotKind = Literal["line", "bar", "scatter"]


@dataclass
class PlotSpec:
    kind: PlotKind
    x: str
    y: str | None = None
    color: str | None = None
    agg: str | None = None
    top_k: int | None = None
    title: str | None = None
    x_label: str | None = None
    y_label: str | None = None

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> "PlotSpec":
        return PlotSpec(
            kind=payload["kind"],
            x=payload["x"],
            y=payload.get("y"),
            color=payload.get("color"),
            agg=payload.get("agg"),
            top_k=payload.get("top_k"),
            title=payload.get("title"),
            x_label=payload.get("x_label"),
            y_label=payload.get("y_label"),
        )


class PlotValidator:
    @staticmethod
    def validate(spec: PlotSpec, df: pd.DataFrame) -> tuple[bool, list[str]]:
        errors: list[str] = []
        columns = set(df.columns)
        if spec.kind not in {"line", "bar", "scatter"}:
            errors.append(f"unsupported plot kind: {spec.kind}")
        if spec.x not in columns:
            errors.append(f"x column not found: {spec.x}")
        if spec.kind in {"line", "scatter"} and (not spec.y or spec.y not in columns):
            errors.append(f"y column not found: {spec.y}")
        if spec.color and spec.color not in columns:
            errors.append(f"color column not found: {spec.color}")
        if spec.agg and spec.agg not in {"mean", "sum", "count"}:
            errors.append(f"unsupported agg: {spec.agg}")
        if spec.top_k is not None and (spec.top_k < 1 or spec.top_k > 100):
            errors.append("top_k must be 1..100")
        return len(errors) == 0, errors


class PlotRenderer:
    @staticmethod
    def _base_theme() -> Any:
        return theme_minimal() + theme(
            figure_size=(11.5, 6.5),
            panel_background=element_rect(fill="#f8fafc", color=None),
            plot_background=element_rect(fill="#ffffff", color=None),
            panel_grid_major_x=element_line(color="#e2e8f0", size=0.4),
            panel_grid_major_y=element_line(color="#cbd5e1", size=0.4),
            axis_text_x=element_text(rotation=28, ha="right", color="#334155", size=9),
            axis_text_y=element_text(color="#334155", size=9),
            axis_title=element_text(color="#0f172a", size=10),
            plot_title=element_text(color="#0f172a", weight="bold", size=15),
            legend_title=element_text(color="#0f172a", size=10),
            legend_text=element_text(color="#334155", size=9),
        )

    @staticmethod
    def _should_flip_categories(plot_df: pd.DataFrame, x_col: str, top_k: int | None) -> bool:
        if x_col not in plot_df.columns:
            return False
        labels = plot_df[x_col].astype(str)
        return bool(top_k) or labels.str.len().max() > 10 or plot_df[x_col].nunique() > 8

    @staticmethod
    def render(df: pd.DataFrame, spec: PlotSpec, max_rows: int = 20000) -> tuple[Any, pd.DataFrame]:
        plot_df = PlotRenderer._build_plot_table(df, spec)
        if len(plot_df) > max_rows:
            plot_df = plot_df.head(max_rows).copy()

        title = spec.title or "Auto-generated plot"
        xlab = spec.x_label or spec.x
        ylab = spec.y_label or (spec.y if spec.y else "value")

        if spec.kind == "line":
            mapping = aes(x=spec.x, y=spec.y, color=spec.color) if spec.color else aes(x=spec.x, y=spec.y, group=1)
            plot = (
                ggplot(plot_df, mapping)
                + geom_line(size=1.2, color=None if spec.color else "#0f766e")
                + geom_point(size=2.6, color=None if spec.color else "#0f766e")
                + labs(title=title, x=xlab, y=ylab)
                + PlotRenderer._base_theme()
            )
        elif spec.kind == "scatter":
            mapping = aes(x=spec.x, y=spec.y, color=spec.color) if spec.color else aes(x=spec.x, y=spec.y)
            plot = (
                ggplot(plot_df, mapping)
                + geom_point(size=2.2, alpha=0.68, color=None if spec.color else "#0f766e")
                + labs(title=title, x=xlab, y=ylab)
                + PlotRenderer._base_theme()
            )
        elif spec.y:
            plot = (
                ggplot(plot_df, aes(x=spec.x, y=spec.y))
                + geom_col(fill="#0f766e")
                + labs(title=title, x=xlab, y=ylab)
                + PlotRenderer._base_theme()
            )
            if PlotRenderer._should_flip_categories(plot_df, spec.x, spec.top_k):
                plot = plot + coord_flip()
        else:
            plot = (
                ggplot(plot_df, aes(x=spec.x))
                + geom_bar(fill="#0f766e")
                + labs(title=title, x=xlab, y="count")
                + PlotRenderer._base_theme()
            )
            if PlotRenderer._should_flip_categories(plot_df, spec.x, spec.top_k):
                plot = plot + coord_flip()
        return plot, plot_df

    @staticmethod
    def _build_plot_table(df: pd.DataFrame, spec: PlotSpec) -> pd.DataFrame:
        d = df.copy()
        x_col = spec.x
        if pd.api.types.is_datetime64_any_dtype(d[x_col]):
            d[f"{spec.x}_month"] = d[x_col].dt.to_period("M").astype(str)
            x_col = f"{spec.x}_month"

        if spec.kind in {"line", "scatter"}:
            cols = [x_col, spec.y] + ([spec.color] if spec.color else [])
            dd = d[cols].dropna()
            if spec.agg in {"mean", "sum", "count"}:
                group_cols = [x_col] + ([spec.color] if spec.color else [])
                if spec.agg == "count":
                    out = dd.groupby(group_cols, dropna=False).size().reset_index(name=spec.y)
                else:
                    out = dd.groupby(group_cols, dropna=False)[spec.y].agg(spec.agg).reset_index()
                out = out.rename(columns={x_col: spec.x})
                return out.sort_values(spec.x).reset_index(drop=True)
            dd = dd.rename(columns={x_col: spec.x})
            return dd.sort_values(spec.x).reset_index(drop=True)

        if spec.y and spec.agg in {"mean", "sum", "count"}:
            dd = d[[x_col, spec.y]].dropna()
            if spec.agg == "count":
                out = dd.groupby(x_col, dropna=False).size().reset_index(name=spec.y)
            else:
                out = dd.groupby(x_col, dropna=False)[spec.y].agg(spec.agg).reset_index()
            out = out.rename(columns={x_col: spec.x})
        else:
            out = d[[x_col]].dropna().rename(columns={x_col: spec.x})
            out = out.groupby(spec.x, dropna=False).size().reset_index(name="count")

        if spec.top_k:
            sort_col = spec.y if spec.y else "count"
            if sort_col in out.columns:
                out = out.sort_values(sort_col, ascending=False).head(spec.top_k)
        elif spec.kind == "bar":
            sort_col = spec.y if spec.y and spec.y in out.columns else "count"
            if sort_col in out.columns:
                out = out.sort_values(sort_col, ascending=False)
        return out.reset_index(drop=True)
