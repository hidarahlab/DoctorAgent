# langkah 1 buka pdf dan baca teks satu halaman

from pathlib import Path   # library bawaan Python buat ngolah path file/folder
import pymupdf             # library buat baca PDF (nama lamanya: fitz)

# Bikin path ke PDF berdasarkan lokasi script ini:
# __file__          → path file eksplorasi_1.py
# .resolve()        → ubah jadi path absolut (lengkap dari root)
# .parent           → naik ke folder latihan/
# .parent.parent    → naik lagi ke folder DoctorAgent/
# / "data" / ...    → masuk ke data/medical_book.pdf
pdfPath = Path(__file__).resolve().parent.parent / "data" / "medical_book.pdf"

doc = pymupdf.open(pdfPath)                    # buka PDF, hasilnya objek dokumen
print("Jumlah halaman: ", doc.page_count)      # total halaman di PDF

page = doc[19]               # ambil halaman ke-20 (index mulai dari 0)
teks = page.get_text()       # ekstrak semua teks di halaman itu jadi string
print(teks[:600])            # tampilkan 600 karakter pertama aja biar nggak kepanjangan

#output
# Jumlah halaman:  637
# Description
# Many unexpected and fascinating events occur dur-
# ing the development of a fetus inside the womb. The
# stomach and intestines begin development outside the
# baby’s abdomen and only later does the abdominal wall
# enclose them. Occasionally, either the umbilical opening
# is too large, or it develops improperly, allowing the bow-
# els or stomach to remain outside or squeeze through the
# abdominal wall.
# Causes and symptoms
# There are many causes for birth defects that still
# remain unclear. Presently, the cause(s) of abdominal wall
# defects is unknown, and any symptoms the mother may
# have to in