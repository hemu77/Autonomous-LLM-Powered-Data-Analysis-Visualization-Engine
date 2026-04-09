from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from langchain_community.chat_models import ChatLiteLLM
from langchain_core.messages import HumanMessage

from automated_llm_pred.config import PipelineConfig
from automated_llm_pred.utils import is_complex_request


class RouterProtocol(Protocol):
    def ask_analysis(self, prompt: str, question: str = "") -> str:
        ...

    def ask_plot(self, prompt: str, goal: str = "") -> str:
        ...

    def ask_critic(self, prompt: str, context: str = "") -> str:
        ...


@dataclass
class LLMService:
    model: str
    api_key: str
    api_base: str
    temperature: float

    def __post_init__(self) -> None:
        self._client = ChatLiteLLM(
            model=self.model,
            api_key=self.api_key,
            api_base=self.api_base,
            temperature=self.temperature,
        )

    def ask(self, prompt: str) -> str:
        response = self._client.invoke([HumanMessage(content=prompt)])
        return response.content


class HybridModelRouter:
    def __init__(self, cfg: PipelineConfig):
        self.cfg = cfg
        cyverse_key = os.getenv(cfg.cyverse_api_key_env, "").strip()
        self.standard_analysis = None
        self.standard_plot = None
        self.standard_critic = None
        if cyverse_key:
            self.standard_analysis = LLMService(
                model=cfg.routing.standard_analysis,
                api_key=cyverse_key,
                api_base=os.getenv("CYVERSE_API_BASE", cfg.cyverse_api_base),
                temperature=cfg.temperature_standard,
            )
            self.standard_plot = LLMService(
                model=cfg.routing.standard_plot,
                api_key=cyverse_key,
                api_base=os.getenv("CYVERSE_API_BASE", cfg.cyverse_api_base),
                temperature=cfg.temperature_standard,
            )
            self.standard_critic = LLMService(
                model=cfg.routing.standard_critic,
                api_key=cyverse_key,
                api_base=os.getenv("CYVERSE_API_BASE", cfg.cyverse_api_base),
                temperature=cfg.temperature_standard,
            )

        openai_key = os.getenv(cfg.openai_api_key_env, "").strip()
        self.complex_analysis = None
        self.complex_critic = None
        self.complex_plot = None
        if openai_key:
            base = os.getenv("OPENAI_API_BASE", cfg.openai_api_base)
            self.complex_analysis = LLMService(
                model=cfg.routing.complex_analysis,
                api_key=openai_key,
                api_base=base,
                temperature=cfg.temperature_complex,
            )
            self.complex_critic = LLMService(
                model=cfg.routing.complex_critic,
                api_key=openai_key,
                api_base=base,
                temperature=cfg.temperature_complex,
            )
            self.complex_plot = LLMService(
                model=cfg.routing.complex_analysis,
                api_key=openai_key,
                api_base=base,
                temperature=cfg.temperature_complex,
            )

        if self.standard_analysis is None and self.complex_analysis is None:
            raise RuntimeError(
                f"Missing model credentials. Set {cfg.cyverse_api_key_env} or {cfg.openai_api_key_env}."
            )

    def _analysis_service(self, text: str) -> LLMService:
        # OpenAI can be forced to the front for portfolio runs, but the router still supports fallback.
        if self.cfg.prefer_openai_primary and self.complex_analysis is not None:
            return self.complex_analysis
        if self.complex_analysis is not None and is_complex_request(text):
            return self.complex_analysis
        return self.standard_analysis or self.complex_analysis

    def _plot_service(self, text: str) -> LLMService:
        if self.cfg.prefer_openai_primary and self.complex_plot is not None:
            return self.complex_plot
        if self.complex_plot is not None and is_complex_request(text):
            return self.complex_plot
        return self.standard_plot or self.complex_plot

    def _critic_service(self, text: str) -> LLMService:
        if self.cfg.prefer_openai_primary and self.complex_critic is not None:
            return self.complex_critic
        if self.complex_critic is not None and is_complex_request(text):
            return self.complex_critic
        return self.standard_critic or self.complex_critic

    def ask_analysis(self, prompt: str, question: str = "") -> str:
        return self._analysis_service(question).ask(prompt)

    def ask_plot(self, prompt: str, goal: str = "") -> str:
        return self._plot_service(goal).ask(prompt)

    def ask_critic(self, prompt: str, context: str = "") -> str:
        return self._critic_service(context).ask(prompt)
