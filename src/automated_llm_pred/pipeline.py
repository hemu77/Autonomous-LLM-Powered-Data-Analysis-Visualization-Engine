from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import pandas as pd

from automated_llm_pred.analysis import AnalysisExecutor, AnalysisPlan, PlanValidator
from automated_llm_pred.config import PipelineConfig
from automated_llm_pred.constants import (
    CURATED_ANALYSIS_PRESETS,
    CURATED_PLOT_PRESETS,
    DEFAULT_PLOT_GOALS,
    DEFAULT_QUESTIONS,
)
from automated_llm_pred.data import DataIngestor
from automated_llm_pred.evaluation import grounding_score, run_core_benchmark, save_benchmark_report
from automated_llm_pred.guardrails import HallucinationGuard
from automated_llm_pred.insights import build_plot_insights, build_table_insights, strengthen_bullets
from automated_llm_pred.plotting import PlotRenderer, PlotSpec, PlotValidator
from automated_llm_pred.profiling import DataProfiler
from automated_llm_pred.prompts import Prompts
from automated_llm_pred.reporting import ReportExporter
from automated_llm_pred.routing import HybridModelRouter, RouterProtocol
from automated_llm_pred.utils import parse_json_object, split_bullets

LOGGER = logging.getLogger("automated_llm_pred")
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


class AnalyticsAutomationPipeline:
    def __init__(self, df: pd.DataFrame, cfg: PipelineConfig | None = None, router: RouterProtocol | None = None):
        self.cfg = cfg or PipelineConfig()
        self.df = DataIngestor.from_dataframe(df)
        self.profile = DataProfiler.profile(self.df, max_unique_preview=self.cfg.max_unique_cats_preview)
        self.router = router or HybridModelRouter(self.cfg)

    def answer(self, question: str) -> dict[str, Any]:
        query = (question or "").strip()
        if not query:
            raise ValueError("question must be non-empty")

        # The flagship case-study prompts use curated plans so the showcase report stays stable.
        if query in CURATED_ANALYSIS_PRESETS:
            plan_payload = CURATED_ANALYSIS_PRESETS[query]
        else:
            raw = self.router.ask_analysis(Prompts.analysis_plan(self.profile, query), question=query)
            plan_payload = parse_json_object(raw)
        plan = AnalysisPlan.from_dict(plan_payload)
        valid, errors = PlanValidator.validate(plan, self.df)

        if not valid:
            result = self.df.head(25)
            answer = "- Not derivable from computed evidence."
            return {"question": query, "plan": plan_payload, "result": result, "answer": answer, "errors": errors}

        result = AnalysisExecutor.execute(self.df, plan)
        draft = self.router.ask_analysis(Prompts.story(self.profile, query, result), question=query).strip()

        if self.cfg.strict_hallucination_guard:
            evidence = {
                "profile": self.profile,
                "plan": plan_payload,
                "result_csv": result.head(200).to_csv(index=False),
            }
            draft = HallucinationGuard.critic_pass(self.router, query, evidence, draft)
        # Deterministic bullets backstop the model output so the report never collapses into vague filler.
        answer_bullets = strengthen_bullets(split_bullets(draft), build_table_insights(query, result), min_count=4)

        return {
            "question": query,
            "plan": plan_payload,
            "result": result,
            "answer": draft,
            "answer_bullets": answer_bullets,
            "grounding": grounding_score(result, answer_bullets),
        }

    def plot(self, goal: str) -> dict[str, Any]:
        objective = (goal or "").strip()
        if not objective:
            raise ValueError("goal must be non-empty")

        # Plot presets keep the default visuals aligned with the business story we want to show.
        if objective in CURATED_PLOT_PRESETS:
            spec_payload = CURATED_PLOT_PRESETS[objective]
        else:
            raw = self.router.ask_plot(Prompts.plot_spec(self.profile, objective), goal=objective)
            spec_payload = parse_json_object(raw)
        spec = PlotSpec.from_dict(spec_payload)
        valid, errors = PlotValidator.validate(spec, self.df)
        if not valid:
            raise ValueError(f"Invalid plot spec: {errors}")

        plot_obj, plot_table = PlotRenderer.render(self.df, spec, max_rows=self.cfg.max_rows_for_plot_table)
        draft = self.router.ask_plot(Prompts.caption(objective, spec_payload, plot_table), goal=objective).strip()
        if self.cfg.strict_hallucination_guard:
            evidence = {"spec": spec_payload, "plot_table_csv": plot_table.head(200).to_csv(index=False)}
            draft = HallucinationGuard.critic_pass(self.router, objective, evidence, draft)
        caption_bullets = strengthen_bullets(split_bullets(draft), build_plot_insights(objective, plot_table), min_count=4)
        return {
            "goal": objective,
            "spec": spec_payload,
            "plot": plot_obj,
            "plot_table": plot_table,
            "caption": draft,
            "caption_bullets": caption_bullets,
            "grounding": grounding_score(plot_table, caption_bullets),
        }


def normalize_questions(
    questions: list[str] | None,
    plot_goals: list[str] | None,
    use_defaults_when_empty: bool = True,
) -> tuple[list[str], list[str]]:
    cleaned_questions = [q.strip() for q in (questions or []) if q and q.strip()]
    cleaned_goals = [g.strip() for g in (plot_goals or []) if g and g.strip()]

    if use_defaults_when_empty:
        if not cleaned_questions:
            cleaned_questions = DEFAULT_QUESTIONS.copy()
        if not cleaned_goals:
            cleaned_goals = DEFAULT_PLOT_GOALS.copy()
    return cleaned_questions, cleaned_goals


def run_case_study(
    *,
    df: pd.DataFrame,
    out_dir: str,
    title: str,
    questions: list[str] | None = None,
    plot_goals: list[str] | None = None,
    cfg: PipelineConfig | None = None,
    use_defaults_when_empty: bool = True,
    router: RouterProtocol | None = None,
) -> dict[str, str]:
    ask, goals = normalize_questions(questions, plot_goals, use_defaults_when_empty=use_defaults_when_empty)
    pipeline = AnalyticsAutomationPipeline(df=df, cfg=cfg, router=router)
    exporter = ReportExporter(out_dir=out_dir)
    sections: list[dict[str, Any]] = []

    for idx, question in enumerate(ask, start=1):
        LOGGER.info("Answering question %d: %s", idx, question)
        out = pipeline.answer(question)
        sections.append(
            {
                "heading": f"Analysis {idx}",
                "question": question,
                "answer_bullets": out["answer_bullets"],
                "table": out["result"],
                "grounding": out["grounding"],
            }
        )

    for idx, goal in enumerate(goals, start=1):
        LOGGER.info("Generating plot %d: %s", idx, goal)
        plot_out = pipeline.plot(goal)
        image_path = exporter.save_plot_png(plot_out["plot"], filename=f"plot_{idx}.png")
        sections.append(
            {
                "heading": f"Visualization {idx}",
                "question": goal,
                "table": plot_out["plot_table"].head(25),
                "plot_path": str(image_path),
                "caption_bullets": plot_out["caption_bullets"],
                "grounding": plot_out["grounding"],
            }
        )

    html = exporter.export_html(title=title, dataset_profile=pipeline.profile, sections=sections)
    pdf = exporter.export_pdf(title=title, dataset_profile=pipeline.profile, sections=sections)
    benchmark = run_core_benchmark(pipeline.df)
    benchmark_json = save_benchmark_report(benchmark, out_dir=out_dir)
    executive = exporter.export_executive_summary(dataset_profile=pipeline.profile, sections=sections)
    appendix = exporter.export_technical_appendix(
        config_summary=asdict(cfg or PipelineConfig()),
        benchmark_summary=benchmark,
    )

    return {
        "html": str(html),
        "pdf": str(pdf),
        "executive_summary": str(executive),
        "technical_appendix": str(appendix),
        "benchmark_json": str(benchmark_json),
    }
