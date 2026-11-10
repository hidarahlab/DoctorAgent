from ingest_saya import _split

kalimat = "Ini adalah kalimat contoh nomor {} yang cukup panjang untuk tes. "
teks = "".join(kalimat.format(i) for i in range(1, 41))
print("panjang teks asli:", len(teks))

potongan = _split(teks, size=600, overlap=100)
for i, p in enumerate(potongan):
    print(f"chunk {i}: {len(p)} karakter | awal: {p[:40]!r}")

#langkah 11
# panjang teks asli: 2591
# chunk 0: 575 karakter | awal: 'Ini adalah kalimat contoh nomor 1 yang c'
# chunk 1: 551 karakter | awal: '8 yang cukup panjang untuk tes. Ini adal'
# chunk 2: 553 karakter | awal: '15 yang cukup panjang untuk tes. Ini ada'
# chunk 3: 553 karakter | awal: '22 yang cukup panjang untuk tes. Ini ada'
# chunk 4: 553 karakter | awal: '29 yang cukup panjang untuk tes. Ini ada'
# chunk 5: 293 karakter | awal: '36 yang cukup panjang untuk tes. Ini ada'