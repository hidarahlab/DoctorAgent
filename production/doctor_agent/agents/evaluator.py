"""Evaluator Agent - an LLM-as-judge that fact-checks the RAG answer against
the same excerpts the RAG agent saw.

It scores faithfulness (no hallucination), completeness, relevance and tone,
lists unsupported claims, and - if needed - returns a corrected answer.
The final confidence score is a fixed weighted mix of those scores
(computed in code, so it is transparent and reproducible)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from config import CONFIDENCE_WEIGHTS
from doctor_agent.agents.rag import format_context
from doctor_agent.llm import LLM, Usage
from doctor_agent.retriever import Hit


class Evaluation(BaseModel):
    faithfulness: float = Field(description="0-1: share of claims in the FINAL answer supported by the excerpts")
    completeness: float = Field(description="0-1: how fully the FINAL answer addresses the question, given what the excerpts contain")
    relevance: float = Field(description="0-1: how well the excerpts and the FINAL answer match the question")
    tone: float = Field(description="0-1: clear, calm, empathetic, non-alarming, appropriate for a medical audience")
    unsupported_claims: list[str] = Field(description="Claims in the ORIGINAL answer not supported by the excerpts")
    missing_points: list[str] = Field(description="Important points present in the excerpts but missing from the answer")
    verdict: Literal["pass", "revise", "insufficient_context"]
    revised_answer: str = Field(description="Corrected answer if verdict is 'revise', otherwise empty")
    suggested_query: str = Field(description="Better English search query if verdict is 'insufficient_context', otherwise empty")
    feedback: str = Field(description="One or two sentences summarising the review")


SYSTEM = """You are the Evaluator in a medical question-answering system. You fact-check an answer
against the numbered excerpts from the Medical Book that the answer was supposed to be based on.

Procedure:
1. Split the answer into individual claims. A claim is supported only if an excerpt states it
   (paraphrase and translation are fine). Anything else is unsupported - even if medically true.
2. Choose a verdict:
   - pass: every claim is supported and the answer addresses the question well.
   - revise: the excerpts do answer the question, but the answer has unsupported claims, wrong
     citations, missing key points, or poor tone. Write `revised_answer`: same language, same style,
     unsupported claims removed, key missing points added from the excerpts, citations [n] kept.
   - insufficient_context: the excerpts do not contain the information needed to answer the question.
     Give `suggested_query`: a better English query for the encyclopedia (or empty if the topic is
     probably not in an A-B volume at all). An answer that correctly says "the book does not cover
     this" is still insufficient_context.
3. Score the FINAL answer - the original if verdict is pass, otherwise your revised_answer -
   on faithfulness, completeness, relevance and tone (0.0-1.0). Be strict and calibrated:
   0.9+ only for excellent, fully supported answers. For insufficient_context, completeness <= 0.3."""


class EvaluatorAgent:
    name = "evaluator"

    def __init__(self, llm: LLM):
        self.llm = llm

    def run(self, question: str, answer: str, hits: list[Hit], language: str) -> tuple[Evaluation, float, Usage]:
        prompt = (
            f"User question ({language}): {question}\n\n"
            f"Excerpts from the Medical Book:\n{format_context(hits)}\n\n"
            f"Answer to evaluate:\n{answer}"
        )
        ev, usage = self.llm.json(self.name, SYSTEM, [{"role": "user", "content": prompt}], Evaluation)
        return ev, confidence(ev), usage


def confidence(ev: Evaluation) -> float:
    clamp = lambda x: max(0.0, min(1.0, float(x)))
    score = sum(w * clamp(getattr(ev, k)) for k, w in CONFIDENCE_WEIGHTS.items())
    if ev.verdict == "insufficient_context":
        score = min(score, 0.4)  # never "confident" when the book lacks the answer
    return round(score, 3)
