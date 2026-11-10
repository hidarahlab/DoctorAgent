"""Thin wrapper around the Anthropic SDK shared by all agents.

It gives every agent two calls - `text()` and `json()` - and records token
usage + cost + latency of every call, so the UI and the evaluation can show
exactly what each agent costs.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from config import EFFORT, MAX_TOKENS, MODELS, PRICES

T = TypeVar("T", bound=BaseModel)

# Opus 5.5 supports server-side refusal fallbacks: if a safety classifier
# wrongly declines a (legitimate) medical question, the API retries it on a
# fallback model inside the same call instead of failing.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
FALLBACK_MODELS = {"claude-opus-5-5"}


class LLMRefusal(Exception):
    """The model declined to answer (stop_reason == 'refusal')."""


@dataclass
class Usage:
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    seconds: float

    @property
    def cost(self) -> float:
        p_in, p_out = PRICES.get(self.model, (0.0, 0.0))
        return (self.input_tokens * p_in + self.output_tokens * p_out) / 1_000_000


def _strict_schema(model: type[BaseModel]) -> dict:
    """Pydantic schema -> JSON schema accepted by structured outputs
    (every field required, no extra keys)."""
    schema = model.model_json_schema()

    def fix(node):
        if isinstance(node, dict):
            node.pop("title", None)
            node.pop("default", None)
            if node.get("type") == "object" and "properties" in node:
                node["additionalProperties"] = False
                node["required"] = list(node["properties"])
            for v in node.values():
                fix(v)
        elif isinstance(node, list):
            for v in node:
                fix(v)

    fix(schema)
    return schema


class LLM:
    def __init__(self, client: anthropic.Anthropic | None = None):
        self.client = client or anthropic.Anthropic(max_retries=3)

    def _call(self, agent: str, system: str, messages: list[dict], fmt: dict | None = None):
        model = MODELS[agent]
        output_config: dict = {"effort": EFFORT[agent]}
        if fmt:
            output_config["format"] = fmt
        kwargs = dict(
            model=model,
            max_tokens=MAX_TOKENS[agent],
            system=system,
            messages=messages,
            output_config=output_config,
        )
        t0 = time.perf_counter()
        if model in FALLBACK_MODELS:
            resp = self.client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
        else:
            resp = self.client.messages.create(**kwargs)
        usage = Usage(agent, model, resp.usage.input_tokens, resp.usage.output_tokens, time.perf_counter() - t0)
        if resp.stop_reason == "refusal":
            raise LLMRefusal(getattr(resp.stop_details, "explanation", "") or "declined")
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        return text, usage

    def text(self, agent: str, system: str, messages: list[dict]) -> tuple[str, Usage]:
        return self._call(agent, system, messages)

    def json(self, agent: str, system: str, messages: list[dict], schema: type[T]) -> tuple[T, Usage]:
        fmt = {"type": "json_schema", "schema": _strict_schema(schema)}
        text, usage = self._call(agent, system, messages, fmt)
        return schema.model_validate(json.loads(text)), usage
