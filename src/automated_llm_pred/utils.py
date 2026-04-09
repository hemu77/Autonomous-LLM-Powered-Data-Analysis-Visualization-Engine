from __future__ import annotations

import json
import re
from typing import Any


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"```[a-zA-Z]*\n?", "", cleaned).replace("```", "").strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
            return parsed[0]
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    raise ValueError(f"Could not parse JSON object from model output:\n{text}")


def split_bullets(text: str, limit: int = 8) -> list[str]:
    bullets: list[str] = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        stripped = re.sub(r"^[-*•]+\s*", "", stripped).strip()
        if stripped:
            bullets.append(stripped)
        if len(bullets) >= limit:
            break
    return bullets


def is_complex_request(text: str) -> bool:
    prompt = (text or "").lower()
    tokens = len(prompt.split())
    complexity_signals = [
        "why",
        "root cause",
        "segment",
        "recommend",
        "executive",
        "multi-step",
        "cohort",
        "retention",
        "counterfactual",
    ]
    matched = any(signal in prompt for signal in complexity_signals)
    return matched or tokens > 28
