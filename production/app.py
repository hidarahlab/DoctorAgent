"""Doctor Agent - Streamlit UI for the multi-agent Medical Book assistant.

Run:  streamlit run app.py
"""
import os

import streamlit as st

from config import ACCEPT_THRESHOLD, MODELS
from doctor_agent.memory import Memory
from doctor_agent.orchestrator import DoctorAgentSystem, Step, TurnResult

st.set_page_config(page_title="Doctor Agent", page_icon="🩺", layout="wide")

AGENT_ICON = {"planner": "🧭", "rag": "📚", "evaluator": "🔍", "summarizer": "📝", "system": "⚙️"}
AGENT_ROLE = {
    "planner": "Classifies intent, rewrites the query, decides accept / re-query / escalate",
    "rag": "Hybrid retrieval (FAISS + BM25) and a grounded, cited answer",
    "evaluator": "Fact-checks the answer, scores it, revises if needed",
    "summarizer": "Keeps a running conversation summary as memory",
}
EXAMPLES = [
    "What causes acne?",
    "Apa saja gejala bronkitis?",
    "Bagaimana cara mengobatinya?",
    "How is malaria treated?",
    "Rangkum percakapan kita",
]


# ------------------------------------------------------------------ state
@st.cache_resource(show_spinner="Loading Medical Book index...")
def load_system() -> DoctorAgentSystem:
    return DoctorAgentSystem()


def init_state() -> None:
    st.session_state.setdefault("memory", Memory())
    st.session_state.setdefault("messages", [])  # {"role", "content", "result"}
    st.session_state.setdefault("total_cost", 0.0)
    st.session_state.setdefault("total_tokens", 0)


def reset() -> None:
    for k in ("memory", "messages", "total_cost", "total_tokens"):
        st.session_state.pop(k, None)


# ------------------------------------------------------------------ rendering helpers
def confidence_badges(r: TurnResult) -> str:
    badges = []
    if r.confidence is not None:
        color = "green" if r.confidence >= ACCEPT_THRESHOLD else "orange" if not r.escalated else "red"
        badges.append(f":{color}-badge[Confidence {r.confidence:.0%}]")
    if r.escalated:
        badges.append(":red-badge[Escalated]")
    if r.revised:
        badges.append(":violet-badge[Revised by Evaluator]")
    if r.attempts > 1:
        badges.append(f":blue-badge[Re-queried ×{r.attempts - 1}]")
    badges.append(f":gray-badge[{r.intent.replace('_', ' ')}]")
    tin, tout = r.tokens
    badges.append(f":gray-badge[{r.seconds:.1f}s · {tin + tout:,} tokens · ${r.cost:.4f}]")
    return " ".join(badges)


def render_details(r: TurnResult) -> None:
    st.markdown(confidence_badges(r))
    if r.evaluation is not None:
        ev = r.evaluation
        with st.expander(f"🔍 Evaluator feedback — verdict: **{ev.verdict}**"):
            cols = st.columns(4)
            for col, (label, val) in zip(cols, [("Faithfulness", ev.faithfulness), ("Completeness", ev.completeness),
                                               ("Relevance", ev.relevance), ("Tone", ev.tone)]):
                col.metric(label, f"{val:.2f}")
            st.write(ev.feedback)
            if ev.unsupported_claims:
                st.markdown("**Unsupported claims found in the draft** (removed or flagged):")
                for c in ev.unsupported_claims:
                    st.markdown(f"- {c}")
            if ev.missing_points:
                st.markdown("**Missing points:**")
                for c in ev.missing_points:
                    st.markdown(f"- {c}")
    if r.sources:
        with st.expander(f"📚 Sources from the Medical Book ({len(r.sources)})"):
            for n, h in enumerate(r.sources, 1):
                c = h.chunk
                page = c["book_page"] or f"PDF {c['pdf_page']}"
                st.markdown(f"**[{n}] {c['entry']} — {c['section']}** · page {page} · similarity {h.dense_sim:.2f}")
                st.caption(c["text"][:400] + ("…" if len(c["text"]) > 400 else ""))
    with st.expander(f"🧭 Agent trace ({len(r.steps)} steps)"):
        st.dataframe(
            [{"agent": f"{AGENT_ICON.get(s.agent, '')} {s.agent}", "action": s.action, "model": s.model,
              "time (s)": round(s.seconds, 2), "tokens in/out": f"{s.input_tokens}/{s.output_tokens}",
              "cost ($)": round(s.cost, 5), "detail": s.detail} for s in r.steps],
            hide_index=True, width="stretch",
        )


def sidebar() -> None:
    with st.sidebar:
        st.header("🩺 Doctor Agent")
        st.caption("Multi-agent RAG assistant over the **Medical Book** "
                   "(Gale Encyclopedia of Medicine, vol. 1 — topics A–B).")
        st.subheader("Agents")
        for name, model in MODELS.items():
            st.markdown(f"{AGENT_ICON[name]} **{name.capitalize()}** · `{model}`")
            st.caption(AGENT_ROLE[name])
        st.subheader("Session")
        c1, c2 = st.columns(2)
        c1.metric("Questions", sum(m["role"] == "user" for m in st.session_state.messages))
        c2.metric("Cost", f"${st.session_state.total_cost:.3f}")
        st.caption(f"{st.session_state.total_tokens:,} tokens used")
        st.subheader("Memory (Summarizer)")
        st.caption(st.session_state.memory.summary or "No summary yet — created every 3 turns.")
        st.button("🗑️ Clear conversation", on_click=reset, width="stretch")
        st.caption("⚠️ Educational tool, not a substitute for professional medical advice.")


# ------------------------------------------------------------------ main
init_state()
sidebar()

st.title("🩺 Doctor Agent")
st.caption("Ask a medical question in English or Indonesian. Four agents collaborate: "
           "Planner → RAG → Evaluator → Summarizer.")

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.error("ANTHROPIC_API_KEY is not set. Copy `.env.example` to `.env` and add your key, then restart.")
    st.stop()

system = load_system()

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🩺" if m["role"] == "assistant" else None):
        st.markdown(m["content"])
        if m.get("result"):
            render_details(m["result"])

if not st.session_state.messages:
    st.markdown("**Try one of these:**")
    cols = st.columns(len(EXAMPLES))
    for col, ex in zip(cols, EXAMPLES):
        if col.button(ex, width="stretch"):
            st.session_state.pending = ex
            st.rerun()

prompt = st.chat_input("Ask about a disease, symptom, test or treatment...") or st.session_state.pop("pending", None)
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🩺"):
        with st.status("Agents are working...", expanded=True) as status:
            def on_step(s: Step) -> None:
                st.write(f"{AGENT_ICON.get(s.agent, '')} **{s.agent.capitalize()}** — {s.action}")

            try:
                result = system.ask(prompt, st.session_state.memory, on_step=on_step)
            except Exception as e:  # show API / network errors instead of crashing the app
                status.update(label="Something went wrong", state="error")
                st.error(f"{type(e).__name__}: {e}")
                st.session_state.messages.pop()
                st.stop()
            status.update(label=f"Done in {result.seconds:.1f}s", state="complete", expanded=False)
        st.markdown(result.answer)
        render_details(result)

    st.session_state.messages.append({"role": "assistant", "content": result.answer, "result": result})
    st.session_state.total_cost += result.cost
    st.session_state.total_tokens += sum(result.tokens)
    st.rerun()  # refresh sidebar counters
