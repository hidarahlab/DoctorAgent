"""Step 1 - Ingestion: turn the Medical Book PDF into structure-aware chunks.

The book (Gale Encyclopedia of Medicine, vol. 1, A-B) has a very regular layout:
    ENTRY TITLE (15pt bold)  ->  Section heading (11pt bold)  ->  body text
so instead of cutting the text blindly every N characters we read the font
size/weight of every text block and cut along the book's own structure.
Every chunk therefore knows which entry + section + page it came from, which
we later show to the user as a citation.

Run:  python -m doctor_agent.ingest
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from config import CHUNK_CHARS, CHUNKS_PATH, FIRST_CONTENT_PAGE, OVERLAP_CHARS, PDF_PATH


@dataclass
class Section:
    entry: str
    section: str
    pdf_page: int
    book_page: str
    lines: list[str] = field(default_factory=list)


def _block_kind(spans: list[dict]) -> str:
    """Classify a text block by the font of its first span."""
    s0 = spans[0]
    size, font, text = round(s0["size"], 1), s0["font"], s0["text"].strip()
    if size == 15.0 and "Bold" in font:
        return "entry"
    if size == 12.5 and text.upper().startswith("KEY TERMS"):
        return "keyterms_header"
    if size == 12.0:
        return "crossref"  # "Abrasions see Wounds"
    if size == 11.0 and "Bold" in font:
        return "section"
    if size == 10.0 and font == "Optima-Bold" and text == "Resources":
        return "resources"
    if size == 10.0 and font == "Optima-Bold":
        return "keyterm"  # "Term - definition" inside the KEY TERMS box
    if size <= 9.0:
        return "small"  # bibliography / captions
    return "body"


def _page_blocks(page: pymupdf.Page):
    """Yield (kind, lines) for content blocks in reading order (2 columns)."""
    w, h = page.rect.width, page.rect.height
    blocks = []
    for b in page.get_text("dict")["blocks"]:
        if "lines" not in b:
            continue
        x0, y0, x1, _ = b["bbox"]
        if y0 > h * 0.91 or x1 < 60 or x0 > w - 60:  # footer / margin header
            continue
        spans = [s for l in b["lines"] for s in l["spans"] if s["text"].strip()]
        if not spans:
            continue
        lines = ["".join(s["text"] for s in l["spans"]) for l in b["lines"]]
        col = 0 if x0 < w / 2 - 10 else 1
        kind = _block_kind(spans)
        if kind in ("entry", "section"):
            # A heading and the paragraph after it sometimes share one block:
            # keep only the heading-sized lines as heading, re-classify the rest.
            head = round(spans[0]["size"], 1)
            sizes = [
                next((round(s["size"], 1) for s in l["spans"] if s["text"].strip()), head)
                for l in b["lines"]
            ]
            n = next((i for i, sz in enumerate(sizes) if sz != head), len(lines))
            if n < len(lines):
                rest = [s for l in b["lines"][n:] for s in l["spans"] if s["text"].strip()]
                blocks.append((col, y0, kind, lines[:n]))
                blocks.append((col, y0 + 0.1, _block_kind(rest), lines[n:]))
                continue
        blocks.append((col, y0, kind, lines))
    blocks.sort(key=lambda t: (t[0], t[1]))  # left column first, then top-down
    for _, _, kind, lines in blocks:
        yield kind, lines


def _join_lines(lines: list[str]) -> str:
    """Join PDF lines, repairing end-of-line hyphenation ("vacu-" + "um")."""
    out = ""
    for ln in lines:
        ln = re.sub(r"\s+", " ", ln).strip()
        if not ln:
            continue
        if out.endswith("-") and ln[:1].islower():
            out = out[:-1] + ln
        else:
            out = f"{out} {ln}" if out else ln
    return out


def _book_page(page: pymupdf.Page) -> str:
    """The printed page number (10.1pt digits) - nicer to cite than the PDF index."""
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if round(s["size"], 1) == 10.1 and s["text"].strip().isdigit():
                    return s["text"].strip()
    return ""


def parse_sections(pdf_path: Path = PDF_PATH) -> tuple[list[Section], dict[str, str]]:
    doc = pymupdf.open(pdf_path)
    sections: list[Section] = []
    aliases: dict[str, str] = {}
    cur: Section | None = None
    keyterms: Section | None = None
    entry, mode = "", "body"  # mode: body (keep text) | skip (bibliography)
    pending_title: list[str] = []
    crossref_buf: list[str] = []

    def start(sec_name: str, pno: int, bp: str) -> Section:
        s = Section(entry, sec_name, pno + 1, bp)
        sections.append(s)
        return s

    for pno in range(FIRST_CONTENT_PAGE, doc.page_count):
        page = doc[pno]
        bp = _book_page(page)
        for kind, lines in _page_blocks(page):
            text = _join_lines(lines)
            if kind != "entry" and pending_title:
                # entry titles can wrap over several blocks - close the title now
                entry = " ".join(pending_title)
                pending_title = []
                cur, keyterms, mode = start("Overview", pno, bp), None, "body"
            if kind == "crossref":
                crossref_buf.append(text)
                continue
            if kind == "entry":
                pending_title.append(text)
                continue
            if kind == "section":
                cur, mode = start(text, pno, bp), "body"
            elif kind == "resources":
                mode = "skip"
            elif kind == "keyterms_header":
                keyterms = keyterms or start("Key terms", pno, bp)
            elif kind == "keyterm":
                if entry:
                    keyterms = keyterms or start("Key terms", pno, bp)
                    keyterms.lines.append(text)
            elif kind == "body" and mode == "body" and cur is not None:
                cur.lines.append(text)

    # Cross references: "Abrasions see Wounds Abruptio placentae see Placental abruption"
    joined = " ".join(crossref_buf)
    for m in re.finditer(r"(.+?)\s+see\s+(.+?)(?=\s+[A-Z][\w,'’\- ]*?\s+see\s+|$)", joined):
        aliases[m.group(1).strip()] = m.group(2).strip()
    return [s for s in sections if s.lines], aliases


def split_text(text: str, size: int = CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    """Split long sections on sentence boundaries, with a small word-aligned overlap."""
    if len(text) <= size:
        return [text]
    sents = []
    for s in re.split(r"(?<=[.!?])\s+|\s(?=• )", text):  # sentences and bullet items
        while len(s) > size:  # very long run-on: hard split on a word boundary
            cut = s.rfind(" ", 0, size)
            cut = cut if cut > 0 else size
            sents.append(s[:cut])
            s = s[cut:].strip()
        sents.append(s)
    chunks, buf = [], ""
    for s in sents:
        if buf and len(buf) + len(s) > size:
            chunks.append(buf.strip())
            buf = buf[-overlap:].split(" ", 1)[-1] + " "  # overlap on word boundary
        buf += s + " "
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def build_chunks(pdf_path: Path = PDF_PATH) -> tuple[list[dict], dict[str, str]]:
    sections, aliases = parse_sections(pdf_path)
    chunks = []
    for s in sections:
        body = _join_lines(s.lines) if s.section != "Key terms" else "\n".join(s.lines)
        for part in split_text(body):
            chunks.append({
                "id": f"{len(chunks):05d}",
                "entry": s.entry,
                "section": s.section,
                "pdf_page": s.pdf_page,
                "book_page": s.book_page,
                "text": part,
            })
    return chunks, aliases


def main() -> None:
    chunks, aliases = build_chunks()
    CHUNKS_PATH.write_text(json.dumps({"chunks": chunks, "aliases": aliases}, indent=1, ensure_ascii=False))
    entries = {c["entry"] for c in chunks}
    print(f"{len(chunks)} chunks, {len(entries)} entries, {len(aliases)} aliases -> {CHUNKS_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
