"""Orchestrator - runs one user turn through the agents.

    user message
        -> Planner.plan()            intent + search query          (Haiku)
        -> [medical] loop up to MAX_ATTEMPTS:
               RAG.run()             retrieve + grounded answer     (Opus)
               Evaluator.run()       fact-check, score, revise      (Opus)
               Planner.after_evaluation()  accept / requery / escalate (rules)
        -> [summary_request] Summarizer.for_user()
        -> memory.add(); every N turns Summarizer.update()          (Haiku)

Every agent call is logged as a Step, which the UI shows as an "agent trace".
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from config import MAX_ATTEMPTS
from doctor_agent.agents.evaluator import Evaluation, EvaluatorAgent
from doctor_agent.agents.planner import Plan, PlannerAgent
from doctor_agent.agents.rag import RAGAgent
from doctor_agent.agents.summarizer import SummarizerAgent
from doctor_agent.llm import LLM, LLMRefusal, Usage
from doctor_agent.memory import Memory
from doctor_agent.retriever import Hit, HybridRetriever


@dataclass
class Step:
    agent: str
    action: str
    detail: str = ""
    seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    model: str = ""

    @classmethod
    def from_usage(cls, u: Usage | None, action: str, detail: str = "") -> "Step":
        if u is None:
            return cls("system", action, detail)
        return cls(u.agent, action, detail, u.seconds, u.input_tokens, u.output_tokens, u.cost, u.model)


@dataclass
class TurnResult:
    answer: str
    intent: str
    plan: Plan | None = None
    confidence: float | None = None
    evaluation: Evaluation | None = None
    sources: list[Hit] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    escalated: bool = False
    revised: bool = False
    attempts: int = 0
    seconds: float = 0.0

    @property
    def cost(self) -> float:
        return sum(s.cost for s in self.steps)

    @property
    def tokens(self) -> tuple[int, int]:
        return sum(s.input_tokens for s in self.steps), sum(s.output_tokens for s in self.steps)


def _is_indonesian(language: str) -> bool:
    return "indones" in language.lower() or "bahasa" in language.lower()


def escalation_message(language: str, partial: str = "") -> str:
    if _is_indonesian(language):
        msg = ("⚠️ **Saya belum bisa menjawab ini dengan yakin dari Medical Book.** "
               "Informasi yang relevan tidak ditemukan atau tidak cukup di dalam buku. "
               "Silakan konsultasikan pertanyaan ini dengan dokter atau tenaga kesehatan.")
        prefix = "Informasi terkait yang ditemukan (tingkat keyakinan rendah):"
    else:
        msg = ("⚠️ **I can't answer this confidently from the Medical Book.** "
               "The relevant information was not found or is insufficient in the book. "
               "Please consult a doctor or a qualified health professional.")
        prefix = "Related information that was found (low confidence):"
    return f"{msg}\n\n{prefix}\n\n{partial}" if partial else msg


class DoctorAgentSystem:
    def __init__(self, llm: LLM | None = None, retriever: HybridRetriever | None = None):
        self.llm = llm or LLM()
        self.retriever = retriever or HybridRetriever.load()
        self.planner = PlannerAgent(self.llm)
        self.rag = RAGAgent(self.llm, self.retriever)
        self.evaluator = EvaluatorAgent(self.llm)
        self.summarizer = SummarizerAgent(self.llm)

    def ask(self, message: str, memory: Memory, on_step: Callable[[Step], None] | None = None,
            on_progress: Callable[[str], None] | None = None) -> TurnResult:
        """on_step: called AFTER each agent call (for the trace).
        on_progress: called with the agent name just BEFORE it starts (for a live "X is running" label)."""
        t0 = time.perf_counter()
        steps: list[Step] = []

        def log(step: Step) -> None:
            steps.append(step)
            if on_step:
                on_step(step)

        def progress(agent: str) -> None:
            if on_progress:
                on_progress(agent)

        progress("planner")
        plan, u = self.planner.plan(message, memory)
        route = self.planner.route(plan)
        log(Step.from_usage(u, f"intent = {plan.intent}",
                            f"route: {' → '.join(route) or 'direct reply'} | query: {plan.search_query or '-'} | {plan.reasoning}"))

        result = TurnResult(answer="", intent=plan.intent, plan=plan, steps=steps)

        if plan.intent in ("greeting", "out_of_scope", "emergency"):
            result.answer = plan.direct_reply
            result.escalated = plan.intent == "emergency"
        elif plan.intent == "summary_request":
            progress("summarizer")
            text, u = self.summarizer.for_user(memory, plan.language)
            log(Step.from_usage(u, "recap for user"))
            result.answer = text or ("Belum ada percakapan untuk dirangkum." if _is_indonesian(plan.language)
                                     else "There is no conversation to summarise yet.")
        else:
            self._answer_medical(message, plan, memory, result, log, progress)

        memory.add(message, result.answer)
        if self.planner.should_summarize(memory):
            progress("summarizer")
            u = self.summarizer.update(memory)
            log(Step.from_usage(u, "memory updated", memory.summary[:160]))

        result.seconds = time.perf_counter() - t0
        return result

    def _answer_medical(self, message: str, plan: Plan, memory: Memory, result: TurnResult, log, progress) -> None:
        query, feedback = plan.search_query or message, ""
        best = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            result.attempts = attempt
            progress("rag")
            try:
                rag = self.rag.run(message, query, plan.language, memory, feedback)
            except LLMRefusal as e:
                log(Step("rag", "refused", str(e)))
                break
            sources = ", ".join(dict.fromkeys(h.chunk["entry"] for h in rag.hits))
            log(Step.from_usage(rag.usage, f"attempt {attempt}: answered",
                                f"query: {query} | top sim {rag.top_similarity:.2f} | sources: {sources}"))

            progress("evaluator")
            ev, conf, u = self.evaluator.run(message, rag.answer, rag.hits, plan.language)
            log(Step.from_usage(u, f"verdict = {ev.verdict}, confidence = {conf:.2f}",
                                f"F {ev.faithfulness:.2f} · C {ev.completeness:.2f} · R {ev.relevance:.2f} · "
                                f"T {ev.tone:.2f} | unsupported: {len(ev.unsupported_claims)} | {ev.feedback}"))

            revised = ev.verdict == "revise" and bool(ev.revised_answer.strip())
            final = ev.revised_answer.strip() if revised else rag.answer
            if best is None or conf > best[0]:
                best = (conf, final, ev, rag.hits, revised)

            decision = self.planner.after_evaluation(ev.verdict, conf, attempt)
            log(Step("planner", f"decision = {decision.action}", decision.reason))
            if decision.action != "requery":
                break
            query = ev.suggested_query.strip() or f"{plan.search_query} {message}"
            feedback = "; ".join(ev.unsupported_claims + [f"missing: {m}" for m in ev.missing_points]) or ev.feedback

        if best is None:
            result.answer, result.escalated = escalation_message(plan.language), True
            return

        conf, answer, ev, hits, revised = best
        result.confidence, result.evaluation, result.sources, result.revised = conf, ev, hits, revised
        final = self.planner.after_evaluation(ev.verdict, conf, MAX_ATTEMPTS)
        if result.attempts > 1:
            log(Step("planner", f"final = {final.action}", f"best attempt: {final.reason}"))
        if final.action == "escalate":
            result.escalated = True
            partial = answer if ev.verdict != "insufficient_context" else ""
            result.answer = escalation_message(plan.language, partial)
        else:
            result.answer = answer
