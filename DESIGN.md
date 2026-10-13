# DESIGN.md

Arah desain untuk dashboard `todo-tele`.

## Identitas

Buku catatan kerja pribadi. Terasa seperti membaca lembar arsip: tinta di atas
kertas, baris yang rapi, satu aksen cap merah. Bukan dashboard SaaS generik.

## Kepribadian

Tenang, presisi, agak formal. Data dibaca dulu, dekorasi belakangan.

## Palet

Neutral kertas + tinta, satu aksen warna cap.

- Kertas (light): `#f4f1e9`, Tinta: `#1b1a16`, Garis: `#d8d1c2`
- Malam (dark): `#15140f` / `#e8e2d4` / `#2e2b23`
- Aksen cap (satu-satunya warna): `#9b2c22` di terang, `#e08a6f` di gelap

Alasan: arsip itu tinta di kertas, jadi warna masuk lewat dua neutral dulu.
Aksen dipakai cuma di status "Arsip" dan fokus keyboard, supaya tetap jadi
aksen, bukan cat seluruh halaman (R-29).

## Tipografi

- Judul + isi catatan: serif (`Iowan Old Style`, `Palatino`, `Georgia`) supaya
  berasa tercetak dan entri kebaca seperti baris buku (R-06).
- Angka + kolom data (id, tanggal, user): sans sistem dengan angka tabular,
  karena data kecil butuh kebaca, bukan gaya.

## Mood

Meja kerja siang hari, teks gelap di kertas terang. Ada mode malam buat baca
malam, tapi default-nya terang.

## Dial

`Dial: ENERGY 2 / RHYTHM 2 / MOTION 1`

Alasan: 2 karena ini alat kerja, bukan panggung. RHYTHM 2 karena bagiannya
sedikit (masthead, filter, tabel) dan cuma tabel yang jadi fokus. MOTION 1
karena dashboard yang dibaca cepat gak butuh animasi; cukup hover + fokus.
