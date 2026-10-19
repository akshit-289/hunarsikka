"""SQLite storage helpers for the local HunarSikka demo."""
import hashlib
import hmac
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "hunarsikka.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 240_000)
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','teacher','admin')),
            approved INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            duration TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS completions (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
            completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id, lesson_id)
        );
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            answers_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS training (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            objectives TEXT NOT NULL,
            duration TEXT NOT NULL,
            activity TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS training_completions (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            training_id INTEGER NOT NULL REFERENCES training(id) ON DELETE CASCADE,
            completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id, training_id)
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            starts_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Awaiting Confirmation',
            meeting_url TEXT NOT NULL DEFAULT '',
            created_by INTEGER REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS registrations (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id, session_id)
        );
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            pathway TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS budget_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            allowance REAL NOT NULL,
            needs REAL NOT NULL,
            wants REAL NOT NULL,
            savings REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # Local-only demonstration administrator. Change the password before any real use.
        admin = db.execute("SELECT id FROM users WHERE email=?", ("admin@hunarsikka.local",)).fetchone()
        if not admin:
            db.execute(
                "INSERT INTO users(name,email,password_hash,role,approved) VALUES(?,?,?,?,1)",
                ("HunarSikka Admin", "admin@hunarsikka.local", hash_password("ChangeMe123!"), "admin"),
            )
        if db.execute("SELECT COUNT(*) FROM lessons").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO lessons(title,category,description,duration,url) VALUES(?,?,?,?,?)",
                [
                    ("Budgeting Basics", "Financial Literacy", "Learn to separate needs, wants and savings using a simple student budget.", "8 min", ""),
                    ("Understanding Digital Safety", "Digital Skills", "Recognise suspicious links and protect personal information online.", "10 min", ""),
                    ("Presenting an Entrepreneurial Idea", "Entrepreneurship", "Structure a short pitch around a problem, solution and audience.", "12 min", ""),
                ],
            )
        if db.execute("SELECT COUNT(*) FROM training").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO training(title,description,objectives,duration,activity,url) VALUES(?,?,?,?,?,?)",
                [
                    ("Effective Lesson Planning", "Plan a clear lesson around student learning outcomes.", "Write measurable objectives; sequence activities; plan a short check for understanding.", "25 minutes", "Draft a 3-step lesson plan for a topic you teach.", ""),
                    ("Presentation and Communication Skills", "Make explanations clearer and more engaging.", "Use concise language; structure explanations; ask useful questions.", "20 minutes", "Explain one difficult concept in five simple sentences.", ""),
                    ("Student Engagement Techniques", "Use practical activities to encourage participation.", "Choose an active-learning technique; include different participation options.", "20 minutes", "Design one 5-minute classroom activity.", ""),
                    ("Classroom Management", "Set routines and respond constructively to common scenarios.", "Create clear expectations; use calm redirection; reflect on classroom scenarios.", "25 minutes", "Write a response to a fictional classroom scenario.", ""),
                    ("Digital Tools for Teaching", "Choose digital tools that support a learning objective.", "Match a tool to a task; consider accessibility and privacy.", "20 minutes", "Plan one lesson activity using a digital resource.", ""),
                    ("Assessment and Feedback", "Give specific feedback students can act on.", "Use criteria; identify a strength; provide a next step.", "20 minutes", "Write supportive feedback for a sample assignment.", ""),
                ],
            )
        if db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0:
            db.execute(
                "INSERT INTO sessions(title,description,starts_at,status,meeting_url) VALUES(?,?,?,?,?)",
                ("Planning Your First Student Budget", "A sample Live Lab session. The date and meeting link should be confirmed by an administrator.", "2026-11-07 16:00", "Awaiting Confirmation", ""),
            )


def get_user_by_email(email: str):
    with connect() as db:
        return db.execute("SELECT * FROM users WHERE email=?", (email.strip(),)).fetchone()


def create_user(name: str, email: str, password: str, role: str):
    approved = 1 if role == "student" else 0
    with connect() as db:
        db.execute(
            "INSERT INTO users(name,email,password_hash,role,approved) VALUES(?,?,?,?,?)",
            (name.strip(), email.strip().lower(), hash_password(password), role, approved),
        )


def rows(query: str, params=()):
    with connect() as db:
        return db.execute(query, params).fetchall()


def one(query: str, params=()):
    with connect() as db:
        return db.execute(query, params).fetchone()


def execute(query: str, params=()):
    with connect() as db:
        cur = db.execute(query, params)
        return cur.lastrowid
