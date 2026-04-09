# Technical Appendix

## Pipeline Configuration
```json
{
  "cyverse_api_base": "https://llm-api.cyverse.ai/v1",
  "cyverse_api_key_env": "CYVERSE_API_KEY",
  "openai_api_base": "https://api.openai.com/v1",
  "openai_api_key_env": "OPENAI_API_KEY",
  "routing": {
    "standard_analysis": "phi-4",
    "standard_plot": "Llama-3.3-70B-Instruct-quantized",
    "standard_critic": "phi-4",
    "complex_analysis": "openai/gpt-4o-mini",
    "complex_critic": "openai/gpt-4o-mini"
  },
  "temperature_standard": 0.0,
  "temperature_complex": 0.0,
  "prefer_openai_primary": true,
  "max_unique_cats_preview": 12,
  "max_rows_for_plot_table": 20000,
  "strict_hallucination_guard": true
}
```

## Benchmark Summary
```json
{
  "pass_rate": 1.0,
  "passed": 3,
  "total": 3,
  "cases": [
    {
      "name": "country_revenue",
      "pass": true,
      "rows": 10,
      "columns": [
        "country",
        "net_revenue_sum"
      ]
    },
    {
      "name": "monthly_revenue",
      "pass": true,
      "rows": 13,
      "columns": [
        "invoice_ym",
        "net_revenue_sum"
      ]
    },
    {
      "name": "return_rate",
      "pass": true,
      "rows": 2,
      "columns": [
        "is_return",
        "count_rows"
      ]
    }
  ]
}
```

## Guardrails
- Deterministic execution for all computed tables.
- JSON schema validation for analysis and plot plans.
- Critic pass enabled for factuality verification.
- Narrative bullets should be grounded in computed evidence.
