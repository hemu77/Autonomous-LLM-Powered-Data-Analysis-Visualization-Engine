from automated_llm_pred.insights import build_plot_insights, strengthen_bullets
import pandas as pd


def test_strengthen_bullets_replaces_generic_output():
    result = pd.DataFrame(
        {
            "country": ["UK", "France", "Germany"],
            "net_revenue_sum": [1000.0, 700.0, 200.0],
        }
    )
    bullets = strengthen_bullets(
        ["Grounded against computed evidence."],
        build_plot_insights("Revenue by country", result),
        min_count=4,
    )
    assert len(bullets) >= 3
    assert all("grounded against computed evidence" not in bullet.lower() for bullet in bullets)
