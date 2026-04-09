# Autonomous LLM-Powered Data Analysis and Visualization Engine

Portfolio version of a deterministic analytics engine that combines:

- dataset normalization and business feature engineering
- LLM-assisted planning and narration
- deterministic table computation and guarded plot generation
- HTML/PDF case-study export with benchmark checks

## What This Repo Shows

- A notebook-first workflow for interactive analysis
- A modular Python implementation under `src/automated_llm_pred`
- A recruiter-facing business analytics case study built on the UCI Online Retail dataset
- Generated artifacts in `report_output_v2/`

## Repository Notes

- The original notebook is preserved as a baseline artifact.
- The upgraded notebook is `analytics_automation_llm_with_reporting_interactive_v2_case_study.ipynb`.
- API credentials are not stored in this repository.
- Reproduction requires valid third-party model credentials and environment setup.

## Project Structure

- `src/automated_llm_pred/`: package code for ingestion, routing, analysis, plotting, insights, reporting, and CLI
- `tests/`: unit and integration checks
- `report_output_v2/`: generated case-study artifacts and plots

## Reproducibility

This repository intentionally excludes live credentials and local cache state. To run the full pipeline on another machine, a user must supply their own API access and environment configuration.

## License

This repository is published with an all-rights-reserved license. Viewing for portfolio evaluation is allowed; copying, redistribution, and reuse are not granted.
