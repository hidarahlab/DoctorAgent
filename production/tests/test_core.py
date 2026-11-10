"""Offline tests (no API calls, no cost): chunking, planner policy and the
orchestration flow, using a scripted fake LLM."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import ACCEPT_THRESHOLD, INDEX_DIR, MAX_ATTEMPTS
from doctor_agent.agents.evaluator import Evaluation, confidence
from doctor_agent.agents.planner import Plan, PlannerAgent
from doctor_agent.ingest import split_text
from doctor_agent.llm import Usage, _strict_schema
from doctor_agent.memory import Memory
from doctor_agent.orchestrator import DoctorAgentSystem
from doctor_agent.retriever import Hit


# ------------------------------------------------------------------ chunking
def test_split_short_text_is_one_chunk():
    assert split_text("Short text.", size=100) == ["Short text."]


def test_split_respects_size_and_overlaps():
    text = " ".join(f"Sentence number {i} is here." for i in range(200))
    parts = split_text(text, size=300, overlap=60)
    assert len(parts) > 5
    assert all(len(p) <= 300 + 60 for p in parts)
    # consecutive chunks share some words (overlap)
    assert set(parts[0].split()[-5:]) & set(parts[1].split()[:15])


# ------------------------------------------------------------------ evaluator scoring
def _ev(**kw) -> Evaluation:
    base = dict(faithfulness=1, completeness=1, relevance=1, tone=1, unsupported_claims=[],
                missing_points=[], verdict="pass", revised_answer="", suggested_query="", feedback="ok")
    return Evaluation(**{**base, **kw})


def test_confidence_is_weighted_mix():
    assert confidence(_ev()) == 1.0
    assert confidence(_ev(faithfulness=0.0)) == 0.5


def test_confidence_capped_when_context_insufficient():
    assert confidence(_ev(verdict="insufficient_context")) <= 0.4


def test_strict_schema_requires_all_fields():
    schema = _strict_schema(Evaluation)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(Evaluation.model_fields)


# ------------------------------------------------------------------ planner policy
@pytest.mark.parametrize("verdict,conf,attempt,expected", [
    ("pass", 0.90, 1, "accept"),
    ("revise", 0.60, 1, "requery"),
    ("revise", 0.60, MAX_ATTEMPTS, "accept"),      # mid confidence, no retries left -> warn
    ("revise", 0.30, MAX_ATTEMPTS, "escalate"),
    ("insufficient_context", 0.30, 1, "requery"),
    ("insufficient_context", 0.30, MAX_ATTEMPTS, "escalate"),
])
def test_planner_policy(verdict, conf, attempt, expected):
    assert PlannerAgent.after_evaluation(verdict, conf, attempt).action == expected


# ------------------------------------------------------------------ orchestration (fake LLM)
class FakeLLM:
    """Returns scripted outputs per agent, in order."""

    def __init__(self, script: dict[str, list]):
        self.script = {k: list(v) for k, v in script.items()}
        self.calls: list[str] = []

    def _next(self, agent):
        self.calls.append(agent)
        return self.script[agent].pop(0), Usage(agent, "fake", 10, 10, 0.0)

    def json(self, agent, system, messages, schema):
        return self._next(agent)

    def text(self, agent, system, messages):
        return self._next(agent)


class FakeRetriever:
    def search(self, query, k=5):
        chunk = {"entry": "Acne", "section": "Causes", "book_page": "25", "pdf_page": 40, "text": "Sebum clogs pores."}
        return [Hit(chunk, 1.0, 0.9)]


def plan(intent="medical_question", reply=""):
    return Plan(intent=intent, language="English", search_query="acne causes" if not reply else "",
                direct_reply=reply, reasoning="test")


def test_accept_path():
    llm = FakeLLM({"planner": [plan()], "rag": ["Sebum clogs pores [1]."], "evaluator": [_ev()]})
    r = DoctorAgentSystem(llm, FakeRetriever()).ask("What causes acne?", Memory())
    assert r.answer == "Sebum clogs pores [1]." and not r.escalated
    assert r.confidence >= ACCEPT_THRESHOLD and r.attempts == 1
    assert llm.calls == ["planner", "rag", "evaluator"]


def test_revised_answer_replaces_original():
    ev = _ev(verdict="revise", revised_answer="Corrected [1].", unsupported_claims=["made up"])
    llm = FakeLLM({"planner": [plan()], "rag": ["Wrong claim."], "evaluator": [ev]})
    r = DoctorAgentSystem(llm, FakeRetriever()).ask("q", Memory())
    assert r.answer == "Corrected [1]." and r.revised


def test_requery_then_escalate():
    bad = _ev(verdict="insufficient_context", completeness=0.1, suggested_query="better query")
    llm = FakeLLM({"planner": [plan()], "rag": ["Not in book.", "Still not."], "evaluator": [bad, bad]})
    r = DoctorAgentSystem(llm, FakeRetriever()).ask("Treatment for malaria?", Memory())
    assert r.escalated and r.attempts == MAX_ATTEMPTS
    assert llm.calls == ["planner", "rag", "evaluator", "rag", "evaluator"]
    assert "consult" in r.answer.lower()


def test_greeting_uses_no_retrieval():
    llm = FakeLLM({"planner": [plan("greeting", reply="Hi! Ask me a medical question.")]})
    r = DoctorAgentSystem(llm, FakeRetriever()).ask("hello", Memory())
    assert r.answer.startswith("Hi") and llm.calls == ["planner"]


def test_summarizer_runs_every_n_turns():
    n = 3
    llm = FakeLLM({"planner": [plan("greeting", reply="hi")] * n, "summarizer": ["summary v1"]})
    system, mem = DoctorAgentSystem(llm, FakeRetriever()), Memory()
    for _ in range(n):
        system.ask("hello", mem)
    assert mem.summary == "summary v1" and mem.turns_since_summary == 0
    assert llm.calls.count("summarizer") == 1


# ------------------------------------------------------------------ real retrieval (needs built index)
@pytest.mark.skipif(not (INDEX_DIR / "chunks.faiss").exists(), reason="index not built")
@pytest.mark.parametrize("query,entry", [
    ("What causes acne?", "Acne"),
    ("treatment for bronchitis", "Bronchitis"),
    ("side effects of acetaminophen", "Acetaminophen"),
    ("Bell's palsy prognosis", "Bell’s palsy"),  # regression: alias "ALS" used to match inside "palsy"
])
def test_retrieval_finds_right_entry(query, entry):
    from doctor_agent.retriever import HybridRetriever
    r = _retriever_cache.setdefault("r", HybridRetriever.load())
    assert entry in [h.chunk["entry"] for h in r.search(query, 5)]


_retriever_cache: dict = {}
