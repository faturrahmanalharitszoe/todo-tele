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
- **Bersihkan yang selesai** — `/clear` (diarsipkan, bukan dihapus)
- **Dashboard web** — lihat todo selesai & arsip lewat browser

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

## Dashboard web

Dashboard buat ngeliat todo, termasuk yang udah selesai dan yang udah
di-`/clear` (diarsipkan). Jalanin di terminal terpisah:

```powershell
python dashboard.py
```

Buka http://127.0.0.1:5000 di browser. Ada tab: **Selesai**, **Diarsipkan**,
**Belum selesai**, dan **Semua**. Pakai data `todo.db` yang sama kayak bot.

Kalau mau password, isi `DASHBOARD_PASSWORD` di `.env` (login pakai Basic Auth,
username bebas). Default cuma bisa diakses dari komputer sendiri; ubah
`DASHBOARD_HOST` ke `0.0.0.0` kalau mau diakses dari LAN.

## Deploy ke server (nginx + HTTPS)

Contoh untuk Ubuntu/Debian, subdomain `todo.faturrahmanalharitszoe.my.id`,
app di `/opt/todo-tele`. Ganti path/user kalau beda.

1. **Copy project & install dependency** di server:

   ```bash
   sudo mkdir -p /opt/todo-tele
   # copy file project ke /opt/todo-tele (scp/git clone)
   cd /opt/todo-tele
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   cp .env.example .env   # lalu isi BOT_TOKEN & ALLOWED_USER_IDS
   ```

2. **Jalanin sebagai service** (bot + dashboard):

   ```bash
   sudo cp deploy/todo-bot.service deploy/todo-dashboard.service /etc/systemd/system/
   # edit dulu User/WorkingDirectory kalau path-nya beda
   sudo systemctl daemon-reload
   sudo systemctl enable --now todo-bot todo-dashboard
   sudo systemctl status todo-dashboard
   ```

   Cek dashboard lokal: `curl http://127.0.0.1:5000` harus balas HTML.

3. **Pasang config nginx**:

   ```bash
   sudo cp deploy/nginx-todo.conf /etc/nginx/sites-available/todo-dashboard
   sudo ln -s /etc/nginx/sites-available/todo-dashboard /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```

4. **Arahin DNS**: bikin record `A` untuk `todo` ke IP server, tunggu propagasi.

5. **HTTPS via certbot** (otomatis nambah sertifikat + redirect ke 443):

   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d todo.faturrahmanalharitszoe.my.id
   ```

   Buka `https://todo.faturrahmanalharitszoe.my.id`. Renewal udah otomatis
   lewat systemd timer dari certbot.

Catatan: dashboard gak pakai auth sesuai pilihanmu. Kalau nanti mau dibatasi,
bisa pasang Basic Auth di nginx atau isi `DASHBOARD_PASSWORD` di `.env`.

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

Format waktu yang didukung: `HH:MM`, `DD-MM-YYYY HH:MM`, dan relatif `+30m` / `+2h` / `+1d`. Semua waktu ditafsirkan **WIB (GMT+7)**; disimpan sebagai UTC, ditampilkan kembali sebagai WIB.

## Struktur

- `bot.py` — handler Telegram + parser waktu reminder
- `dashboard.py` — web dashboard (Flask)
- `templates/index.html` — tampilan dashboard
- `db.py` — penyimpanan SQLite (`todo.db`, dibuat otomatis)
- `deploy/` — config nginx, systemd service, gunicorn
- `requirements.txt` — dependency

Data disimpan lokal di `todo.db`, jadi tiap user cuma lihat todo-nya sendiri.
