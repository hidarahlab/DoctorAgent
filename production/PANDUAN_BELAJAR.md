# Panduan Belajar — Doctor Agent

Panduan ini untuk kamu **meniru ulang** project ini dan **siap menjawab pertanyaan penilai**.
Ikuti urutannya; setiap langkah bisa dites sendiri sebelum lanjut.

---

## Gambaran besar dalam 30 detik

> "Saya membangun chatbot medis dengan 4 agent. **Planner** memahami maksud user dan menulis ulang
> pertanyaan jadi query bahasa Inggris. **RAG agent** mencari potongan Medical Book dengan hybrid search
> (FAISS + BM25) lalu menjawab **hanya** dari potongan itu dengan sitasi. **Evaluator** memeriksa setiap
> klaim terhadap sumber, memberi skor, dan memperbaiki jawaban kalau ada halusinasi. Dari skor itu
> Planner memutuskan: terima, cari ulang, atau eskalasi ke dokter. **Summarizer** merangkum percakapan
> tiap 3 giliran sebagai memori."

---

## Urutan meniru ulang (sesuai urutan data mengalir)

| # | File | Konsep yang dipelajari | Cara tes |
|---|---|---|---|
| 1 | `config.py` | Semua parameter di satu tempat | — |
| 2 | `doctor_agent/ingest.py` | Parsing PDF berdasarkan **ukuran font** → chunk per entry/section | `python -m doctor_agent.ingest` → 3328 chunks |
| 3 | `doctor_agent/retriever.py` | Embedding, FAISS, BM25, **Reciprocal Rank Fusion** | `python -m doctor_agent.retriever` → acne → Acne |
| 4 | `doctor_agent/llm.py` | Memanggil Claude, **structured output** (JSON schema), hitung biaya | — |
| 5 | `doctor_agent/memory.py` | Ringkasan + beberapa giliran terakhir | — |
| 6 | `agents/planner.py` | Klasifikasi intent (LLM) + **policy berbasis aturan** | `pytest -q tests -k policy` |
| 7 | `agents/rag.py` | Prompt "jawab hanya dari konteks", sitasi [n] | — |
| 8 | `agents/evaluator.py` | **LLM-as-judge**, skor, revisi, confidence | `pytest -q tests -k confidence` |
| 9 | `agents/summarizer.py` | Memori percakapan | — |
| 10 | `doctor_agent/orchestrator.py` | Menyambung semua agent + loop re-query | `python scripts/smoke_test.py` |
| 11 | `app.py` | Streamlit chat UI | `streamlit run app.py` |
| 12 | `eval/run_eval.py` | Mengukur sistem dengan angka | `python eval/run_eval.py` |

Tips: ketik ulang sendiri, jangan copy-paste — saat mengetik kamu akan bertanya "kenapa begini?",
dan itulah yang nanti ditanya penilai.

---

## Konsep inti (wajib bisa dijelaskan)

**RAG (Retrieval-Augmented Generation)** — LLM tidak menjawab dari ingatannya, tapi dari dokumen yang
kita ambilkan. Keuntungannya: jawaban bisa dilacak ke halaman buku, dan halusinasi bisa dicek.

**Chunking berbasis struktur** — buku ensiklopedia punya pola tetap (judul 15pt bold, section 11pt bold).
Kita potong mengikuti struktur itu, bukan setiap N karakter, jadi satu chunk tidak mencampur dua penyakit
dan setiap chunk tahu asalnya (entry, section, halaman).

**Embedding** — teks diubah jadi vektor 384 angka; teks yang maknanya mirip punya vektor yang berdekatan
(diukur dengan cosine similarity). Model `bge-small` jalan **lokal**, gratis.

**Hybrid search + RRF** — dense (makna) bagus untuk sinonim, BM25 (kata kunci) bagus untuk istilah medis
persis. Dua ranking digabung: `skor = Σ 1/(60 + ranking)`. Dokumen yang ranking-nya bagus di keduanya naik.

**Query rewriting** — buku berbahasa Inggris, user bisa bertanya dalam bahasa Indonesia atau bahasa awam
("kencing manis"). Planner menerjemahkan jadi query medis Inggris ("antidiabetic drugs"). Lihat hasil
ablation di evaluasi: ini yang membuat retrieval bahasa Indonesia berhasil.

**Structured output** — Planner dan Evaluator wajib mengembalikan JSON sesuai schema (Pydantic), jadi kode
bisa membaca `verdict`, `faithfulness`, dll. tanpa parsing teks yang rapuh.

**LLM-as-judge** — LLM kedua menilai jawaban LLM pertama terhadap sumber yang sama.

**Confidence score** — dihitung di kode, bukan ditebak LLM:
`0.5·faithfulness + 0.3·completeness + 0.2·relevance`. Faithfulness diberi bobot terbesar karena di
domain medis, jawaban salah lebih berbahaya daripada jawaban kurang lengkap.

**Kenapa keputusan accept/re-query/escalate pakai aturan, bukan LLM?** — murah (gratis), cepat,
bisa diprediksi, dan bisa di-unit-test. LLM dipakai di tempat yang memang butuh pemahaman bahasa.

---

## Kemungkinan pertanyaan penilai & jawaban singkat

**Kenapa multi-agent, bukan satu prompt besar?**
Setiap agent punya satu tugas jelas → prompt lebih fokus, bisa pakai model berbeda (hemat biaya),
bisa diuji dan di-debug terpisah, dan Evaluator independen dari penulis jawaban.

**Kenapa Haiku untuk Planner/Summarizer, Opus untuk RAG/Evaluator?**
Klasifikasi dan merangkum itu tugas ringan; menjawab dan memeriksa fakta medis butuh ketelitian.
Planner+Summarizer hanya ~1% dari biaya per pertanyaan.

**Bagaimana mencegah halusinasi?** (berlapis)
1. Prompt RAG: hanya dari excerpt + wajib sitasi. 2. Evaluator mengecek klaim per klaim dan merevisi.
3. Confidence rendah → re-query → tetap rendah → eskalasi. 4. Evaluasi: pertanyaan di luar buku
(dengue, COVID-19, Zika, Ozempic) harus dieskalasi.

**Kenapa tidak pakai LangChain/LangGraph?**
Alurnya sederhana dan deterministik; Python biasa lebih transparan, lebih mudah di-test, dan tanpa
dependensi berat. Kalau alurnya makin bercabang, LangGraph cocok untuk langkah berikutnya.

**Kenapa FAISS IndexFlatIP, bukan vector DB?**
3.328 vektor itu kecil; pencarian exact < 1 ms. Untuk jutaan dokumen baru perlu index aproksimasi
(IVF/HNSW) atau vector DB seperti Chroma/Qdrant.

**Kelemahan sistem ini?**
- Evaluator menilai dengan LLM juga (bisa bias); idealnya ditambah penilaian manusia / dataset berlabel.
- Buku hanya volume A–B; banyak topik tidak tercakup (itulah kenapa eskalasi penting).
- Latensi ~15 detik per pertanyaan karena 2 panggilan Opus berurutan.
- Embedding model bahasa Inggris, jadi bergantung pada query rewriting untuk bahasa Indonesia.

**Kalau diberi waktu lebih?**
Reranker (cross-encoder), streaming jawaban, caching, dataset evaluasi yang lebih besar dengan label
dokter, dan menyimpan memori ke database.

---

## Perintah yang sering dipakai

```bash
source .venv/bin/activate
streamlit run app.py                          # jalankan aplikasi
pytest -q tests                               # tes gratis
python scripts/smoke_test.py "What is asthma?" # tes cepat di terminal
python eval/run_eval.py                       # evaluasi lengkap (~$1.5)
```

---

## Angka yang perlu kamu hafal (hasil evaluasi final)

| Metrik | Nilai | Artinya |
|---|---|---|
| Intent accuracy | 100% | Planner selalu benar membedakan medis / sapaan / di luar topik / darurat |
| Retrieval Hit@5 | 100% | entri buku yang benar selalu ada di 5 potongan teratas |
| Faithfulness | 0,95 | hampir semua klaim didukung sumber |
| In-book dijawab | 100% | pertanyaan yang ada di buku tidak salah ditolak |
| Out-of-book dieskalasi | 100% | dengue, COVID-19, Zika, Ozempic → tidak mengarang |
| Biaya | ~$0,05 / pertanyaan medis | evaluasi 27 soal = $1,16 |
| Latensi | ~13,5 s rata-rata | 2 panggilan Opus berurutan |

**Cerita bagus untuk interview — "evaluasi menemukan bug":** run pertama, pertanyaan Bell's palsy malah
dieskalasi. Ternyata ekspansi alias memakai `alias in query` (substring), sehingga alias "ALS"
cocok di dalam kata "p-als-y" dan hasil pencarian tercemar artikel ALS. Diperbaiki dengan regex
`\b...\b` (kata utuh) + regression test. Setelahnya semua kategori 100%. Pesannya: evaluasi bukan
formalitas — ia menemukan bug yang tidak terlihat saat demo.

**Ablation (gratis, tanpa API):** pertanyaan mentah (banyak bahasa Indonesia) → Hit@5 hanya 74%;
setelah ditulis ulang Planner ke query medis bahasa Inggris → 100%. Ini bukti kenapa Planner penting.
