import sqlite3
import json
from datetime import datetime

DB_PATH = "history.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    conn.commit()
    conn.close()


def save_analysis(filename: str, result: dict, feedback: list):
    conn = sqlite3.connect(DB_PATH)
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
    conn.commit()
    conn.close()


def get_history(limit: int = 20) -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM analyses ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()

    history = []
    for row in rows:
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

    return history