"""SQLite storage layer for subjects and study logs (no GUI dependencies)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, timedelta
from typing import Any

from config import DB_PATH
from utils.helpers import now_iso

Row = dict[str, Any]

_LOG_COLUMNS = "id AS _id, date, subject_id, subject_name, duration_minutes, note, created_at"


class DatabaseManager:
    """Thin wrapper around a SQLite connection.

    Rows are returned as dicts; the ``id`` column is exposed as ``_id`` so the
    API stays compatible with the old MongoDB backend.
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self.connection: sqlite3.Connection | None = None
        self.connect()

    def connect(self) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = self._row_factory
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            self.connection = conn
            self._create_schema()
        except sqlite3.Error as exc:
            raise ConnectionError(
                f"Could not open database file at {self.db_path}"
            ) from exc

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    @property
    def _conn(self) -> sqlite3.Connection:
        if self.connection is None:
            raise RuntimeError("The database connection is closed.")
        return self.connection

    @staticmethod
    def _row_factory(cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> Row:
        return {
            ("_id" if col[0] == "id" else col[0]): row[idx]
            for idx, col in enumerate(cursor.description)
        }

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    def _create_schema(self) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
                    subject_name TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    note TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_date ON logs(date)")

    # ------------------------------------------------------------------
    # Subjects
    # ------------------------------------------------------------------
    def add_subject(self, name: str) -> int | None:
        """Create a subject (or return the id of the existing one)."""
        name = name.strip()
        if not name:
            return None

        existing = self._fetch_one(
            "SELECT id AS _id FROM subjects WHERE name = ?", (name,)
        )
        if existing:
            return int(existing["_id"])

        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO subjects (name, created_at) VALUES (?, ?)",
                (name, now_iso()),
            )
            return cur.lastrowid

    def get_subjects(self) -> list[Row]:
        return self._fetch_all(
            "SELECT id AS _id, name, created_at FROM subjects ORDER BY name ASC"
        )

    def delete_subject(self, subject_id: int) -> None:
        """Delete a subject; its logs are kept (subject_id becomes NULL)."""
        with self._cursor() as cur:
            cur.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))

    def rename_subject(self, subject_id: int, new_name: str) -> bool:
        """Rename a subject and its past logs.

        Returns False if the name is empty or already used by another subject.
        """
        new_name = new_name.strip()
        if not new_name:
            return False
        try:
            with self._cursor() as cur:
                cur.execute(
                    "UPDATE subjects SET name = ? WHERE id = ?",
                    (new_name, subject_id),
                )
                cur.execute(
                    "UPDATE logs SET subject_name = ? WHERE subject_id = ?",
                    (new_name, subject_id),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    # ------------------------------------------------------------------
    # Study logs
    # ------------------------------------------------------------------
    def add_log(
        self,
        date: str,
        subject_id: int | None,
        subject_name: str,
        duration_minutes: int,
        note: str = "",
    ) -> int | None:
        if duration_minutes <= 0:
            return None
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO logs
                    (date, subject_id, subject_name, duration_minutes, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (date, subject_id, subject_name, duration_minutes, note, now_iso()),
            )
            return cur.lastrowid

    def add_logs_bulk(self, date: str, entries: list[Row]) -> int:
        """Save several subjects for one day.

        If a subject already has a record for that day, the minutes are added
        to it instead of creating a duplicate row. Returns the number of
        subjects saved.
        """
        saved = 0
        with self._cursor() as cur:
            for entry in entries:
                minutes = int(entry["duration_minutes"])
                if minutes <= 0:
                    continue
                subject_id = entry.get("subject_id")
                name = entry["subject_name"]
                cur.execute(
                    "SELECT id AS _id FROM logs "
                    "WHERE date = ? AND subject_id IS ? AND subject_name = ?",
                    (date, subject_id, name),
                )
                row = cur.fetchone()
                if row:
                    cur.execute(
                        "UPDATE logs SET duration_minutes = duration_minutes + ? "
                        "WHERE id = ?",
                        (minutes, row["_id"]),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO logs
                            (date, subject_id, subject_name, duration_minutes,
                             note, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (date, subject_id, name, minutes, entry.get("note", ""), now_iso()),
                    )
                saved += 1
        return saved

    def get_logs_by_date(self, date: str) -> list[Row]:
        return self._fetch_all(
            f"SELECT {_LOG_COLUMNS} FROM logs WHERE date = ? "
            "ORDER BY subject_name ASC",
            (date,),
        )

    def get_logs_between(self, start_date: str, end_date: str) -> list[Row]:
        return self._fetch_all(
            f"SELECT {_LOG_COLUMNS} FROM logs WHERE date BETWEEN ? AND ? "
            "ORDER BY date ASC",
            (start_date, end_date),
        )

    def get_all_logs(self) -> list[Row]:
        return self._fetch_all(f"SELECT {_LOG_COLUMNS} FROM logs ORDER BY date DESC")

    def delete_log(self, log_id: int) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM logs WHERE id = ?", (log_id,))

    def update_log_duration(self, log_id: int, new_duration_minutes: int) -> None:
        if new_duration_minutes <= 0:
            return
        with self._cursor() as cur:
            cur.execute(
                "UPDATE logs SET duration_minutes = ? WHERE id = ?",
                (new_duration_minutes, log_id),
            )

    # ------------------------------------------------------------------
    # Reporting / analytics
    # ------------------------------------------------------------------
    def get_summary_by_subject(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[Row]:
        query = "SELECT subject_name, SUM(duration_minutes) AS total_minutes FROM logs"
        params: tuple[str, ...] = ()
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params = (start_date, end_date)
        query += " GROUP BY subject_name ORDER BY total_minutes DESC, subject_name ASC"
        return self._fetch_all(query, params)

    def get_subject_percentages(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> list[Row]:
        summary = self.get_summary_by_subject(start_date, end_date)
        total = sum(item["total_minutes"] for item in summary)
        return [
            {
                "subject_name": item["subject_name"],
                "total_minutes": item["total_minutes"],
                "percentage": round(item["total_minutes"] / total * 100, 1) if total else 0,
            }
            for item in summary
        ]

    def get_daily_totals(self, start_date: str, end_date: str) -> dict[str, int]:
        rows = self._fetch_all(
            "SELECT date, SUM(duration_minutes) AS total_minutes FROM logs "
            "WHERE date BETWEEN ? AND ? GROUP BY date",
            (start_date, end_date),
        )
        return {r["date"]: r["total_minutes"] for r in rows}

    def get_total_minutes(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> int:
        query = "SELECT SUM(duration_minutes) AS total_minutes FROM logs"
        params: tuple[str, ...] = ()
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params = (start_date, end_date)
        row = self._fetch_one(query, params)
        return int(row["total_minutes"] or 0) if row else 0

    def get_current_streak(self, today: date | None = None) -> int:
        """Consecutive study days ending today (or yesterday if today is empty)."""
        today = today or date.today()
        rows = self._fetch_all(
            "SELECT DISTINCT date FROM logs WHERE duration_minutes > 0 AND date <= ?",
            (today.isoformat(),),
        )
        days: set[date] = set()
        for row in rows:
            try:
                days.add(date.fromisoformat(row["date"]))
            except ValueError:
                continue

        cursor = today if today in days else today - timedelta(days=1)
        streak = 0
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def get_week_total(self) -> int:
        today = date.today()
        start = today - timedelta(days=today.weekday())
        return self.get_total_minutes(start.isoformat(), today.isoformat())

    def get_month_total(self) -> int:
        today = date.today()
        return self.get_total_minutes(today.replace(day=1).isoformat(), today.isoformat())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[Row]:
        with self._cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def _fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> Row | None:
        with self._cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()
