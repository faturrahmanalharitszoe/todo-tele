import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, Response, render_template, request

import db

load_dotenv()
PASSWORD = os.getenv("DASHBOARD_PASSWORD")
HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.getenv("DASHBOARD_PORT", "5000"))

app = Flask(__name__)

FILTERS = {
    "pending": {"label": "Terbuka", "kwargs": {"done": False, "archived": False}},
    "done": {"label": "Selesai", "kwargs": {"done": True, "archived": False}},
    "archived": {"label": "Arsip", "kwargs": {"archived": True}},
    "all": {"label": "Semua", "kwargs": {}},
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
    stats = db.counts()
    filter_counts = {
        "pending": stats["pending"],
        "done": stats["done"],
        "archived": stats["archived"],
        "all": stats["total"],
    }
    return render_template(
        "index.html",
        rows=rows,
        current=key,
        filters=FILTERS,
        filter_counts=filter_counts,
        stats=stats,
        today=datetime.now().strftime("%d-%m-%Y %H:%M"),
    )


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, title="Halaman tidak ada"), 404


@app.errorhandler(500)
def server_error(_):
    return (
        render_template("error.html", code=500, title="Gagal memuat data"),
        500,
    )


if __name__ == "__main__":
    db.init_db()
    print(f"Dashboard jalan di http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
