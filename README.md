# Autonomous LLM-Powered Data Analysis and Visualization Engine

This project is a notebook-first analytics system that turns a messy business dataset into a recruiter-ready case study.

At a high level, it does three things well:
- profiles and cleans a real retail dataset instead of a toy demo
- uses multiple LLMs and routes work to the model that fits the task best
- keeps the final answers grounded in deterministic tables, plots, and validation checks

The result is not just "ask a model about a CSV." It is a guarded pipeline that plans, computes, critiques, visualizes, and exports a polished analytics report.

## What Makes It Different

Most LLM data demos stop at a chatbot layer. This pipeline goes further.

- It starts with reproducible data ingestion and business-focused preprocessing.
- It lets a user type custom analysis questions and visualization goals.
- It chooses different language models depending on whether the task is routine or more complex.
- It validates plans before execution so weak or invalid requests do not silently produce nonsense.
- It backs the final narrative with deterministic evidence and benchmark checks.
- It exports a full HTML/PDF case study instead of leaving results scattered across notebook cells.

## How The Pipeline Works

1. Dataset ingestion
   The pipeline loads the UCI Online Retail dataset and normalizes types carefully so IDs do not get mistaken for dates or numeric measures.

2. Business preprocessing
   It flags cancellations and returns, computes revenue-level fields, derives date features, and prepares the dataset for customer, country, and time-based analysis.

3. Profiling
   Before asking any model to plan work, the system builds a structured profile of the data: column roles, cardinality, missingness, likely measures, likely dimensions, and preview statistics.

4. LLM planning and routing
   A router decides which model should handle the task. Simpler requests can go through the standard model path, while more complex planning and critique requests can go through the stronger model path.

5. Deterministic execution
   The selected plan is validated, then executed with pandas-based logic so tables and plot data come from code, not from model imagination.

6. Guarded narration and reporting
   The model drafts the explanation, a critic pass checks it against evidence, deterministic insight builders strengthen weak bullets, and the final outputs are exported as a report bundle.

## Hybrid LLM Routing

This project does not rely on one model for everything.

It uses a hybrid routing setup where the pipeline picks the best available path based on task complexity and environment configuration.

- Standard analysis tasks use a lighter default route.
- Plot-spec generation uses a model tuned well enough for structured visualization instructions.
- Complex requests and critic passes can be routed to OpenAI.
- If one provider is unavailable, the system can fall back to the other instead of collapsing.

In code, this behavior lives in the router and config layer under `src/automated_llm_pred/config.py` and `src/automated_llm_pred/routing.py`.

## Models In The Current Configuration

These are the models currently wired into the default routing policy.

| Role | Default model | Why it is used |
| --- | --- | --- |
| Standard analysis | `phi-4` | Handles routine planning and table-oriented reasoning with low temperature for stable outputs. |
| Standard plot generation | `Llama-3.3-70B-Instruct-quantized` | Generates structured plot specifications for business visuals in the standard route. |
| Standard critic | `phi-4` | Performs a lightweight consistency pass when the standard path is used. |
| Complex analysis | `openai/gpt-4o-mini` | Used for harder prompts, broader reasoning, and stronger narrative synthesis. |
| Complex critic | `openai/gpt-4o-mini` | Used when the pipeline wants a stronger evidence-aware review pass. |
| Complex plot fallback | `openai/gpt-4o-mini` | Acts as the stronger fallback path when plot instructions are more demanding. |

The standard model pool is configurable and the project also supports additional CyVerse-accessible models through the routing config, including families such as Qwen, Gemma, Llama, GPT-OSS, and Phi variants.

## What A User Can Do

The upgraded notebook keeps the interactive feel of the original workflow.

A user can:
- type analysis questions about the dataset
- type visualization goals directly in the notebook flow
- leave the prompts blank and let the system run a stronger default case-study path
- generate a report bundle with tables, plots, an executive summary, a technical appendix, and benchmark output

The original notebook is preserved as a baseline artifact.
The upgraded notebook is:
- `analytics_automation_llm_with_reporting_interactive_v2_case_study.ipynb`

## Project Structure

- `src/automated_llm_pred/`
  Core package code for ingestion, routing, deterministic analysis, plotting, guardrails, reporting, and evaluation.
- `tests/`
  Unit and integration checks for preprocessing, execution, insights, and pipeline behavior.
- `report_output_v2/`
  Generated business case-study artifacts, plots, summary files, and benchmark output.
- `analytics_automation_llm_with_reporting_interactive.ipynb`
  Original notebook kept as the untouched baseline.
- `analytics_automation_llm_with_reporting_interactive_v2_case_study.ipynb`
  Upgraded notebook with stronger dataset, routing, reporting, and interactive question flow.

## Output Bundle

The generated report bundle includes:
- HTML report
- PDF report
- executive summary
- technical appendix
- benchmark report
- saved visualization assets

This makes the project easier to review like a real analytics deliverable rather than a one-off experiment.

## Credentials And Reproducibility

API keys are not stored in this repository.

To run the full hybrid pipeline on another machine, a user needs their own environment variables and provider access. That is intentional. This repo is meant to show architecture, code quality, and outputs without exposing private credentials.

## License

This repository is published with an all-rights-reserved license.
Viewing for evaluation is allowed.
Copying, redistribution, and reuse are not granted.
