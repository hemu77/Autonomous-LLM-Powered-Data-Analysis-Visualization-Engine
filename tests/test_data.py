import pandas as pd

from automated_llm_pred.data import prepare_online_retail_business_view


def test_prepare_online_retail_business_view_creates_business_columns():
    raw = pd.DataFrame(
        {
            "InvoiceNo": ["10001", "C10001", "10002"],
            "StockCode": ["A", "A", "B"],
            "Description": ["Item A", "Item A", "Item B"],
            "Quantity": [10, -2, 3],
            "InvoiceDate": ["2011-01-01 10:00:00", "2011-01-02 10:00:00", "2011-02-01 09:00:00"],
            "UnitPrice": [2.5, 2.5, 4.0],
            "CustomerID": [12345, 12345, 22222],
            "Country": ["United Kingdom", "United Kingdom", "France"],
        }
    )

    df = prepare_online_retail_business_view(raw)

    assert "net_revenue" in df.columns
    assert "is_return" in df.columns
    assert "invoice_ym" in df.columns
    assert "customer_id" in df.columns
    assert df["is_return"].sum() >= 1
