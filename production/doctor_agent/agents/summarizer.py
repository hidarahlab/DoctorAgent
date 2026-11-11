"""Summarizer Agent - condenses the conversation.

* update():   every N turns, folds the newest turns into a running summary
              (the bot's long-term memory, injected into later prompts).
* for_user(): when the user asks "summarise our chat", writes a readable recap."""
from __future__ import annotations

from doctor_agent.llm import LLM, Usage
from doctor_agent.memory import Memory

MEMORY_SYSTEM = """You maintain the memory of a medical Q&A chat. Merge the previous summary and the new
turns into ONE updated summary of at most 120 words, in English. Keep: topics/diseases discussed,
key facts already given, personal context the user shared (age, symptoms, conditions), and open
questions. Drop greetings and filler. Output only the summary text."""

USER_SYSTEM = """Write a short recap of this medical Q&A conversation for the user, in {language}.
Use 3-6 bullet points covering the topics asked about and the main information given.
Do not add new medical facts. Output only the recap."""


def _transcript(memory: Memory, turns) -> str:
    lines = [f"User: {t.user}\nAssistant: {t.assistant}" for t in turns]
    prev = memory.summary or "(none)"
    return f"Previous summary:\n{prev}\n\nNew turns:\n" + "\n\n".join(lines)


class SummarizerAgent:
    name = "summarizer"

    def __init__(self, llm: LLM):
        self.llm = llm

    def update(self, memory: Memory) -> Usage:
        text, usage = self.llm.text(self.name, MEMORY_SYSTEM,
                                    [{"role": "user", "content": _transcript(memory, memory.unsummarized())}])
        memory.summary = text
        memory.turns_since_summary = 0
        return usage

    def for_user(self, memory: Memory, language: str) -> tuple[str, Usage]:
        if not memory.turns:
            return "", None
        content = _transcript(memory, memory.unsummarized() or memory.recent())
        return self.llm.text(self.name, USER_SYSTEM.format(language=language),
                             [{"role": "user", "content": content}])
