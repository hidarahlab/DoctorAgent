# Langkah 3: statistik font di banyak halaman
# Tujuan: pastikan pola font dari 1 halaman itu konsisten di seluruh buku

from pathlib import Path   # library bawaan Python buat ngolah path file/folder
import pymupdf             # library buat baca PDF
import collections         # buat Counter (penghitung otomatis)

pdfPath = Path(__file__).resolve().parent.parent / "data" / "medical_book.pdf"
doc = pymupdf.open(pdfPath)

hitung = collections.Counter()   # dict khusus: kunci → jumlah kemunculan
contoh = {}                      # kunci → satu contoh teks dengan font itu

for pno in range(15, 60):        # scan halaman 16 s/d 60 (index 15–59)
    for block in doc[pno].get_text("dict")["blocks"]:
        # .get("lines", []) → kalau block gambar (nggak punya lines), pakai list kosong
        for line in block.get("lines", []):
            for span in line["spans"]:
                teks = span["text"].strip()
                if not teks:                 # skip span kosong
                    continue
                kunci = (round(span["size"], 1), span["font"])  # identitas gaya: (ukuran, font)
                hitung[kunci] += 1                              # tambah hitungan
                contoh.setdefault(kunci, teks[:35])             # simpan contoh PERTAMA saja

# Urutkan berdasarkan UKURAN font (terbesar dulu), bukan frekuensi
for kunci, n in sorted(hitung.items(), key=lambda x: -x[0][0]):
    print(f"{kunci[0]:>5} {kunci[1]:<22} {n:>5}x  contoh: {contoh[kunci]}")


#output:
# 15.0 Optima-Bold               20x  contoh: Abdominal wall defects
#  12.5 Optima-Bold               20x  contoh: KEY TERMS
#  12.0 Optima                    28x  contoh: Abnormal heart rhythms
#  12.0 Optima-Italic             29x  contoh: see
#  12.0 Optima-Bold               37x  contoh: Arrhythmias
#  11.0 Optima-Bold              145x  contoh: Precautions
#  10.1 Optima-Bold               45x  contoh: 2
#  10.0 Times-Roman             3003x  contoh: located and tentatively identified 
#  10.0 Times-Bold               194x  contoh: jaundice
#  10.0 Optima-Bold              175x  contoh: Abdominal ultrasound
#  10.0 Optima                   350x  contoh: —A lump of tissue adjacent to an
#  10.0 Times-Italic              52x  contoh: laminaria
#  10.0 Times-SemiboldItalic      19x  contoh: Very early abortions
#  10.0 Optima-Italic              4x  contoh: Streptococ-
#   9.4 T1                         6x  contoh:  
#   9.0 Times-Roman              293x  contoh: Hall, Rebecca.
#   9.0 Times-Italic             127x  contoh: The Ultrasonic Handbook: Clinical, 
#   9.0 Helvetica                  8x  contoh: Uterus
#   8.5 Optima-Bold               99x  contoh: GALE ENCYCLOPEDIA OF MEDICINE 2
#   8.0 Helvetica-Bold            21x  contoh: Between 5 and 7 weeks, a pregnancy 
#   8.0 Helvetica-Oblique         15x  contoh: (Illustration by Elec-
#   8.0 Helvetica-BoldOblique      1x  contoh: Entameoba histolytica.
#   8.0 Helvetica                  8x  contoh: Conception vessel
#   7.8 Helvetica                  6x  contoh: Liver
#   7.5 Times-Roman                4x  contoh: A