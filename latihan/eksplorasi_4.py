# Langkah 4: lihat posisi blok (bounding box)
# Tujuan: tahu layout halaman (kolom, header, footer) supaya
# urutan baca benar & noise bisa dibuang berdasarkan posisi

from pathlib import Path   # library bawaan Python buat ngolah path file/folder
import pymupdf             # library buat baca PDF

pdfPath = Path(__file__).resolve().parent.parent / "data" / "medical_book.pdf"
doc = pymupdf.open(pdfPath)
page = doc[19]                                                  # halaman ke-20
print("ukuran halaman:", page.rect.width, "x", page.rect.height)  # lebar x tinggi (satuan point)

for block in page.get_text("dict")["blocks"]:
    if "lines" not in block:        # block gambar → lewati
        continue

    # bbox = kotak pembatas block: (x0, y0) pojok kiri-atas, (x1, y1) pojok kanan-bawah
    # titik (0,0) ada di pojok KIRI-ATAS halaman, y makin besar = makin ke bawah
    x0, y0, x1, y1 = [round(v) for v in block["bbox"]]   # dibulatkan biar enak dibaca

    # list comprehension bertingkat: ambil semua span dari semua line di block ini,
    # tapi hanya yang teksnya tidak kosong
    spans = [s for l in block["lines"] for s in l["spans"] if s["text"].strip()]
    if not spans:                   # block isinya spasi doang → lewati
        continue

    teks = " ".join(s["text"] for s in spans)   # gabung semua span jadi satu string

    # :>3 → rata kanan, lebar 3 karakter (biar kolom angkanya sejajar)
    print(f"x0={x0:>3} y0={y0:>3} x1={x1:>3} | {teks[:55]}")

#output:
# ukuran halaman: 603.0 x 789.6000366210938
# x0= 87 y0=230 x1=143 | Description
# x0= 69 y0=248 x1=297 | Many unexpected and fascinating events occur dur- ing t
# x0= 87 y0=360 x1=192 | Causes and symptoms
# x0= 69 y0=379 x1=297 | There are many causes for  birth defects  that still re
# x0= 87 y0=455 x1=133 | Diagnosis
# x0= 69 y0=474 x1=297 | At birth, the problem is obvious, because the base of t
# x0= 87 y0=562 x1=136 | Treatment
# x0= 69 y0=580 x1=297 | Abdominal wall defects are effectively treated with sur
# x0= 87 y0=668 x1=133 | Prognosis
# x0= 69 y0=687 x1=297 | If there are no other defects, the prognosis after sur-
# x0=147 y0= 74 x1=220 | KEY TERMS
# x0= 75 y0=100 x1=291 | Hernia —Movement of a structure into a place it does no
# x0= 75 y0=128 x1=291 | Umbilical —Referring to the opening in the abdominal wa
# x0= 75 y0=168 x1=291 | Viscera —Any of the body’s organs located in the chest 
# x0=315 y0= 61 x1=543 | 10% of those with more severe or additional abnormali- 
# x0=333 y0=174 x1=384 | Prevention
# x0=315 y0=193 x1=543 | Some, but by no means all, birth defects are pre- venta
# x0=315 y0=268 x1=359 | Resources
# x0=315 y0=286 x1=538 | PERIODICALS Dunn, J. C., and E. W. Fonkalsrud. “Improve
# x0=443 y0=364 x1=543 | J. Ricker Polsdorfer, MD
# x0=315 y0=387 x1=527 | Abnormal heart rhythms  see  Arrhythmias ABO blood typi
# x0=346 y0=551 x1=491 | Abortion, partial birth
# x0=333 y0=573 x1=382 | Definition
# x0=315 y0=591 x1=543 | Partial birth abortion is a method of late-term abor- t
# x0=333 y0=668 x1=372 | Purpose
# x0=315 y0=687 x1=543 | Partial birth abortion, or D&X, is performed to end a p
# x0= 69 y0=730 x1=543 | GALE ENCYCLOPEDIA OF MEDICINE 2 6
# x0= 43 y0= 62 x1= 53 | Abortion, partial birth