import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).with_name("todo.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                text        TEXT NOT NULL,
                done        INTEGER NOT NULL DEFAULT 0,
                done_at     TEXT,
                archived    INTEGER NOT NULL DEFAULT 0,
                archived_at TEXT,
                remind_at   TEXT,
                reminded    INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL
            )
            """
        )
        _migrate(conn)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_todos_user ON todos (user_id, done, archived)"
        )


def _migrate(conn):
    """Tambahin kolom baru kalau DB lama belum punya."""
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(todos)")}
    if "done_at" not in cols:
        conn.execute("ALTER TABLE todos ADD COLUMN done_at TEXT")
    if "archived" not in cols:
        conn.execute("ALTER TABLE todos ADD COLUMN archived INTEGER NOT NULL DEFAULT 0")
    if "archived_at" not in cols:
        conn.execute("ALTER TABLE todos ADD COLUMN archived_at TEXT")


def add_todo(user_id, text, remind_at=None):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO todos (user_id, text, remind_at, created_at) VALUES (?, ?, ?, ?)",
            (user_id, text, remind_at, datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def list_todos(user_id, only_pending=False):
    query = "SELECT * FROM todos WHERE user_id = ? AND archived = 0"
    if only_pending:
        query += " AND done = 0"
    query += " ORDER BY done ASC, id ASC"
    with get_conn() as conn:
        return conn.execute(query, (user_id,)).fetchall()


def get_todo(user_id, todo_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id)
        ).fetchone()


def update_todo(user_id, todo_id, text):
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE todos SET text = ? WHERE id = ? AND user_id = ?",
            (text, todo_id, user_id),
        )
        return cur.rowcount > 0


def mark_done(user_id, todo_id, done=True):
    done_at = datetime.now().isoformat(timespec="seconds") if done else None
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE todos SET done = ?, done_at = ? WHERE id = ? AND user_id = ?",
            (1 if done else 0, done_at, todo_id, user_id),
        )
        return cur.rowcount > 0


def delete_todo(user_id, todo_id):
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id)
        )
        return cur.rowcount > 0


def archive_done(user_id):
    """Arsip todo yang udah selesai (gak dihapus, biar masih kebaca di dashboard)."""
    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE todos
            SET archived = 1, archived_at = ?
            WHERE user_id = ? AND done = 1 AND archived = 0
            """,
            (datetime.now().isoformat(timespec="seconds"), user_id),
        )
        return cur.rowcount


def query_todos(done=None, archived=None, user_id=None):
    """Query fleksibel buat dashboard. None = gak difilter."""
    query = "SELECT * FROM todos WHERE 1=1"
    params = []
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)
    if done is not None:
        query += " AND done = ?"
        params.append(1 if done else 0)
    if archived is not None:
        query += " AND archived = ?"
        params.append(1 if archived else 0)
    query += " ORDER BY id DESC"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def counts():
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*)                                          AS total,
                SUM(CASE WHEN done = 0 AND archived = 0 THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN done = 1 AND archived = 0 THEN 1 ELSE 0 END) AS done,
                SUM(CASE WHEN archived = 1 THEN 1 ELSE 0 END)              AS archived
            FROM todos
            """
        ).fetchone()
        return {k: (row[k] or 0) for k in ("total", "pending", "done", "archived")}


def due_reminders(now_iso):
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT * FROM todos
            WHERE remind_at IS NOT NULL
              AND reminded = 0
              AND done = 0
              AND archived = 0
              AND remind_at <= ?
            """,
            (now_iso,),
        ).fetchall()


def mark_reminded(todo_id):
    with get_conn() as conn:
        conn.execute("UPDATE todos SET reminded = 1 WHERE id = ?", (todo_id,))
