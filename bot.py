import logging
import os
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import db

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHECK_INTERVAL = 30  # detik

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)


def parse_reminder(args):
    """Ambil waktu di awal `args`. Return (datetime, sisa_teks) atau (None, None)."""
    now = datetime.now()
    text = args.strip()

    m = re.match(r"^\+(\d+)\s*([smhd])\s+(.+)$", text, re.IGNORECASE)
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        delta = {
            "s": timedelta(seconds=n),
            "m": timedelta(minutes=n),
            "h": timedelta(hours=n),
            "d": timedelta(days=n),
        }[unit]
        return now + delta, m.group(3).strip()

    m = re.match(r"^(\d{1,2}):(\d{2})\s+(.+)$", text)
    if m:
        target = now.replace(
            hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0
        )
        if target <= now:
            target += timedelta(days=1)
        return target, m.group(3).strip()

    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})\s+(\d{1,2}):(\d{2})\s+(.+)$", text)
    if m:
        try:
            target = datetime(
                int(m.group(3)), int(m.group(2)), int(m.group(1)),
                int(m.group(4)), int(m.group(5)),
            )
        except ValueError:
            return None, None
        return target, m.group(6).strip()

    return None, None


def fmt(todo):
    mark = "✅" if todo["done"] else "⬜"
    line = f"{mark} <code>#{todo['id']}</code> {todo['text']}"
    if todo["remind_at"]:
        line += f"\n     ⏰ <i>{todo['remind_at'][:16].replace('T', ' ')}</i>"
    return line


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirim pesan apa aja, langsung gw catet jadi todo.\n\n"
        "Perintah:\n"
        "/list — lihat semua todo\n"
        "/done &lt;id&gt; — tandai selesai\n"
        "/hapus &lt;id&gt; — hapus todo\n"
        "/edit &lt;id&gt; &lt;teks baru&gt; — ganti isi todo\n"
        "/tambah &lt;id&gt; &lt;catatan&gt; — tambahin catatan ke todo\n"
        "/remind &lt;waktu&gt; &lt;teks&gt; — todo + pengingat\n"
        "/clear — hapus semua todo yang udah selesai\n\n"
        "Format waktu pengingat:\n"
        "• <code>22:30</code> (hari ini/ besok)\n"
        "• <code>17-08-2026 09:00</code>\n"
        "• <code>+30m</code>, <code>+2h</code>, <code>+1d</code>",
        parse_mode=ParseMode.HTML,
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await start(update, ctx)


async def list_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = db.list_todos(update.effective_user.id)
    if not rows:
        await update.message.reply_text("Belum ada todo. Kirim pesan buat nambahin.")
        return
    pending = sum(1 for r in rows if not r["done"])
    header = f"📋 *Todo kamu* ({pending} belum selesai)\n\n"
    body = "\n".join(fmt(r) for r in rows)
    await update.message.reply_text(
        header + body, parse_mode=ParseMode.HTML
    )


async def add_from_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        return
    todo_id = db.add_todo(update.effective_user.id, text)
    await update.message.reply_text(
        f"✅ Dicatet! <code>#{todo_id}</code> {text}", parse_mode=ParseMode.HTML
    )


async def done_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _set_done(update, ctx, True)


async def undo_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _set_done(update, ctx, False)


async def _set_done(update, ctx, done):
    if not ctx.args:
        await update.message.reply_text("Format: /done <id>")
        return
    try:
        todo_id = int(ctx.args[0].lstrip("#"))
    except ValueError:
        await update.message.reply_text("Id harus berupa angka.")
        return
    if db.mark_done(update.effective_user.id, todo_id, done):
        await update.message.reply_text(
            f"{'✅ Selesai' if done else '↩️ Dibalikin'} #{todo_id}"
        )
    else:
        await update.message.reply_text(f"Todo #{todo_id} gak ketemu.")


async def hapus_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Format: /hapus <id>")
        return
    try:
        todo_id = int(ctx.args[0].lstrip("#"))
    except ValueError:
        await update.message.reply_text("Id harus berupa angka.")
        return
    if db.delete_todo(update.effective_user.id, todo_id):
        await update.message.reply_text(f"🗑️ Todo #{todo_id} dihapus.")
    else:
        await update.message.reply_text(f"Todo #{todo_id} gak ketemu.")


async def clear_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n = db.clear_done(update.effective_user.id)
    await update.message.reply_text(f"🗑️ {n} todo selesai dihapus.")


def split_id_text(args):
    if not args:
        return None, ""
    try:
        todo_id = int(args[0].lstrip("#"))
    except ValueError:
        return None, ""
    return todo_id, " ".join(args[1:]).strip()


async def edit_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    todo_id, text = split_id_text(ctx.args)
    if todo_id is None or not text:
        await update.message.reply_text("Format: /edit <id> <teks baru>")
        return
    if db.update_todo(update.effective_user.id, todo_id, text):
        await update.message.reply_text(
            f"✏️ Todo #{todo_id} diperbarui:\n{text}"
        )
    else:
        await update.message.reply_text(f"Todo #{todo_id} gak ketemu.")


async def tambah_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    todo_id, text = split_id_text(ctx.args)
    if todo_id is None or not text:
        await update.message.reply_text("Format: /tambah <id> <catatan>")
        return
    todo = db.get_todo(update.effective_user.id, todo_id)
    if not todo:
        await update.message.reply_text(f"Todo #{todo_id} gak ketemu.")
        return
    db.update_todo(update.effective_user.id, todo_id, f"{todo['text']}\n{text}")
    await update.message.reply_text(f"➕ Catatan ditambahin ke #{todo_id}.")


async def remind_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = " ".join(ctx.args)
    if not args:
        await update.message.reply_text(
            "Format: /remind <waktu> <teks>\n"
            "Contoh: /remind 22:30 belajar\n"
            "        /remind +2h meeting\n"
            "        /remind 17-08-2026 09:00 bayar listrik"
        )
        return
    when, text = parse_reminder(args)
    if when is None or not text:
        await update.message.reply_text(
            "Waktu gak kebaca. Contoh: 22:30, +30m, +2h, +1d, 17-08-2026 09:00"
        )
        return
    todo_id = db.add_todo(
        update.effective_user.id, text, remind_at=when.isoformat(timespec="seconds")
    )
    await update.message.reply_text(
        f"⏰ Dicatet! <code>#{todo_id}</code> {text}\n"
        f"Diingetin: <b>{when.strftime('%d-%m-%Y %H:%M')}</b>",
        parse_mode=ParseMode.HTML,
    )


async def check_reminders(ctx: ContextTypes.DEFAULT_TYPE):
    for row in db.due_reminders(datetime.now().isoformat(timespec="seconds")):
        try:
            await ctx.bot.send_message(
                chat_id=row["user_id"],
                text=f"⏰ *Pengingat!*\n<code>#{row['id']}</code> {row['text']}",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            log.warning("Gagal kirim reminder #%s: %s", row["id"], e)
        db.mark_reminded(row["id"])


def main():
    if not TOKEN:
        raise SystemExit(
            "BOT_TOKEN belum diisi. Copy .env.example jadi .env lalu isi tokennya."
        )
    db.init_db()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("done", done_cmd))
    app.add_handler(CommandHandler(["undo", "undone"], undo_cmd))
    app.add_handler(CommandHandler(["hapus", "del", "delete"], hapus_cmd))
    app.add_handler(CommandHandler(["edit", "revisi"], edit_cmd))
    app.add_handler(CommandHandler(["tambah", "append"], tambah_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("remind", remind_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_from_text))

    app.job_queue.run_repeating(check_reminders, interval=CHECK_INTERVAL, first=5)

    log.info("Bot jalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
