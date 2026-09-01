import sqlite3
import json
import os
from contextlib import closing
from datetime import datetime

DB_PATH = "history.db"
DB_PATH_ENV_VAR = "AI_RECRUITMENT_COPILOT_DB_PATH"


def get_db_path() -> str:
    return os.environ.get(DB_PATH_ENV_VAR, DB_PATH)


def init_db():
    with closing(sqlite3.connect(get_db_path())) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT,
                    filename TEXT,
                    match_score REAL,
                    semantic_score REAL,
                    semantic_source TEXT,
                    score_explanation TEXT,
                    resume_skills TEXT,
                    matched_skills TEXT,
                    missing_skills TEXT,
                    feedback TEXT
                )
            """)


def save_analysis(filename: str, result: dict, feedback: list):
    with closing(sqlite3.connect(get_db_path())) as conn:
        with conn:
            conn.execute("""
                INSERT INTO analyses (
                    created_at,
                    filename,
                    match_score,
                    semantic_score,
                    semantic_source,
                    score_explanation,
                    resume_skills,
                    matched_skills,
                    missing_skills,
                    feedback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                filename,
                result["match_score"],
                result["semantic_score"],
                result["semantic_source"],
                result.get("score_explanation", ""),
                json.dumps(result.get("resume_skills", [])),
                json.dumps(result["matched_skills"]),
                json.dumps(result["missing_skills"]),
                json.dumps(feedback)
            ))


def get_history(limit: int = 5) -> list:
    with closing(sqlite3.connect(get_db_path())) as conn:
        rows = conn.execute(
            "SELECT * FROM analyses ORDER BY created_at DESC, id DESC"
        ).fetchall()

    history = []
    seen_filenames = set()

    for row in rows:
        filename = row[2]

        if filename in seen_filenames:
            continue

        seen_filenames.add(filename)

        history.append({
            "id": row[0],
            "created_at": row[1],
            "filename": row[2],
            "match_score": row[3],
            "semantic_score": row[4],
            "semantic_source": row[5],
            "score_explanation": row[6],
            "resume_skills": json.loads(row[7]),
            "matched_skills": json.loads(row[8]),
            "missing_skills": json.loads(row[9]),
            "feedback": json.loads(row[10])
        })

        if len(history) >= limit:
            break

    return history
