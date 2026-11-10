import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = ROOT / "data" / "medical_book.pdf"
OUT_PATH = ROOT / "data" / "chunks_saya.json"

data = json.load(open(OUT_PATH))
chunks, aliases = data["chunks"], data["aliases"]
panjang = [len(c["text"]) for c in chunks]
entri = {c["entry"] for c in chunks}

print("jumlah chunk :", len(chunks))
print("jumlah entri :", len(entri))
print("jumlah alias :", len(aliases))
print("panjang maks :", max(panjang))
print("entry kosong :", sum(1 for c in chunks if not c["entry"]))
print("ada footer? :", sum(1 for c in chunks if "GALE ENCYCLOPEDIA" in c["text"]))
print("ada PERIODICALS?:", sum(1 for c in chunks if "PERIODICALS" in c["text"]))

asli = json.load(open(ROOT / "data" / "chunks.json"))
print("sama dengan versi referensi?", asli == data)