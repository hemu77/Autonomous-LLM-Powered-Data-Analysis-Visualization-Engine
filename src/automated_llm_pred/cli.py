from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from automated_llm_pred.config import PipelineConfig
from automated_llm_pred.data import DataIngestor, fetch_uci_online_retail, prepare_online_retail_business_view
from automated_llm_pred.pipeline import run_case_study


def _load_questions(path: str | None) -> list[str]:
    if not path:
        return []
    content = Path(path).read_text(encoding="utf-8").strip()
    if not content:
        return []
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
    except Exception:
        pass
    return [line.strip() for line in content.splitlines() if line.strip()]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run recruiter-grade analytics case study.")
    parser.add_argument("--dataset-source", choices=["uci_online_retail", "local"], default="uci_online_retail")
    parser.add_argument("--dataset-path", default="", help="Used when --dataset-source=local")
    parser.add_argument("--cache-dir", default=".cache")
    parser.add_argument("--out-dir", default="report_output_v2")
    parser.add_argument("--title", default="Automated Business Analytics Case Study (LLM + Deterministic Execution)")
    parser.add_argument("--questions-file", default="")
    parser.add_argument("--plot-goals-file", default="")
    parser.add_argument("--prefer-openai-primary", action="store_true")
    parser.add_argument("--allow-empty-input", action="store_true", help="Do not auto-fill default questions/goals.")
    return parser


def load_dataset(args: argparse.Namespace) -> pd.DataFrame:
    if args.dataset_source == "uci_online_retail":
        raw = fetch_uci_online_retail(cache_dir=args.cache_dir)
        return prepare_online_retail_business_view(raw)
    if not args.dataset_path.strip():
        raise ValueError("--dataset-path is required when --dataset-source=local")
    return DataIngestor.load(args.dataset_path.strip())


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    df = load_dataset(args)
    questions = _load_questions(args.questions_file)
    plot_goals = _load_questions(args.plot_goals_file)

    paths = run_case_study(
        df=df,
        out_dir=args.out_dir,
        title=args.title,
        questions=questions,
        plot_goals=plot_goals,
        cfg=PipelineConfig(prefer_openai_primary=args.prefer_openai_primary),
        use_defaults_when_empty=not args.allow_empty_input,
    )
    print("Generated artifacts:")
    for key, value in paths.items():
        print(f"- {key}: {Path(value).resolve()}")


if __name__ == "__main__":
    main()
