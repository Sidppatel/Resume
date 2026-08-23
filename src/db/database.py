"""
SQLite Database Manager and Repository for Resume Tailoring History, Queries, Career Knowledge & Data.
"""
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple


DEFAULT_DB_PATH = "data/resume_vault.db"


class ResumeDatabase:
    """
    Manages local SQLite storage for all JD queries, AI prompts, thinking traces,
    career domain knowledge profiles, and tailored resume outputs.
    """

    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self._ensure_db_dir()
        self.init_db()

    def _ensure_db_dir(self):
        """Ensures the parent directory for the database exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Returns an SQLite connection with row factory configured."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        """Initializes database tables, columns, and performance indexes if not present."""
        with self._get_connection() as conn:
            # 1. Tailoring Sessions Table
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tailoring_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_uuid TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    target_job_title TEXT,
                    company_name TEXT,
                    jd_text TEXT NOT NULL,
                    jd_hash TEXT,
                    model TEXT,
                    reasoning_effort TEXT,
                    thinking_process TEXT,
                    token_count INTEGER DEFAULT 0,
                    execution_time_seconds REAL DEFAULT 0.0,
                    prompt_system TEXT,
                    prompt_user TEXT,
                    tailored_data_json TEXT NOT NULL,
                    static_profile_json TEXT,
                    career_knowledge_json TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON tailoring_sessions(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_sessions_job_title ON tailoring_sessions(target_job_title);
                CREATE INDEX IF NOT EXISTS idx_sessions_jd_hash ON tailoring_sessions(jd_hash);

                CREATE TABLE IF NOT EXISTS career_knowledge_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_name TEXT NOT NULL,
                    candidate_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_static_path TEXT,
                    companies_count INTEGER DEFAULT 0,
                    knowledge_json TEXT NOT NULL,
                    reasoning_trace TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_knowledge_profile_name ON career_knowledge_profiles(profile_name);
            """)

            # Schema migration: check if career_knowledge_json exists in tailoring_sessions
            cursor = conn.execute("PRAGMA table_info(tailoring_sessions)")
            columns = [row[1] for row in cursor.fetchall()]
            if "career_knowledge_json" not in columns:
                conn.execute("ALTER TABLE tailoring_sessions ADD COLUMN career_knowledge_json TEXT")

            conn.commit()

    @staticmethod
    def compute_hash(text: str) -> str:
        """Generates SHA256 hex digest of input text."""
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def save_tailoring_run(
        self,
        jd_text: str,
        tailored_data: Dict[str, Any],
        static_data: Optional[Dict[str, Any]] = None,
        knowledge_data: Optional[Dict[str, Any]] = None,
        prompt_system: Optional[str] = None,
        prompt_user: Optional[str] = None,
        thinking_process: Optional[str] = None,
        token_count: int = 0,
        execution_time_seconds: float = 0.0,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        company_name: Optional[str] = None
    ) -> int:
        """
        Records a complete AI tailoring session into the database.

        Returns:
            The newly inserted record ID (int).
        """
        session_uuid = str(uuid.uuid4())
        target_job_title = (
            tailored_data.get("header", {}).get("job_title") or
            tailored_data.get("job_title") or
            "Tailored Resume"
        )
        jd_hash = self.compute_hash(jd_text)

        tailored_json = json.dumps(tailored_data, indent=2, ensure_ascii=False)
        static_json = json.dumps(static_data, indent=2, ensure_ascii=False) if static_data else None
        knowledge_json = json.dumps(knowledge_data, indent=2, ensure_ascii=False) if knowledge_data else None

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tailoring_sessions (
                    session_uuid,
                    target_job_title,
                    company_name,
                    jd_text,
                    jd_hash,
                    model,
                    reasoning_effort,
                    thinking_process,
                    token_count,
                    execution_time_seconds,
                    prompt_system,
                    prompt_user,
                    tailored_data_json,
                    static_profile_json,
                    career_knowledge_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_uuid,
                    target_job_title,
                    company_name,
                    jd_text,
                    jd_hash,
                    model,
                    reasoning_effort,
                    thinking_process,
                    token_count,
                    execution_time_seconds,
                    prompt_system,
                    prompt_user,
                    tailored_json,
                    static_json,
                    knowledge_json
                )
            )
            conn.commit()
            return cursor.lastrowid

    def save_career_knowledge(
        self,
        profile_name: str,
        knowledge_data: Dict[str, Any],
        candidate_name: Optional[str] = None,
        source_static_path: Optional[str] = None,
        reasoning_trace: Optional[str] = None
    ) -> int:
        """
        Records a researched career domain knowledge profile into the database.

        Returns:
            The newly inserted knowledge record ID (int).
        """
        cand_name = candidate_name or knowledge_data.get("candidate_name", "Unknown")
        companies = knowledge_data.get("companies", [])
        companies_count = len(companies)
        knowledge_json = json.dumps(knowledge_data, indent=2, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO career_knowledge_profiles (
                    profile_name,
                    candidate_name,
                    source_static_path,
                    companies_count,
                    knowledge_json,
                    reasoning_trace
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_name,
                    cand_name,
                    source_static_path,
                    companies_count,
                    knowledge_json,
                    reasoning_trace
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_career_knowledge(self, profile_name_or_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Retrieves a career knowledge profile by ID or by profile name (latest)."""
        with self._get_connection() as conn:
            if isinstance(profile_name_or_id, int) or (isinstance(profile_name_or_id, str) and profile_name_or_id.isdigit()):
                row = conn.execute(
                    "SELECT * FROM career_knowledge_profiles WHERE id = ?",
                    (int(profile_name_or_id),)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM career_knowledge_profiles WHERE profile_name = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                    (str(profile_name_or_id),)
                ).fetchone()

            if not row:
                return None

            data = dict(row)
            try:
                data["knowledge_data"] = json.loads(data["knowledge_json"])
            except Exception:
                data["knowledge_data"] = None
            return data

    def list_career_knowledge_profiles(self) -> List[Dict[str, Any]]:
        """Lists all stored career domain knowledge profiles."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT 
                    id,
                    profile_name,
                    candidate_name,
                    created_at,
                    source_static_path,
                    companies_count,
                    LENGTH(knowledge_json) AS knowledge_len,
                    CASE WHEN reasoning_trace IS NOT NULL AND LENGTH(reasoning_trace) > 0 THEN 1 ELSE 0 END AS has_reasoning
                FROM career_knowledge_profiles
                ORDER BY created_at DESC, id DESC
                """
            ).fetchall()
            return [dict(r) for r in rows]

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single tailoring session by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tailoring_sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            if not row:
                return None
            
            data = dict(row)
            try:
                data["tailored_data"] = json.loads(data["tailored_data_json"])
            except Exception:
                data["tailored_data"] = None

            try:
                data["static_profile"] = json.loads(data["static_profile_json"]) if data.get("static_profile_json") else None
            except Exception:
                data["static_profile"] = None

            try:
                data["career_knowledge"] = json.loads(data["career_knowledge_json"]) if data.get("career_knowledge_json") else None
            except Exception:
                data["career_knowledge"] = None

            return data

    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Lists recent tailoring sessions with summary metadata.
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT 
                    id,
                    session_uuid,
                    created_at,
                    target_job_title,
                    company_name,
                    model,
                    token_count,
                    execution_time_seconds,
                    SUBSTR(jd_text, 1, 150) AS jd_preview,
                    LENGTH(jd_text) AS jd_length,
                    CASE WHEN thinking_process IS NOT NULL AND LENGTH(thinking_process) > 0 THEN 1 ELSE 0 END AS has_reasoning,
                    CASE WHEN career_knowledge_json IS NOT NULL AND LENGTH(career_knowledge_json) > 0 THEN 1 ELSE 0 END AS has_knowledge
                FROM tailoring_sessions
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            ).fetchall()
            return [dict(r) for r in rows]

    def search_sessions(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Searches tailoring sessions across job titles, JD content, tailored resume text, and knowledge.
        """
        term = f"%{keyword.strip()}%"
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT 
                    id,
                    session_uuid,
                    created_at,
                    target_job_title,
                    company_name,
                    model,
                    token_count,
                    execution_time_seconds,
                    SUBSTR(jd_text, 1, 150) AS jd_preview,
                    CASE WHEN career_knowledge_json IS NOT NULL AND LENGTH(career_knowledge_json) > 0 THEN 1 ELSE 0 END AS has_knowledge
                FROM tailoring_sessions
                WHERE target_job_title LIKE ? 
                   OR company_name LIKE ? 
                   OR jd_text LIKE ?
                   OR tailored_data_json LIKE ?
                   OR career_knowledge_json LIKE ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (term, term, term, term, term, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def export_session_data(self, session_id: int, output_path: Union[str, Path]) -> Path:
        """
        Exports the tailored resume JSON from a specific session to a target file.
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session #{session_id} not found in database.")

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(session["tailored_data_json"])
        return out_file

    def export_knowledge_data(self, profile_name_or_id: Union[str, int], output_path: Union[str, Path]) -> Path:
        """
        Exports career knowledge JSON from a specific profile to a target file.
        """
        knowledge = self.get_career_knowledge(profile_name_or_id)
        if not knowledge:
            raise ValueError(f"Career knowledge profile '{profile_name_or_id}' not found in database.")

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(knowledge["knowledge_json"])
        return out_file

    def delete_session(self, session_id: int) -> bool:
        """Deletes a tailoring session record by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM tailoring_sessions WHERE id = ?",
                (session_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_knowledge_profile(self, profile_id: int) -> bool:
        """Deletes a career knowledge profile record by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM career_knowledge_profiles WHERE id = ?",
                (profile_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """Calculates global usage statistics from the database."""
        with self._get_connection() as conn:
            total_sessions = conn.execute("SELECT COUNT(*) FROM tailoring_sessions").fetchone()[0]
            total_knowledge_profiles = conn.execute("SELECT COUNT(*) FROM career_knowledge_profiles").fetchone()[0]

            if total_sessions == 0:
                return {
                    "total_sessions": 0,
                    "total_knowledge_profiles": total_knowledge_profiles,
                    "total_tokens": 0,
                    "avg_execution_time": 0.0,
                    "top_job_titles": []
                }

            row_tokens = conn.execute(
                "SELECT SUM(token_count), AVG(execution_time_seconds) FROM tailoring_sessions"
            ).fetchone()
            total_tokens = row_tokens[0] or 0
            avg_time = row_tokens[1] or 0.0

            top_titles_rows = conn.execute(
                """
                SELECT target_job_title, COUNT(*) as cnt 
                FROM tailoring_sessions 
                GROUP BY target_job_title 
                ORDER BY cnt DESC 
                LIMIT 5
                """
            ).fetchall()
            top_titles = [{"title": r[0], "count": r[1]} for r in top_titles_rows]

            return {
                "total_sessions": total_sessions,
                "total_knowledge_profiles": total_knowledge_profiles,
                "total_tokens": total_tokens,
                "avg_execution_time": round(avg_time, 2),
                "top_job_titles": top_titles
            }


_GLOBAL_DB: Optional[ResumeDatabase] = None


def get_db(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> ResumeDatabase:
    """Singleton-style accessor for the local resume database."""
    global _GLOBAL_DB
    if _GLOBAL_DB is None or str(_GLOBAL_DB.db_path) != str(Path(db_path)):
        _GLOBAL_DB = ResumeDatabase(db_path=db_path)
    return _GLOBAL_DB
