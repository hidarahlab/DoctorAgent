# 🩺 Doctor Agent — Multi-Agent RAG Assistant over the "Medical Book"

A Streamlit chatbot in which four agents collaborate to answer medical questions **only from the
provided Medical Book** (Gale Encyclopedia of Medicine, vol. 1, topics A–B), check their own answers
for hallucinations, remember the conversation, and escalate when the book can't answer.

```
User ──► Planner (Haiku 5.5) ── intent + English search query
            │
            ├─ greeting / out-of-scope / emergency ──► direct reply
            ├─ summary request ──► Summarizer.for_user
            └─ medical question:
                 ┌──────────────────────────────────────────────┐
                 │ RAG (Opus 5.5): hybrid retrieval → cited answer│
                 │ Evaluator (Opus 5.5): fact-check, score, revise │◄─ re-query with
                 │ Planner policy: accept / re-query / escalate   │   suggested query
                 └──────────────────────────────────────────────┘
            ▼
       Memory  ◄── Summarizer (Haiku 5.5) every 3 turns
```

## Quick start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # then put your ANTHROPIC_API_KEY in .env
python -m doctor_agent.retriever  # chunks -> index/chunks.faiss   (~2 min, first run downloads the embedding model)
streamlit run app.py
```

`data/chunks.json` is included, so the PDF is only needed to re-run ingestion: put the provided
`medical_book.pdf` in `data/` and run `python -m doctor_agent.ingest` (~15 s).
The app builds the vector index automatically on first start if it is missing.

## Results (27-question evaluation, `eval/results/report.md`)

| Metric | Value |
|---|---|
| Planner intent accuracy | 100% |
| Retrieval Hit@5 / MRR (in-book) | 100% / 1.00 |
| In-book answered · out-of-book escalated | 100% · 100% |
| Faithfulness · completeness · relevance · tone | 0.95 · 0.89 · 0.95 · 0.94 |
| Valid citations | 100% |
| Avg latency (p90) | 13.5 s (20.9 s) |
| Avg cost per medical question | $0.050 |

The first evaluation run exposed a retrieval bug (the alias "ALS" matched inside "p**als**y"); after the
fix every category reached 100% (`eval/results/*_v1_before_alias_fix.*` keeps the first run).

| Command | What it does |
|---|---|
| `pytest -q tests` | 20 offline tests (no API cost): chunking, planner policy, orchestration with a fake LLM, retrieval |
| `python scripts/smoke_test.py "question" ...` | run questions through the pipeline in the terminal, with the agent trace |
| `python eval/run_eval.py` | full evaluation on `eval/questions.json` (27 questions, ~$1.5) |
| `python eval/run_eval.py --ablation-only` | retrieval ablation only (free) |

## Project layout

```
app.py                      Streamlit UI (chat, confidence badges, evaluator feedback, sources, agent trace)
config.py                   every tunable parameter: models, effort, thresholds, chunk size, top-k ...
doctor_agent/
  ingest.py                 font-aware PDF parsing -> structure-aware chunks (entry / section / page)
  retriever.py              hybrid retrieval: FAISS dense + BM25, Reciprocal Rank Fusion, alias expansion
  llm.py                    Anthropic SDK wrapper: structured outputs, refusal fallback, token/cost tracking
  memory.py                 running summary + recent turns
  orchestrator.py           runs one turn through the agents, records the agent trace
  agents/planner.py         intent classification + query rewriting (LLM) and accept/re-query/escalate (rules)
  agents/rag.py             grounded, cited answer from retrieved excerpts
  agents/evaluator.py       LLM-as-judge: faithfulness, completeness, relevance, tone, revision
  agents/summarizer.py      conversation memory + user-facing recap
eval/                       questions, evaluation script, results
tests/                      offline unit tests
```

## Key parameters (`config.py`)

| Component | Choice |
|---|---|
| Chunking | by encyclopedia entry → section, max 1 200 chars, 200 overlap → 3 328 chunks / 282 entries |
| Embeddings | `BAAI/bge-small-en-v1.5` (384-d), local ONNX via fastembed |
| Retrieval | FAISS `IndexFlatIP` (cosine) + BM25, top-30 each, RRF (k=60), top-5 to the LLM |
| Planner / Summarizer | `claude-haiku-5-5`, effort low |
| RAG / Evaluator | `claude-opus-5-5`, effort low / medium, server-side refusal fallback |
| Confidence | 0.5·faithfulness + 0.3·completeness + 0.2·relevance (capped at 0.4 if context insufficient) |
| Policy | accept ≥ 0.70 · otherwise re-query once · escalate if < 0.45 or book lacks the answer |

> Educational project — not a substitute for professional medical advice.
