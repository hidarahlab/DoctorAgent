"""Planner Agent - the coordinator.

Two kinds of decisions:
1. BEFORE answering (LLM call, cheap model): what does the user want?
   -> intent, language, and a standalone English search query.
2. AFTER evaluation (deterministic policy): accept, re-query or escalate,
   based on the Evaluator's confidence score.  Rules (not an LLM) make this
   step predictable, testable and free.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from config import ACCEPT_THRESHOLD, ESCALATE_THRESHOLD, MAX_ATTEMPTS, SUMMARY_EVERY
from doctor_agent.llm import LLM, Usage
from doctor_agent.memory import Memory

Intent = Literal["medical_question", "follow_up", "summary_request", "greeting", "out_of_scope", "emergency"]


class Plan(BaseModel):
    intent: Intent
    language: str = Field(description="Language the user writes in, e.g. 'Indonesian' or 'English'")
    search_query: str = Field(description="Standalone English search query for the medical encyclopedia; empty if no retrieval is needed")
    direct_reply: str = Field(description="Short reply for greeting / out_of_scope / emergency, in the user's language; empty otherwise")
    reasoning: str = Field(description="One sentence explaining the decision")


@dataclass
class Decision:
    action: Literal["accept", "requery", "escalate"]
    reason: str


SYSTEM = """You are the Planner of a multi-agent medical assistant. The knowledge source is the
"Medical Book": the Gale Encyclopedia of Medicine, volume 1 (topics from A to B, written in English).

Classify the user's latest message:
- medical_question: a new health/medical question.
- follow_up: a medical question that depends on earlier turns ("how is it treated?").
- summary_request: the user asks to summarise / recap the conversation.
- greeting: greetings, thanks, small talk, questions about what you can do.
- out_of_scope: clearly NOT about health or medicine (sports, coding, politics...).
- emergency: the user describes an acute, possibly life-threatening situation happening now
  (e.g. chest pain with shortness of breath, stroke signs, heavy bleeding, overdose, suicidal intent).

Rules:
- Any health topic is medical_question/follow_up even if it might not be in the book;
  the retrieval step decides whether the book covers it. Do NOT answer medical questions yourself.
- search_query: rewrite the question as a standalone English search query, resolving pronouns from
  the conversation ("it" -> the disease being discussed) and translating medical terms into the
  terminology an English encyclopedia uses. Empty for greeting/out_of_scope/summary_request.
- direct_reply: for greeting, a friendly 1-2 sentence reply explaining you answer questions from the
  Medical Book; for out_of_scope, politely say you only handle medical topics; for emergency, tell
  the user to contact emergency services immediately (Indonesia: 119 or 112, or the nearest ER).
  Write it in the user's language. Empty for the other intents."""


class PlannerAgent:
    name = "planner"

    def __init__(self, llm: LLM):
        self.llm = llm

    # ------------------------------------------------------------ 1. plan
    def plan(self, message: str, memory: Memory) -> tuple[Plan, Usage]:
        prompt = f"{memory.context()}\n\nLatest user message:\n{message}"
        return self.llm.json(self.name, SYSTEM, [{"role": "user", "content": prompt}], Plan)

    @staticmethod
    def route(plan: Plan) -> list[str]:
        """Which agents to activate for this intent."""
        return {
            "medical_question": ["rag", "evaluator", "summarizer?"],
            "follow_up": ["rag", "evaluator", "summarizer?"],
            "summary_request": ["summarizer"],
            "greeting": [],
            "out_of_scope": [],
            "emergency": [],
        }[plan.intent]

    # ------------------------------------------------------------ 2. decide
    @staticmethod
    def after_evaluation(verdict: str, confidence: float, attempt: int) -> Decision:
        can_retry = attempt < MAX_ATTEMPTS
        if verdict == "insufficient_context":
            if can_retry:
                return Decision("requery", "retrieved passages do not answer the question; trying a better query")
            return Decision("escalate", "the Medical Book does not seem to cover this question")
        if confidence >= ACCEPT_THRESHOLD:
            return Decision("accept", f"confidence {confidence:.2f} >= {ACCEPT_THRESHOLD}")
        if can_retry:
            return Decision("requery", f"confidence {confidence:.2f} < {ACCEPT_THRESHOLD}; re-querying")
        if confidence >= ESCALATE_THRESHOLD:
            return Decision("accept", f"accepted with low confidence {confidence:.2f} (shown with a warning)")
        return Decision("escalate", f"confidence {confidence:.2f} < {ESCALATE_THRESHOLD} after re-query")

    @staticmethod
    def should_summarize(memory: Memory) -> bool:
        return memory.turns_since_summary >= SUMMARY_EVERY
