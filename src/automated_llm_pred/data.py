from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Any

import pandas as pd

UCI_ONLINE_RETAIL_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"


class DataIngestor:
    @staticmethod
    def load(path: str) -> pd.DataFrame:
        source = (path or "").strip()
        if not source:
            raise ValueError("Path must be non-empty.")

        lower = source.lower()
        if lower.endswith(".csv"):
            df = pd.read_csv(source)
        elif lower.endswith(".json") or lower.endswith(".jsonl"):
            df = pd.read_json(source, lines=lower.endswith(".jsonl"))
        elif lower.endswith(".parquet"):
            df = pd.read_parquet(source)
        elif lower.endswith(".xlsx") or lower.endswith(".xls"):
            df = pd.read_excel(source)
        else:
            df = pd.read_csv(source)
        return DataNormalizer.normalize(df)

    @staticmethod
    def from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        return DataNormalizer.normalize(df)


class DataNormalizer:
    DATE_HINT_TOKENS = ("date", "time", "month", "year", "ym")
    NON_DATE_IDENTIFIER_TOKENS = ("id", "code", "invoice")

    @staticmethod
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a DataFrame")

        normalized = df.copy()
        normalized.columns = [DataNormalizer._clean_col(col) for col in normalized.columns]
        normalized = DataNormalizer._flatten_object_columns(normalized)
        normalized = DataNormalizer._coerce_dates(normalized)
        normalized = DataNormalizer._coerce_numeric(normalized)
        normalized = normalized.dropna(how="all")
        return normalized

    @staticmethod
    def _clean_col(name: Any) -> str:
        out = str(name).strip()
        out = re.sub(r"\s+", "_", out)
        out = re.sub(r"[^0-9a-zA-Z_]+", "", out)
        out = re.sub(r"_+", "_", out)
        return out.strip("_")

    @staticmethod
    def _flatten_object_columns(df: pd.DataFrame) -> pd.DataFrame:
        flat = df.copy()
        object_cols = flat.select_dtypes(include=["object"]).columns.tolist()
        for col in object_cols:
            non_null = flat[col].dropna()
            if non_null.empty:
                continue
            sample = non_null.iloc[0]
            if not isinstance(sample, dict):
                continue
            expanded = flat[col].apply(lambda x: x if isinstance(x, dict) else {})
            expanded_df = pd.json_normalize(expanded)
            expanded_df.columns = [DataNormalizer._clean_col(f"{col}_{c}") for c in expanded_df.columns]
            flat = flat.drop(columns=[col]).reset_index(drop=True)
            flat = pd.concat([flat, expanded_df.reset_index(drop=True)], axis=1)
        return flat

    @staticmethod
    def _coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for col in out.columns:
            if out[col].dtype != "object":
                continue
            lowered = col.lower()
            # Treat identifiers like invoice IDs and product codes as IDs first, not timestamps.
            if any(token in lowered for token in DataNormalizer.NON_DATE_IDENTIFIER_TOKENS) and not any(
                token in lowered for token in DataNormalizer.DATE_HINT_TOKENS
            ):
                continue
            sample_strings = out[col].dropna().astype(str).head(25).tolist()
            if sample_strings and not any(
                any(marker in sample for marker in ("-", "/", ":", " "))
                for sample in sample_strings
            ) and not any(token in lowered for token in DataNormalizer.DATE_HINT_TOKENS):
                continue
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="Could not infer format",
                    category=UserWarning,
                )
                parsed = pd.to_datetime(out[col], errors="coerce")
            if parsed.notna().sum() >= max(10, int(0.25 * len(out))):
                out[col] = parsed
        return out

    @staticmethod
    def _coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for col in out.columns:
            if out[col].dtype != "object":
                continue
            lowered = col.lower()
            if any(token in lowered for token in DataNormalizer.NON_DATE_IDENTIFIER_TOKENS):
                continue
            maybe = pd.to_numeric(out[col], errors="coerce")
            if maybe.notna().sum() >= max(10, int(0.35 * len(out))):
                out[col] = maybe
        return out


def fetch_uci_online_retail(cache_dir: str = ".cache") -> pd.DataFrame:
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    target = cache_path / "online_retail.xlsx"
    if not target.exists():
        # Keep a local cached copy so repeated case-study runs do not keep hitting the source.
        frame = pd.read_excel(UCI_ONLINE_RETAIL_URL)
        frame.to_excel(target, index=False)
    return pd.read_excel(target)


def prepare_online_retail_business_view(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df.columns = [DataNormalizer._clean_col(col) for col in df.columns]

    required_cols = {"InvoiceNo", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"}
    if not required_cols.issubset(set(df.columns)):
        missing = sorted(required_cols.difference(set(df.columns)))
        raise ValueError(f"UCI Online Retail expected columns missing: {missing}")

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = df["CustomerID"].astype("string")

    df = df.dropna(subset=["InvoiceDate", "Quantity", "UnitPrice", "Country"])
    df = df[df["UnitPrice"] >= 0]

    # These derived fields are the ones the analytics/reporting layers actually reason over.
    df["invoice_no"] = df["InvoiceNo"].astype(str)
    df["is_cancellation"] = df["invoice_no"].str.startswith("C")
    df["is_return"] = (df["Quantity"] < 0) | df["is_cancellation"]
    df["line_total"] = df["Quantity"] * df["UnitPrice"]
    df["abs_line_total"] = df["line_total"].abs()
    df["net_revenue"] = df["line_total"]
    df["invoice_year"] = df["InvoiceDate"].dt.year
    df["invoice_month"] = df["InvoiceDate"].dt.month
    df["invoice_ym"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    df = df.drop(columns=["InvoiceNo"])

    df = df.rename(
        columns={
            "InvoiceDate": "invoice_date",
            "Quantity": "quantity",
            "UnitPrice": "unit_price",
            "CustomerID": "customer_id",
            "Country": "country",
            "StockCode": "stock_code",
            "Description": "description",
        }
    )

    valid_customers = df["customer_id"].notna() & (df["customer_id"].str.strip() != "")
    df["has_customer"] = valid_customers
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")

    # First purchase is used to support customer-level lifecycle views later in the pipeline.
    first_purchase = (
        df[df["has_customer"]]
        .groupby("customer_id", dropna=False)["invoice_date"]
        .min()
        .rename("first_purchase_date")
        .reset_index()
    )
    df = df.merge(first_purchase, on="customer_id", how="left")
    df["days_since_first_purchase"] = (
        (df["invoice_date"] - df["first_purchase_date"]).dt.total_seconds() / 86400
    ).fillna(0)
    return DataNormalizer.normalize(df)


def build_rfm_table(df: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    required = {"customer_id", "invoice_date", "net_revenue", "invoice_no", "has_customer"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns for RFM: {sorted(missing)}")

    ref = reference_date or pd.to_datetime(df["invoice_date"]).max()
    customer_df = df[df["has_customer"]].copy()
    agg = (
        customer_df.groupby("customer_id", dropna=False)
        .agg(
            recency_days=("invoice_date", lambda s: int((ref - pd.to_datetime(s).max()).days)),
            frequency=("invoice_no", "nunique"),
            monetary=("net_revenue", "sum"),
        )
        .reset_index()
    )
    agg["rfm_segment"] = (
        pd.qcut(agg["recency_days"].rank(method="first"), 4, labels=["A", "B", "C", "D"]).astype(str)
        + "-"
        + pd.qcut(agg["frequency"].rank(method="first"), 4, labels=["D", "C", "B", "A"]).astype(str)
        + "-"
        + pd.qcut(agg["monetary"].rank(method="first"), 4, labels=["D", "C", "B", "A"]).astype(str)
    )
    return agg.sort_values("monetary", ascending=False).reset_index(drop=True)
