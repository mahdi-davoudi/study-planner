import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from config import DB_PATH
from utils.helpers import now_iso


class DatabaseManager:
    # Lifecycle
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.connect()

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = self._row_factory
            self.connection.execute("PRAGMA foreign_keys = ON")
            self._create_schema()
        except sqlite3.Error as e:
            raise ConnectionError(
                f"Could not open database file at {self.db_path}"
            ) from e

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    @staticmethod
    def _row_factory(cursor, row):
        data = {}
        for idx, col in enumerate(cursor.description):
            name = col[0]
            data["_id" if name == "id" else name] = row[idx]
        return data

    @contextmanager
    def _cursor(self):
        cur = self.connection.cursor()
        try:
            yield cur
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cur.close()

    def _create_schema(self):
        with self._cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    name       TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    date             TEXT NOT NULL,
                    subject_id       INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
                    subject_name     TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    note             TEXT DEFAULT '',
                    created_at       TEXT NOT NULL
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_date ON logs(date)")

    # Subjects
    def add_subject(self, name: str) -> Optional[int]:
        name = name.strip()
        if not name:
            return None

        existing = self._fetch_one(
            "SELECT id AS _id FROM subjects WHERE name = ?", (name,)
        )
        if existing:
            return existing["_id"]

        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO subjects (name, created_at) VALUES (?, ?)",
                (name, now_iso()),
            )
            return cur.lastrowid

    def get_subjects(self) -> List[Dict[str, Any]]:
        return self._fetch_all(
            "SELECT id AS _id, name, created_at FROM subjects ORDER BY name ASC"
        )

    def delete_subject(self, subject_id) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

    def rename_subject(self, subject_id, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            return
        with self._cursor() as cur:
            cur.execute(
                "UPDATE subjects SET name = ? WHERE id = ?",
                (new_name, subject_id),
            )

    # Study Logs
    def add_log(
        self,
        date: str,
        subject_id,
        subject_name: str,
        duration_minutes: int,
        note: str = "",
    ) -> Optional[int]:
        if duration_minutes <= 0:
            return None

        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO logs (date, subject_id, subject_name, duration_minutes, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (date, subject_id, subject_name, duration_minutes, note, now_iso()),
            )
            return cur.lastrowid

    def add_logs_bulk(self, date: str, entries: list) -> int:
        rows = []
        for e in entries:
            if e["duration_minutes"] <= 0:
                continue
            rows.append((
                date,
                e.get("subject_id"),
                e["subject_name"],
                e["duration_minutes"],
                e.get("note", ""),
                now_iso(),
            ))

        if not rows:
            return 0

        with self._cursor() as cur:
            cur.executemany(
                """
                INSERT INTO logs (date, subject_id, subject_name, duration_minutes, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def get_logs_by_date(self, date: str) -> List[Dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id AS _id, date, subject_id, subject_name, duration_minutes, note, created_at
            FROM logs WHERE date = ? ORDER BY subject_name ASC
            """,
            (date,),
        )

    def get_logs_between(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id AS _id, date, subject_id, subject_name, duration_minutes, note, created_at
            FROM logs WHERE date BETWEEN ? AND ? ORDER BY date ASC
            """,
            (start_date, end_date),
        )

    def get_all_logs(self) -> List[Dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id AS _id, date, subject_id, subject_name, duration_minutes, note, created_at
            FROM logs ORDER BY date DESC
            """
        )

    def delete_log(self, log_id) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM logs WHERE id = ?", (log_id,))

    def update_log_duration(self, log_id, new_duration_minutes: int) -> None:
        if new_duration_minutes <= 0:
            return
        with self._cursor() as cur:
            cur.execute(
                "UPDATE logs SET duration_minutes = ? WHERE id = ?",
                (new_duration_minutes, log_id),
            )

    # Reporting / analytics
    def get_summary_by_subject(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT subject_name, SUM(duration_minutes) AS total_minutes
            FROM logs
        """
        params: tuple = ()
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params = (start_date, end_date)
        query += " GROUP BY subject_name ORDER BY total_minutes DESC"

        rows = self._fetch_all(query, params)
        return [
            {"subject_name": r["subject_name"], "total_minutes": r["total_minutes"]}
            for r in rows
        ]

    def get_subject_percentages(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        summary = self.get_summary_by_subject(start_date, end_date)
        total = sum(item["total_minutes"] for item in summary)

        result = []
        for item in summary:
            percentage = (item["total_minutes"] / total * 100) if total else 0
            result.append({
                "subject_name": item["subject_name"],
                "total_minutes": item["total_minutes"],
                "percentage": round(percentage, 1),
            })
        return result

    def get_daily_totals(self, start_date: str, end_date: str) -> Dict[str, int]:
        rows = self._fetch_all(
            """
            SELECT date, SUM(duration_minutes) AS total_minutes
            FROM logs WHERE date BETWEEN ? AND ?
            GROUP BY date
            """,
            (start_date, end_date),
        )
        return {r["date"]: r["total_minutes"] for r in rows}

    def get_total_minutes(self, start_date: str = None, end_date: str = None) -> int:
        query = "SELECT SUM(duration_minutes) AS total_minutes FROM logs"
        params: tuple = ()
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params = (start_date, end_date)

        row = self._fetch_one(query, params)
        return row["total_minutes"] or 0 if row else 0

    def get_current_streak(self) -> int:
        streak = 0
        day = datetime.now()

        while True:
            date_str = day.strftime("%Y-%m-%d")
            total = self.get_total_minutes(date_str, date_str)
            if total and total > 0:
                streak += 1
                day -= timedelta(days=1)
            else:
                break

        return streak

    def get_week_total(self) -> int:
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        return self.get_total_minutes(
            start_of_week.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d"),
        )

    def get_month_total(self) -> int:
        today = datetime.now()
        start_of_month = today.replace(day=1)
        return self.get_total_minutes(
            start_of_month.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d"),
        )

    # Internal helpers
    def _fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()