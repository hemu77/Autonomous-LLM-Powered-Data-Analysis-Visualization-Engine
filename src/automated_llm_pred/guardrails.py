from __future__ import annotations

import json
from typing import Any

from automated_llm_pred.routing import RouterProtocol


class HallucinationGuard:
    @staticmethod
    def critic_pass(
        router: RouterProtocol,
        question_or_goal: str,
        evidence: dict[str, Any],
        draft: str,
    ) -> str:
        prompt = f"""
You are a strict factuality auditor.

QUESTION_OR_GOAL:
{question_or_goal}

EVIDENCE JSON:
{json.dumps(evidence, ensure_ascii=False)[:22000]}

DRAFT:
{draft}

Rules:
- Return bullets only (prefer 4 to 6 lines when evidence supports it).
- Rewrite or remove unsupported claims.
- If unsupported, say: "Not derivable from computed evidence."
- Do not add new facts.
"""
        return router.ask_critic(prompt, context=question_or_goal).strip()
