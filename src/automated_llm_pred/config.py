from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelRouting:
    standard_analysis: str = "phi-4"
    standard_plot: str = "Llama-3.3-70B-Instruct-quantized"
    standard_critic: str = "phi-4"
    complex_analysis: str = "openai/gpt-4o-mini"
    complex_critic: str = "openai/gpt-4o-mini"

    allowed_standard_models = {
        "Qwen2.5-Coder-32B-Instruct",
        "phi-4",
        "Llama-3.3-70B-Instruct-quantized",
        "gemma-3-12b-it",
        "Llama-3.2-11B-Vision-Instruct",
        "js2/llama-4-scout",
        "js2/gpt-oss-120b",
        "nrp/phi3",
        "nrp/gorilla",
        "nrp/olmo",
        "nrp/llava-onevision",
        "nrp/gemma3",
        "nrp/groq-tools",
        "nrp/llama3-sdsc",
        "nrp/watt",
        "nrp/llama3",
        "nrp/embed-mistral",
        "nrp/qwen3",
        "anvilgpt/llama3:70b",
        "anvilgpt/llama3:instruct",
        "anvilgpt/llama3:latest",
        "anvilgpt/llama3.3:70b",
        "anvilgpt/llama3.2:latest",
        "anvilgpt/llama3.1:70b",
        "anvilgpt/llama3.1:latest",
        "anvilgpt/codegemma:latest",
        "anvilgpt/gemma:latest",
        "anvilgpt/llama2:latest",
        "anvilgpt/llama2:13b",
        "anvilgpt/llava:latest",
        "anvilgpt/mistral:latest",
        "anvilgpt/phi3:latest",
        "anvilgpt/phi4:latest",
        "anvilgpt/qwen2.5:3b",
        "anvilgpt/qwen2.5:7b",
        "anvilgpt/qwen2.5:7b-instructt",
    }

    def __post_init__(self) -> None:
        for model in (self.standard_analysis, self.standard_plot, self.standard_critic):
            if model not in self.allowed_standard_models:
                raise ValueError(f"Unsupported standard model: {model}")


@dataclass
class PipelineConfig:
    cyverse_api_base: str = "https://llm-api.cyverse.ai/v1"
    cyverse_api_key_env: str = "CYVERSE_API_KEY"
    openai_api_base: str = "https://api.openai.com/v1"
    openai_api_key_env: str = "OPENAI_API_KEY"
    routing: ModelRouting = field(default_factory=ModelRouting)
    temperature_standard: float = 0.0
    temperature_complex: float = 0.0
    prefer_openai_primary: bool = False
    max_unique_cats_preview: int = 12
    max_rows_for_plot_table: int = 20000
    strict_hallucination_guard: bool = True
