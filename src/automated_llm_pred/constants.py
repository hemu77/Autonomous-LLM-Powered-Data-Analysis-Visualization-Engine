DEFAULT_QUESTIONS = [
    "Which countries generate the highest net revenue, and how concentrated is revenue among the top five markets?",
    "How do monthly net revenue and order count move over time, and where are the major peaks or slowdowns?",
    "Which customers drive the highest lifetime value, and how far ahead are they from the next tier?",
    "What share of activity is tied to returns or cancellations, and which markets look materially worse than baseline?",
    "Which products dominate revenue, and which items appear high-volume but lower-value?",
    "Where does the business show concentration risk across countries, customers, and products?",
]

DEFAULT_PLOT_GOALS = [
    "Bar chart of top 12 countries by net revenue with emphasis on concentration",
    "Line chart of monthly net revenue over time",
    "Bar chart of top 12 customers by net revenue",
    "Bar chart of countries with the highest return rate",
    "Bar chart of top 12 products by net revenue",
]

CURATED_ANALYSIS_PRESETS = {
    DEFAULT_QUESTIONS[0]: {
        "groupby": ["country"],
        "metrics": [{"col": "net_revenue", "agg": "sum", "as": "net_revenue"}],
        "sort_by": "net_revenue_sum",
        "sort_dir": "desc",
        "limit": 10,
    },
    DEFAULT_QUESTIONS[1]: {
        "groupby": ["invoice_ym"],
        "metrics": [
            {"col": "invoice_no", "agg": "nunique", "as": "order_count"},
            {"col": "net_revenue", "agg": "sum", "as": "net_revenue"},
        ],
        "sort_by": "invoice_ym",
        "sort_dir": "asc",
        "limit": 24,
    },
    DEFAULT_QUESTIONS[2]: {
        "filters": [
            {"col": "has_customer", "op": "==", "value": True},
            {"col": "customer_id", "op": "!=", "value": "UNKNOWN"},
        ],
        "groupby": ["customer_id"],
        "metrics": [{"col": "net_revenue", "agg": "sum", "as": "net_revenue"}],
        "sort_by": "net_revenue_sum",
        "sort_dir": "desc",
        "limit": 12,
    },
    DEFAULT_QUESTIONS[3]: {
        "groupby": ["country"],
        "metrics": [
            {"col": "is_return", "agg": "mean", "as": "return_rate"},
            {"col": "is_cancellation", "agg": "mean", "as": "cancellation_rate"},
            {"col": "invoice_no", "agg": "nunique", "as": "invoice_count"},
        ],
        "sort_by": "is_return_mean",
        "sort_dir": "desc",
        "limit": 12,
    },
    DEFAULT_QUESTIONS[4]: {
        "filters": [{"col": "description", "op": "notnull"}],
        "groupby": ["description"],
        "metrics": [
            {"col": "net_revenue", "agg": "sum", "as": "net_revenue"},
            {"col": "quantity", "agg": "sum", "as": "quantity"},
        ],
        "sort_by": "net_revenue_sum",
        "sort_dir": "desc",
        "limit": 12,
    },
    DEFAULT_QUESTIONS[5]: {
        "groupby": ["country"],
        "metrics": [
            {"col": "net_revenue", "agg": "sum", "as": "net_revenue"},
            {"col": "invoice_no", "agg": "nunique", "as": "invoice_count"},
            {"col": "customer_id", "agg": "nunique", "as": "customer_count"},
        ],
        "sort_by": "net_revenue_sum",
        "sort_dir": "desc",
        "limit": 12,
    },
}

CURATED_PLOT_PRESETS = {
    DEFAULT_PLOT_GOALS[0]: {
        "kind": "bar",
        "x": "country",
        "y": "net_revenue",
        "agg": "sum",
        "top_k": 12,
        "title": "Top Countries by Net Revenue",
        "x_label": "Country",
        "y_label": "Net Revenue",
    },
    DEFAULT_PLOT_GOALS[1]: {
        "kind": "line",
        "x": "invoice_ym",
        "y": "net_revenue",
        "agg": "sum",
        "top_k": None,
        "title": "Monthly Net Revenue",
        "x_label": "Month",
        "y_label": "Net Revenue",
    },
    DEFAULT_PLOT_GOALS[2]: {
        "kind": "bar",
        "x": "customer_id",
        "y": "net_revenue",
        "agg": "sum",
        "top_k": 12,
        "title": "Top Customers by Net Revenue",
        "x_label": "Customer",
        "y_label": "Net Revenue",
    },
    DEFAULT_PLOT_GOALS[3]: {
        "kind": "bar",
        "x": "country",
        "y": "is_return",
        "agg": "mean",
        "top_k": 12,
        "title": "Countries with Highest Return Rate",
        "x_label": "Country",
        "y_label": "Return Rate",
    },
    DEFAULT_PLOT_GOALS[4]: {
        "kind": "bar",
        "x": "description",
        "y": "net_revenue",
        "agg": "sum",
        "top_k": 12,
        "title": "Top Products by Net Revenue",
        "x_label": "Product",
        "y_label": "Net Revenue",
    },
}
