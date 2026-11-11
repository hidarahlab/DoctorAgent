import os

import streamlit as st

from config import ACCEPT_THRESHOLD, MODELS
from doctor_agent.memory import Memory
from doctor_agent.orchestrator import DoctorAgentSystem, TurnResult

st.set_page_config(page_title="Doctor Agent", page_icon="🩺", layout="wide")

st.html("""<style>
[data-testid="stAppDeployButton"], [data-testid="stStatusWidget"],
[data-testid="stMainMenuItem-rerun"], [data-testid="stMainMenuItem-autoRerun"],
[data-testid="stMainMenuItem-print"], [data-testid="stMainMenuItem-recordScreencast"],
[data-testid="stMainMenuDivider"], [data-testid="stMainMenuList"] ~ div { display: none !important; }
[data-testid="stChatInput"] > div { background-color: #FFFFFF !important; }  /* white chat box, keep border */
</style>""")

AGENT_ICON = {"planner": "🧭", "rag": "📚", "evaluator": "🔍", "summarizer": "📝", "system": "⚙️"}
AGENT_LABEL = {"planner": "Planner", "rag": "RAG", "evaluator": "Evaluator", "summarizer": "Summarizer"}


@st.cache_resource(show_spinner="Loading Medical Book index...")
def load_system() -> DoctorAgentSystem:
    return DoctorAgentSystem()


def init_state() -> None:
    st.session_state.setdefault("memory", Memory())
    st.session_state.setdefault("messages", [])


def reset() -> None:
    for k in ("memory", "messages"):
        st.session_state.pop(k, None)



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
    return " ".join(badges)


def render_details(r: TurnResult) -> None:
    badges = confidence_badges(r)
    if badges:
        st.markdown(badges)
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
        st.caption("Multi-agent RAG assistant")
        st.subheader("Agents")
        rows = "".join(
            f'<div style="margin-bottom:5px">&gt; <b>{name.capitalize()}</b> · <code>{model}</code></div>'
            for name, model in MODELS.items()
        )
        st.markdown(rows, unsafe_allow_html=True)
        st.subheader("Memory (Summarizer)")
        st.caption(st.session_state.memory.summary or "No summary yet — created every 3 turns.")
        st.button("🗑️ Clear conversation", on_click=reset, width="stretch")

init_state()
sidebar()

st.title("🩺 Doctor Agent")
st.caption("Ask a medical question")

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.error("ANTHROPIC_API_KEY is not set. Copy `.env.example` to `.env` and add your key, then restart.")
    st.stop()

system = load_system()

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🩺" if m["role"] == "assistant" else None):
        st.markdown(m["content"])
        if m.get("result"):
            render_details(m["result"])

prompt = st.chat_input("Try chat")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🩺"):
        progress = st.empty()
        try:
            result = system.ask(prompt, st.session_state.memory,
                                on_progress=lambda agent: progress.caption(f"⏳ {AGENT_LABEL[agent]} berjalan..."))
        except Exception as e:
            progress.empty()
            st.error(f"{type(e).__name__}: {e}")
            st.session_state.messages.pop()
            st.stop()
        progress.empty()
        st.markdown(result.answer)
        render_details(result)

    st.session_state.messages.append({"role": "assistant", "content": result.answer, "result": result})
    st.rerun()
