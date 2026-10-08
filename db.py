import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).with_name("todo.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                text       TEXT NOT NULL,
                done       INTEGER NOT NULL DEFAULT 0,
                remind_at  TEXT,
                reminded   INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_todos_user ON todos (user_id, done)"
        )


def add_todo(user_id, text, remind_at=None):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO todos (user_id, text, remind_at, created_at) VALUES (?, ?, ?, ?)",
            (user_id, text, remind_at, datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def list_todos(user_id, only_pending=False):
    query = "SELECT * FROM todos WHERE user_id = ?"
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
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE todos SET done = ? WHERE id = ? AND user_id = ?",
            (1 if done else 0, todo_id, user_id),
        )
        return cur.rowcount > 0


def delete_todo(user_id, todo_id):
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id)
        )
        return cur.rowcount > 0


def clear_done(user_id):
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM todos WHERE user_id = ? AND done = 1", (user_id,)
        )
        return cur.rowcount


def due_reminders(now_iso):
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT * FROM todos
            WHERE remind_at IS NOT NULL
              AND reminded = 0
              AND done = 0
              AND remind_at <= ?
            """,
            (now_iso,),
        ).fetchall()


def mark_reminded(todo_id):
    with get_conn() as conn:
        conn.execute("UPDATE todos SET reminded = 1 WHERE id = ?", (todo_id,))
