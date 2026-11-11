"""Evaluation of the whole multi-agent system on eval/questions.json.

Measures
  * routing      - Planner intent accuracy
  * retrieval    - Hit@5 and MRR of the expected Medical Book entry
  * answers      - Evaluator scores (faithfulness, completeness, relevance, tone), confidence,
                   revision / re-query rate, citation validity
  * safety       - in-book questions answered vs. out-of-book questions correctly escalated
  * cost/latency - USD and seconds per question
plus a free retrieval ablation: dense vs. BM25 vs. hybrid, raw question vs. Planner-rewritten query.

Run:  python eval/run_eval.py                 (full run, uses the API, ~$1.5)
      python eval/run_eval.py --ablation-only (re-uses saved results, free)
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as stats
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor_agent.memory import Memory
from doctor_agent.orchestrator import DoctorAgentSystem

QUESTIONS = Path(__file__).parent / "questions.json"
OUT = Path(__file__).parent / "results"
MEDICAL = {"medical_question", "follow_up"}


def rank_of_expected(entries: list[str], expected: list[str]) -> int | None:
    for r, e in enumerate(entries, 1):
        if e in expected:
            return r
    return None


def citations_valid(answer: str, n_sources: int) -> bool:
    nums = [int(n) for n in re.findall(r"\[(\d+)\]", answer)]
    return all(1 <= n <= n_sources for n in nums)


def run_full(system: DoctorAgentSystem, questions: list[dict]) -> list[dict]:
    rows = []
    for i, q in enumerate(questions, 1):
        t0 = time.perf_counter()
        r = system.ask(q["question"], Memory())
        expected_intent = q.get("expected_intent", "medical_question")
        intent_ok = (r.intent in MEDICAL) if expected_intent == "medical_question" else (r.intent == expected_intent)
        entries = [h.chunk["entry"] for h in r.sources]
        rank = rank_of_expected(entries, q["expected_entries"]) if q["expected_entries"] else None
        ev = r.evaluation
        if q["category"].startswith("in_book"):
            outcome_ok = not r.escalated
        elif q["category"] == "out_of_book":
            outcome_ok = r.escalated
        else:
            outcome_ok = intent_ok
        row = {
            "id": q["id"], "category": q["category"], "lang": q["lang"], "question": q["question"],
            "intent": r.intent, "intent_ok": intent_ok,
            "search_query": r.plan.search_query if r.plan else "",
            "escalated": r.escalated, "outcome_ok": outcome_ok, "revised": r.revised, "attempts": r.attempts,
            "confidence": r.confidence,
            "faithfulness": ev.faithfulness if ev else None, "completeness": ev.completeness if ev else None,
            "relevance": ev.relevance if ev else None, "tone": ev.tone if ev else None,
            "verdict": ev.verdict if ev else None, "unsupported_claims": len(ev.unsupported_claims) if ev else None,
            "hit_at_5": (rank is not None) if q["expected_entries"] else None,
            "reciprocal_rank": (1 / rank if rank else 0.0) if q["expected_entries"] else None,
            "citations_valid": citations_valid(r.answer, len(r.sources)) if r.sources else None,
            "sources": entries, "seconds": round(time.perf_counter() - t0, 2),
            "cost": round(r.cost, 5), "tokens": sum(r.tokens), "answer": r.answer,
        }
        rows.append(row)
        print(f"[{i:2}/{len(questions)}] {q['id']:6} intent={r.intent:16} esc={r.escalated!s:5} "
              f"conf={r.confidence if r.confidence is not None else '-'!s:5} ok={outcome_ok!s:5} "
              f"{row['seconds']:5.1f}s ${row['cost']:.4f}", flush=True)
    return rows


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(stats.mean(xs), 3) if xs else None


def rate(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(bool(x) for x in xs) / len(xs), 3) if xs else None


def summarize(rows: list[dict]) -> dict:
    inb = [r for r in rows if r["category"].startswith("in_book")]
    oob = [r for r in rows if r["category"] == "out_of_book"]
    answered = [r for r in inb if not r["escalated"]]
    secs = sorted(r["seconds"] for r in rows)
    return {
        "n_questions": len(rows),
        "intent_accuracy": rate(r["intent_ok"] for r in rows),
        "retrieval_hit_at_5": rate(r["hit_at_5"] for r in inb),
        "retrieval_mrr": mean(r["reciprocal_rank"] for r in inb),
        "in_book_answer_rate": rate(not r["escalated"] for r in inb),
        "out_of_book_escalation_rate": rate(r["escalated"] for r in oob),
        "overall_outcome_accuracy": rate(r["outcome_ok"] for r in rows),
        "faithfulness": mean(r["faithfulness"] for r in answered),
        "completeness": mean(r["completeness"] for r in answered),
        "relevance": mean(r["relevance"] for r in answered),
        "tone": mean(r["tone"] for r in answered),
        "confidence_in_book": mean(r["confidence"] for r in answered),
        "confidence_out_of_book": mean(r["confidence"] for r in oob),
        "revision_rate": rate(r["revised"] for r in inb),
        "requery_rate": rate(r["attempts"] > 1 for r in rows if r["attempts"]),
        "citation_validity": rate(r["citations_valid"] for r in rows),
        "avg_latency_s": round(stats.mean(secs), 2),
        "p90_latency_s": secs[int(0.9 * (len(secs) - 1))],
        "avg_cost_usd": round(stats.mean(r["cost"] for r in rows), 4),
        "avg_cost_medical_usd": round(stats.mean(r["cost"] for r in rows if r["attempts"]), 4),
        "total_cost_usd": round(sum(r["cost"] for r in rows), 4),
    }


def ablation(system: DoctorAgentSystem, rows: list[dict], questions: list[dict]) -> list[dict]:
    """Retrieval only (free): which retriever + query form finds the expected entry?"""
    rewritten = {r["id"]: r["search_query"] for r in rows}
    inb = [q for q in questions if q["category"].startswith("in_book")]
    table = []
    for source in ("raw question", "planner rewrite"):
        for mode in ("dense", "sparse", "hybrid"):
            hits, rr = [], []
            for q in inb:
                query = q["question"] if source == "raw question" else (rewritten.get(q["id"]) or q["question"])
                entries = [h.chunk["entry"] for h in system.retriever.search(query, 5, mode=mode)]
                rank = rank_of_expected(entries, q["expected_entries"])
                hits.append(rank is not None)
                rr.append(1 / rank if rank else 0.0)
            table.append({"query": source, "retriever": mode,
                          "hit_at_5": round(sum(hits) / len(hits), 3), "mrr": round(stats.mean(rr), 3)})
    return table


def write_report(summary: dict, abl: list[dict], rows: list[dict]) -> None:
    lines = ["# Evaluation results", "", "| Metric | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in summary.items()]
    lines += ["", "## Retrieval ablation (in-book questions, Hit@5 / MRR)", "",
              "| Query | Retriever | Hit@5 | MRR |", "|---|---|---|---|"]
    lines += [f"| {a['query']} | {a['retriever']} | {a['hit_at_5']} | {a['mrr']} |" for a in abl]
    lines += ["", "## Per question", "",
              "| id | category | intent | escalated | conf | F | C | hit@5 | s | $ |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['category']} | {r['intent']} | {r['escalated']} | {r['confidence']} | "
                     f"{r['faithfulness']} | {r['completeness']} | {r['hit_at_5']} | {r['seconds']} | {r['cost']} |")
    (OUT / "report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ablation-only", action="store_true")
    ap.add_argument("--ids", nargs="*", help="only run these question ids")
    args = ap.parse_args()

    questions = json.loads(QUESTIONS.read_text())
    if args.ids:
        questions = [q for q in questions if q["id"] in args.ids]
    OUT.mkdir(exist_ok=True)
    system = DoctorAgentSystem()

    if args.ablation_only:
        rows = json.loads((OUT / "results.json").read_text())
    else:
        rows = run_full(system, questions)
        (OUT / "results.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))

    summary = summarize(rows)
    abl = ablation(system, rows, questions)
    (OUT / "summary.json").write_text(json.dumps({"summary": summary, "ablation": abl}, indent=1))
    write_report(summary, abl, rows)
    print(json.dumps(summary, indent=1))
    for a in abl:
        print(a)


if __name__ == "__main__":
    main()
