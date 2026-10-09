# todo-tele

Bot Telegram buat nyatet todo list langsung dari chat. Kirim pesan apa aja, langsung jadi todo. Ada juga fitur pengingat (reminder).

## Fitur

- **Tambah todo dari chat** — kirim pesan biasa, langsung dicatet
- **Lihat todo** — `/list`
- **Tandai selesai** — `/done <id>` (bisa dibalikin pakai `/undo <id>`)
- **Hapus todo** — `/hapus <id>`
- **Revisi todo** — `/edit <id> <teks baru>`
- **Tambah catatan** — `/tambah <id> <catatan>`
- **Pengingat** — `/remind <waktu> <teks>`
- **Bersihkan yang selesai** — `/clear`

## Setup

1. Bikin bot di [@BotFather](https://t.me/BotFather), ambil token-nya.
2. Bikin virtual env & install dependency:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Copy `.env.example` jadi `.env`, isi `BOT_TOKEN`:

   ```
   BOT_TOKEN=123456789:token_kamu
   ```

   Buat batasi cuma ID tertentu yang boleh pakai bot, isi `ALLOWED_USER_IDS`
   (pisah pakai koma). Kosongin kalau mau semua orang boleh. Kalau ada yang
   gak diizinkan chat, bot bakal balas sambil nunjukin ID Telegram-nya.

4. Jalanin bot:

   ```powershell
   python bot.py
   ```

5. Buka chat bot di Telegram, kirim `/start`.

## Contoh pakai

| Kirim ke bot            | Hasil                                  |
| ----------------------- | -------------------------------------- |
| `beli susu`             | langsung jadi todo                     |
| `/list`                 | lihat semua todo                       |
| `/done 3`               | todo #3 ditandai selesai               |
| `/edit 3 teks baru`     | ganti isi todo #3                      |
| `/tambah 3 catatan`     | tambahin catatan ke todo #3            |
| `/hapus 3`              | todo #3 dihapus                        |
| `/remind 22:30 belajar` | todo + diingetin jam 22:30             |
| `/remind +2h meeting`   | todo + diingetin 2 jam dari sekarang   |
| `/remind 17-08-2026 09:00 bayar listrik` | diingetin di tanggal & jam itu |

Format waktu yang didukung: `HH:MM`, `DD-MM-YYYY HH:MM`, dan relatif `+30m` / `+2h` / `+1d`.

## Struktur

- `bot.py` — handler Telegram + parser waktu reminder
- `db.py` — penyimpanan SQLite (`todo.db`, dibuat otomatis)
- `requirements.txt` — dependency

Data disimpan lokal di `todo.db`, jadi tiap user cuma lihat todo-nya sendiri.
