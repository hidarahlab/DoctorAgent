"""Conversation memory: a running summary (written by the Summarizer agent)
plus the last few raw turns.  This keeps prompts short no matter how long
the chat gets, while still letting the bot resolve follow-ups like
"and how is it treated?"."""
from __future__ import annotations

from dataclasses import dataclass, field

from config import RECENT_TURNS


@dataclass
class Turn:
    user: str
    assistant: str


@dataclass
class Memory:
    summary: str = ""
    turns: list[Turn] = field(default_factory=list)
    turns_since_summary: int = 0

    def add(self, user: str, assistant: str) -> None:
        self.turns.append(Turn(user, assistant))
        self.turns_since_summary += 1

    def recent(self, n: int = RECENT_TURNS) -> list[Turn]:
        return self.turns[-n:]

    def unsummarized(self) -> list[Turn]:
        return self.turns[-self.turns_since_summary:] if self.turns_since_summary else []

    def context(self, n: int = RECENT_TURNS) -> str:
        """Plain-text block injected into agent prompts."""
        parts = []
        if self.summary:
            parts.append(f"Conversation summary so far:\n{self.summary}")
        recent = self.recent(n)
        if recent:
            lines = [f"User: {t.user}\nAssistant: {t.assistant}" for t in recent]
            parts.append("Most recent turns:\n" + "\n\n".join(lines))
        return "\n\n".join(parts) or "(no previous conversation)"
