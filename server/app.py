import json
import os
import sqlite3
import time
import uuid
from functools import wraps
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS


DATABASE_PATH = Path(os.environ.get("PSR354_DATABASE_PATH", "data/kalender.sqlite3"))
DAY_IDS = {"minggu", "senin", "selasa", "rabu", "kamis", "jumat", "sabtu"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
CORS(app, supports_credentials=True)


def db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_ms():
    return int(time.time() * 1000)


def json_map(value):
    if isinstance(value, dict):
        return value
    return {}


def require_login(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "unauthorized"}), 401
        return handler(*args, **kwargs)

    return wrapper


def require_admin(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return jsonify({"error": "forbidden"}), 403
        return handler(*args, **kwargs)

    return wrapper


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY,
              email TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL,
              is_admin INTEGER NOT NULL DEFAULT 0,
              created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
              id TEXT PRIMARY KEY,
              date TEXT NOT NULL,
              title TEXT NOT NULL,
              created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS schedule (
              day_id TEXT PRIMARY KEY,
              lessons TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS announcements (
              id TEXT PRIMARY KEY,
              text TEXT NOT NULL,
              created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_data (
              user_id TEXT PRIMARY KEY,
              personal_tasks TEXT NOT NULL,
              daily_plans TEXT NOT NULL,
              daily_notes TEXT NOT NULL,
              data_version INTEGER NOT NULL,
              updated_at INTEGER NOT NULL,
              FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        admin_email = os.environ.get("ADMIN_EMAIL")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if admin_email and admin_password:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO users (id, email, password_hash, is_admin, created_at) VALUES (?, ?, ?, 1, ?)",
                    (str(uuid.uuid4()), admin_email, generate_password_hash(admin_password), now_ms()),
                )


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.get("/")
def frontend_index():
    return send_from_directory("/app", "index.html")


@app.get("/assets/<path:filename>")
def frontend_assets(filename):
    return send_from_directory("/app/assets", filename)


@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "invalid_credentials"}), 401
    session.clear()
    session["user_id"] = user["id"]
    session["email"] = user["email"]
    session["is_admin"] = bool(user["is_admin"])
    return jsonify({"id": user["id"], "email": user["email"], "isAdmin": bool(user["is_admin"])})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/me")
def me():
    if not session.get("user_id"):
        return jsonify({"user": None})
    return jsonify({
        "user": {
            "id": session["user_id"],
            "email": session.get("email", ""),
            "isAdmin": bool(session.get("is_admin")),
        }
    })


@app.get("/api/events")
def events_index():
    with db() as conn:
        rows = conn.execute("SELECT id, date, title, created_at FROM events ORDER BY date ASC").fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/events")
@require_admin
def events_create():
    payload = request.get_json(silent=True) or {}
    date = str(payload.get("date", "")).strip()
    title = str(payload.get("title", "")).strip()
    if len(date) != 10 or not title or len(title) > 120:
        return jsonify({"error": "invalid_event"}), 400
    item = {"id": str(uuid.uuid4()), "date": date, "title": title, "created_at": now_ms()}
    with db() as conn:
        conn.execute(
            "INSERT INTO events (id, date, title, created_at) VALUES (?, ?, ?, ?)",
            (item["id"], item["date"], item["title"], item["created_at"]),
        )
    return jsonify(item), 201


@app.delete("/api/events/<event_id>")
@require_admin
def events_delete(event_id):
    with db() as conn:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    return jsonify({"ok": True})


@app.get("/api/schedule")
def schedule_index():
    with db() as conn:
        rows = conn.execute("SELECT day_id, lessons FROM schedule").fetchall()
    return jsonify({row["day_id"]: {"lessons": json.loads(row["lessons"])} for row in rows})


@app.put("/api/schedule/<day_id>")
@require_admin
def schedule_update(day_id):
    if day_id not in DAY_IDS:
        return jsonify({"error": "invalid_day"}), 400
    payload = request.get_json(silent=True) or {}
    lessons = payload.get("lessons", [])
    if not isinstance(lessons, list) or len(lessons) > 30:
        return jsonify({"error": "invalid_lessons"}), 400
    clean = []
    for lesson in lessons:
        if not isinstance(lesson, dict):
            continue
        clean.append({
            "teacher": str(lesson.get("teacher", ""))[:80],
            "time": str(lesson.get("time", ""))[:40],
            "subject": str(lesson.get("subject", ""))[:80],
        })
    with db() as conn:
        conn.execute(
            "INSERT INTO schedule (day_id, lessons) VALUES (?, ?) ON CONFLICT(day_id) DO UPDATE SET lessons = excluded.lessons",
            (day_id, json.dumps(clean)),
        )
    return jsonify({"lessons": clean})


@app.get("/api/announcements")
def announcements_index():
    with db() as conn:
        rows = conn.execute("SELECT id, text, created_at FROM announcements ORDER BY created_at DESC").fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/announcements")
@require_admin
def announcements_create():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text or len(text) > 300:
        return jsonify({"error": "invalid_announcement"}), 400
    item = {"id": str(uuid.uuid4()), "text": text, "created_at": now_ms()}
    with db() as conn:
        conn.execute(
            "INSERT INTO announcements (id, text, created_at) VALUES (?, ?, ?)",
            (item["id"], item["text"], item["created_at"]),
        )
    return jsonify(item), 201


@app.delete("/api/announcements/<announcement_id>")
@require_admin
def announcements_delete(announcement_id):
    with db() as conn:
        conn.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
    return jsonify({"ok": True})


@app.get("/api/user-data")
@require_login
def user_data_show():
    user_id = session["user_id"]
    with db() as conn:
        row = conn.execute("SELECT * FROM user_data WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        return jsonify({})
    return jsonify({
        "personalTasks": json.loads(row["personal_tasks"]),
        "dailyPlans": json.loads(row["daily_plans"]),
        "dailyNotes": json.loads(row["daily_notes"]),
        "dataVersion": row["data_version"],
        "updatedAt": row["updated_at"],
    })


@app.put("/api/user-data")
@require_login
def user_data_update():
    payload = request.get_json(silent=True) or {}
    data_version = int(payload.get("dataVersion") or 0)
    record = {
        "personal_tasks": json.dumps(json_map(payload.get("personalTasks"))),
        "daily_plans": json.dumps(json_map(payload.get("dailyPlans"))),
        "daily_notes": json.dumps(json_map(payload.get("dailyNotes"))),
        "data_version": data_version,
        "updated_at": now_ms(),
    }
    with db() as conn:
        conn.execute(
            """
            INSERT INTO user_data (user_id, personal_tasks, daily_plans, daily_notes, data_version, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
              personal_tasks = excluded.personal_tasks,
              daily_plans = excluded.daily_plans,
              daily_notes = excluded.daily_notes,
              data_version = excluded.data_version,
              updated_at = excluded.updated_at
            """,
            (
                session["user_id"],
                record["personal_tasks"],
                record["daily_plans"],
                record["daily_notes"],
                record["data_version"],
                record["updated_at"],
            ),
        )
    return jsonify({"ok": True, "updatedAt": record["updated_at"]})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5050)
