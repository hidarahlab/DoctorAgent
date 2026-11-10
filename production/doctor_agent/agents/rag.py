"""RAG Agent - retrieves passages from the Medical Book and writes a grounded,
cited answer.  It is told to use ONLY the passages, so anything it says can
be traced back to a page of the book (and checked by the Evaluator)."""
from __future__ import annotations

from dataclasses import dataclass

from config import TOP_K
from doctor_agent.llm import LLM, Usage
from doctor_agent.memory import Memory
from doctor_agent.retriever import Hit, HybridRetriever

SYSTEM = """You are a careful medical information assistant. You answer ONLY with information found in
the numbered excerpts from the "Medical Book" (Gale Encyclopedia of Medicine) given to you.

Rules:
1. Use only the excerpts. Do not add facts from your own knowledge, even if you are sure they are true.
2. Cite the excerpt numbers after each claim, like [1] or [2][3].
3. If the excerpts do not contain the answer, say plainly that the Medical Book does not cover it
   (you may mention what related information the excerpts do contain). Never guess.
4. Write in {language}. Translate the content faithfully; keep medical terms understandable.
5. Be clear, calm and empathetic. At most ~200 words; short paragraphs or bullet points.
6. When you describe treatments, drugs or dosages, end with one short sentence advising the user
   to consult a doctor for their personal situation."""


def format_context(hits: list[Hit]) -> str:
    blocks = []
    for n, h in enumerate(hits, 1):
        c = h.chunk
        page = f"p. {c['book_page']}" if c["book_page"] else f"PDF p. {c['pdf_page']}"
        blocks.append(f"[{n}] {c['entry']} - {c['section']} ({page})\n{c['text']}")
    return "\n\n".join(blocks)


@dataclass
class RagResult:
    answer: str
    hits: list[Hit]
    query: str
    usage: Usage

    @property
    def top_similarity(self) -> float:
        return max((h.dense_sim for h in self.hits), default=0.0)


class RAGAgent:
    name = "rag"

    def __init__(self, llm: LLM, retriever: HybridRetriever):
        self.llm = llm
        self.retriever = retriever

    def run(self, question: str, search_query: str, language: str, memory: Memory,
            feedback: str = "") -> RagResult:
        hits = self.retriever.search(search_query or question, TOP_K)
        prompt = (
            f"{memory.context()}\n\n"
            f"Excerpts from the Medical Book:\n{format_context(hits)}\n\n"
            + (f"A reviewer found problems with a previous attempt - avoid them:\n{feedback}\n\n" if feedback else "")
            + f"User question: {question}"
        )
        answer, usage = self.llm.text(self.name, SYSTEM.format(language=language),
                                      [{"role": "user", "content": prompt}])
        return RagResult(answer, hits, search_query, usage)
