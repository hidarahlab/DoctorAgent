# Langkah 2: lihat font setiap potongan teks (span)
# Tujuan: cari pola ukuran/jenis font buat ngenalin judul artikel & subjudul,
# supaya nanti chunking bisa per topik, bukan potong buta per N karakter

from pathlib import Path   # library bawaan Python buat ngolah path file/folder
import pymupdf             # library buat baca PDF

pdfPath = Path(__file__).resolve().parent.parent / "data" / "medical_book.pdf"

doc = pymupdf.open(pdfPath)   # buka PDF
page = doc[19]                # halaman ke-20 (index mulai dari 0)

# get_text("dict") → teks dalam bentuk struktur bertingkat, lengkap dengan info font
# hierarkinya: page → blocks → lines → spans
#   block = satu paragraf/area (bisa juga berisi gambar)
#   line  = satu baris dalam block
#   span  = potongan teks dalam satu baris yang font-nya SAMA
data = page.get_text("dict")

for block in data["blocks"]:
    if "lines" not in block:      # block gambar nggak punya "lines" → lewati
        continue
    for line in block["lines"]:
        for span in line["spans"]:
            teks = span["text"].strip()    # buang spasi di awal/akhir
            if teks:                       # skip span kosong
                # cetak: ukuran font (dibulatkan 1 desimal), nama font, 50 karakter pertama
                print(round(span["size"], 1), span["font"], "|", teks[:50])

#output:
# 11.0 Optima-Bold | Description
# 10.0 Times-Roman | Many unexpected and fascinating events occur dur-
# 10.0 Times-Roman | ing the development of a fetus inside the womb. Th
# 10.0 Times-Roman | stomach and intestines begin development outside t
# 10.0 Times-Roman | baby’s abdomen and only later does the abdominal w
# 10.0 Times-Roman | enclose them. Occasionally, either the umbilical o
# 10.0 Times-Roman | is too large, or it develops improperly, allowing 
# 10.0 Times-Roman | els or stomach to remain outside or squeeze throug
# 10.0 Times-Roman | abdominal wall.
# 11.0 Optima-Bold | Causes and symptoms
# 10.0 Times-Roman | There are many causes for
# 10.0 Times-Bold | birth defects
# 10.0 Times-Roman | that still
# 10.0 Times-Roman | remain unclear. Presently, the cause(s) of abdomin
# 10.0 Times-Roman | defects is unknown, and any symptoms the mother ma
# 10.0 Times-Roman | have to indicate that the defects are present in t
# 10.0 Times-Roman | are nondescript.
# 11.0 Optima-Bold | Diagnosis
# 10.0 Times-Roman | At birth, the problem is obvious, because the base
# 10.0 Times-Roman | the umbilical cord at the navel will bulge or, in 
# 10.0 Times-Roman | cases, contain viscera (internal organs). Before b
# 10.0 Times-Roman | ultrasound examination may detect the problem. It 
# 10.0 Times-Roman | always necessary in children with one birth defect
# 10.0 Times-Roman | for others, because birth defects are usually mult
# 11.0 Optima-Bold | Treatment
# 10.0 Times-Roman | Abdominal wall defects are effectively treated wit
# 10.0 Times-Roman | surgical repair. Unless there are accompanying ano
# 10.0 Times-Roman | alies, the surgical procedure is not overly compli
# 10.0 Times-Roman | The organs are normal, just misplaced. However, if
# 10.0 Times-Roman | defect is large, it may be difficult to fit all th
# 10.0 Times-Roman | the small abdominal cavity.
# 11.0 Optima-Bold | Prognosis
# 10.0 Times-Roman | If there are no other defects, the prognosis after
# 10.0 Times-Roman | gical repair of this condition is relatively good.
# 12.5 Optima-Bold | KEY TERMS
# 10.0 Optima-Bold | Hernia
# 10.0 Optima | —Movement of a structure into a place it
# 10.0 Optima | does not belong.
# 10.0 Optima-Bold | Umbilical
# 10.0 Optima | —Referring to the opening in the
# 10.0 Optima | abdominal wall where the blood vessels from the
# 10.0 Optima | placenta enter.
# 10.0 Optima-Bold | Viscera
# 10.0 Optima | —Any of the body’s organs located in the
# 10.0 Optima | chest or abdomen.
# 10.0 Times-Roman | 10% of those with more severe or additional abnorm
# 10.0 Times-Roman | ties die from it. The organs themselves are fully 
# 10.0 Times-Roman | al; the difficulty lies in fitting them inside the
# 10.0 Times-Roman | The condition is, in fact, a
# 10.0 Times-Bold | hernia
# 10.0 Times-Roman | requiring only replace-
# 10.0 Times-Roman | ment and strengthening of the passageway through
# 10.0 Times-Roman | which it occurred. After surgery, increased pressu
# 10.0 Times-Roman | the stretched abdomen can compromise the function 
# 10.0 Times-Roman | the organs inside.
# 11.0 Optima-Bold | Prevention
# 10.0 Times-Roman | Some, but by no means all, birth defects are pre-
# 10.0 Times-Roman | ventable by early and attentive prenatal care, goo
# 10.0 Times-Bold | nutri-
# 10.0 Times-Bold | tion
# 10.0 Times-Roman | , supplemental
# 10.0 Times-Bold | vitamins
# 10.0 Times-Roman | , diligent avoidance of all
# 10.0 Times-Roman | unnecessary drugs and chemicals—especially tobacco
# 10.0 Times-Roman | and other elements of a healthy lifestyle.
# 10.0 Optima-Bold | Resources
# 8.5 Optima-Bold | PERIODICALS
# 9.0 Times-Roman | Dunn, J. C., and E. W. Fonkalsrud. “Improved Survi
# 9.0 Times-Roman | Infants with Omphalocele.”
# 9.0 Times-Italic | American Journal of Surgery
# 9.0 Times-Roman | 173 (April 1997): 284-7.
# 9.0 Times-Roman | Langer, J. C. “Gastroschisis and Omphalocele.”
# 9.0 Times-Italic | Seminars in
# 9.0 Times-Italic | Pediatric Surgery
# 9.0 Times-Roman | 5 (May 1996): 124-8.
# 10.0 Times-Roman | J. Ricker Polsdorfer, MD
# 12.0 Optima | Abnormal heart rhythms
# 12.0 Optima-Italic | see
# 12.0 Optima-Bold | Arrhythmias
# 12.0 Optima | ABO blood typing
# 12.0 Optima-Italic | see
# 12.0 Optima-Bold | Blood typing and
# 12.0 Optima-Bold | crossmatching
# 12.0 Optima | ABO incompatibility
# 12.0 Optima-Italic | see
# 12.0 Optima-Bold | Erythroblastosis
# 12.0 Optima-Bold | fetalis
# 12.0 Optima | Abortion, habitual
# 12.0 Optima-Italic | see
# 12.0 Optima-Bold | Recurrent
# 12.0 Optima-Bold | miscarriage
# 15.0 Optima-Bold | Abortion, partial birth
# 11.0 Optima-Bold | Definition
# 10.0 Times-Roman | Partial birth abortion is a method of late-term ab
# 10.0 Times-Roman | tion that terminates a
# 10.0 Times-Bold | pregnancy
# 10.0 Times-Roman | and results in the
# 10.0 Times-Bold | death
# 10.0 Times-Roman | and intact removal of a fetus. This procedure is m
# 10.0 Times-Roman | commonly referred to as intact dilatation and extr
# 10.0 Times-Roman | (D & X).
# 11.0 Optima-Bold | Purpose
# 10.0 Times-Roman | Partial birth abortion, or D&X, is performed to en
# 10.0 Times-Roman | pregnancy and results in the death of a fetus, typ
# 8.5 Optima-Bold | GALE ENCYCLOPEDIA OF MEDICINE 2
# 10.1 Optima-Bold | 6
# 10.0 Optima-Bold | Abortion, partial birth