import os

from dotenv import load_dotenv
from flask import Flask, Response, render_template, request

import db

load_dotenv()
PASSWORD = os.getenv("DASHBOARD_PASSWORD")
HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.getenv("DASHBOARD_PORT", "5000"))

app = Flask(__name__)

FILTERS = {
    "done": {"label": "✅ Selesai", "kwargs": {"done": True, "archived": False}},
    "archived": {"label": "📦 Diarsipkan", "kwargs": {"archived": True}},
    "pending": {"label": "⬜ Belum selesai", "kwargs": {"done": False, "archived": False}},
    "all": {"label": "📋 Semua", "kwargs": {}},
}


@app.before_request
def require_auth():
    if not PASSWORD:
        return None
    auth = request.authorization
    if not auth or auth.password != PASSWORD:
        return Response(
            "Login dulu", 401, {"WWW-Authenticate": 'Basic realm="todo"'}
        )
    return None


@app.route("/")
def index():
    key = request.args.get("f", "done")
    if key not in FILTERS:
        key = "done"
    rows = db.query_todos(**FILTERS[key]["kwargs"])
    return render_template(
        "index.html",
        rows=rows,
        current=key,
        filters=FILTERS,
        stats=db.counts(),
    )


if __name__ == "__main__":
    db.init_db()
    print(f"Dashboard jalan di http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
