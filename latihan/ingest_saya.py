#langkah 5 kerangka file: import, konstanta, dan section (ingestion gale encyclopedia of medicine)

from __future__ import annotations 

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "data" / "medical_book.pdf"
OUT_PATH = ROOT / "data" / "chunks_saya.json"

FIRST_CONTENT_PAGE = 13     # 0-BASED; pages before this are front matter
CHUNK_CHARS = 1200          # target chunk size
OVERLAP_CHARS = 200         # overlap between consecutive sub-chunks

@dataclass
class Section:
    entry: str
    section: str
    pdf_page: int
    book_page: str
    lines: list[str] = field(default_factory=list)

#langkah 6
def _block_kind(spans: list[dict]) -> str:
    s0 = spans[0]
    size, font, text = round(s0["size"], 1), s0["font"], s0["text"].strip()
    if size == 15.0 and "Bold" in font:
        return "entry"
    if size == 12.5 and text.upper().startswith("KEY TERMS"):
        return "keyterms_header"
    if size == 12.0:
        return "crossref"
    if size == 11.0 and "Bold" in font:
        return "section"
    if size == 10.0 and font == "Optima-Bold" and text == "Resources":
        return "resources"
    if size == 10.0 and font == "Optima-Bold":
        return "keyterm" # "Term —definition" inside the KEY TERMS box
    if size <= 9.0:
        return "small" # bibliography / captions
    return "body"

#langkah 7
def _page_blocks(page: pymupdf.Page):
    """Yield (kind, text_lines) for content blocks in reading order (2 columns)."""
    w, h = page.rect.width, page.rect.height
    blocks = []
    for b in page.get_text("dict")["blocks"]:
        if "lines" not in b:
            continue
        x0, y0, x1, y1 = b["bbox"]
        if y0 > h * 0.91 or x1 < 60 or x0 > w - 60: # footer / margin header
            continue
        spans = [s for l in b["lines"] for s in l["spans"] if s["text"].strip()]
        if not spans:
            continue
        lines = ["".join(s["text"] for s in l["spans"]) for l in b["lines"]]
        col = 0 if x0 < w / 2 - 10 else 1
        kind = _block_kind(spans)
        if kind in ("entry", "section"):
            # Sometimes a heading and the paragraph after it share one block:
            # keep only the heading-sized lines as the heading, the rest is classified again.
            head = round(spans[0]["size"], 1)
            sizes = [next((round(s["size"], 1) for s in l["spans"] if s["text"].strip()), head)
                for l in b["lines"]]
            n = next((i for i, sz in enumerate(sizes) if sz != head), len(lines))
            if n < len(lines):
                rest = [s for l in b["lines"][n:] for s in l["spans"] if s["text"].strip()]
                blocks.append((col, y0, kind, lines[:n]))
                blocks.append((col, y0 + 0.1, _block_kind(rest), lines[n:]))
                continue
        blocks.append((col, y0, kind, lines))
    blocks.sort(key=lambda t: (t[0], t[1]))
    for _, _, kind, lines in blocks:
        yield kind, lines

#langkah 8
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

#langkah 9
# def _book_page(page: pymupdf.Page) -> str:
#     for b in page.get_text("dict")["blocks"]:
#         for l in b.get("lines", []):
#             for s in l["spans"]:
#                 if round(s["size"], 1) == 10.1 and s["text"].strip().isdigit():
#                     return s["text"].strip()
#     return ""

# def parse_sections(pdf_path: Path = PDF_PATH):
#     """VERSI 1 (sederhana): hanya mengenali entry, section, dan body."""
#     doc = pymupdf.open(pdf_path)
#     sections: list[Section] = []
#     cur: Section | None = None
#     entry = ""
    
#     for pno in range(FIRST_CONTENT_PAGE, doc.page_count):
#         page = doc[pno]
#         bp = _book_page(page)
#         for kind, lines in _page_blocks(page):
#             text = _join_lines(lines)
#             if kind == "entry":
#                 entry = text
#                 cur = None
#             elif kind == "section":
#                 cur = Section(entry, text, pno + 1, bp)
#                 sections.append(cur)
#             elif kind == "body" and cur is not None:
#                 cur.lines.append(text)
#     return [s for s in sections if s.lines], {}

#langkah 10
def _book_page(page: pymupdf.Page) -> str:
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if round(s["size"], 1) == 10.1 and s["text"].strip().isdigit():
                    return s["text"].strip()
    return ""

def parse_sections(pdf_path: Path = PDF_PATH):
    doc = pymupdf.open(pdf_path)
    sections: list[Section] = []
    aliases: dict[str, str] = {}
    cur: Section | None = None
    keyterms: Section | None = None
    entry, mode = "", "body" 
    pending_title: list[str] = []
    # mode: body (simpan teks) | skip (abaikan bibliografi)

    def start(sec_name: str, pno: int, bp: str) -> Section:
        s = Section(entry, sec_name, pno + 1, bp)
        sections.append(s)
        return s

    crossref_buf: list[str] = []
    for pno in range(FIRST_CONTENT_PAGE, doc.page_count):
        page = doc[pno]
        bp = _book_page(page)
        for kind, lines in _page_blocks(page):
            text = _join_lines(lines)
            if kind != "entry" and pending_title:
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

#langkah 11
def _split(text: str, size: int = CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    if len(text) <= size:
        return [text]
    sents = []
    for s in re.split(r"(?<=[.!?])\s+|\s(?=• )", text):
        while len(s) > size: # sentences and bullet items
        # very long run-on: hard word split
            cut = s.rfind(" ", 0, size)
            cut = cut if cut > 0 else size
            sents.append(s[:cut]); s = s[cut:].strip()
        sents.append(s)
    chunks, buf = [], ""
    for s in sents:
        if buf and len(buf) + len(s) > size:
            chunks.append(buf.strip())
            buf = buf[-overlap:].split(" ", 1)[-1] + " " # overlap on word boundary
        buf += s + " "
    if buf.strip():
        chunks.append(buf.strip())
    return chunks

#langkah 12
def build_chunks(pdf_path: Path = PDF_PATH) -> tuple[list[dict], dict]:
    sections, aliases = parse_sections(pdf_path)
    chunks = []
    for s in sections:
        body = _join_lines(s.lines) if s.section != "Key terms" else "\n".join(s.lines)
        for part in _split(body):
            chunks.append({
                "id": f"{len(chunks):05d}",
                "entry": s.entry,
                "section": s.section,
                "pdf_page": s.pdf_page,
                "book_page": s.book_page,
                "text": part,
            })
    return chunks, aliases
if __name__ == "__main__":
    chunks, aliases = build_chunks()
    OUT_PATH.write_text(json.dumps({"chunks": chunks, "aliases": aliases}, indent=1, ensure_ascii=False))
    entries = sorted({c["entry"] for c in chunks})
    print(f"{len(chunks)} chunks, {len(entries)} entries, {len(aliases)} aliases -> {OUT_PATH}", file=sys.stderr)

    #ouput langkah 12: 3319 chunks, 282 entries, 268 aliases -> /Users/ibkindonesia/Documents/Project/Learning/DoctorAgent/data/chunks_saya.json