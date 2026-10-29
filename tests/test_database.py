from datetime import date, timedelta

import pytest

from database import DatabaseManager


@pytest.fixture
def db():
    manager = DatabaseManager(":memory:")
    yield manager
    manager.close()


def test_streak_counts_from_yesterday_if_today_empty(db):
    sid = db.add_subject("Math")
    for d in (1, 2, 3):
        db.add_log((date.today() - timedelta(days=d)).isoformat(), sid, "Math", 30)
    assert db.get_current_streak() == 3


def test_streak_zero_when_gap(db):
    sid = db.add_subject("Math")
    db.add_log((date.today() - timedelta(days=3)).isoformat(), sid, "Math", 30)
    assert db.get_current_streak() == 0


def test_rename_updates_logs(db):
    sid = db.add_subject("Math")
    db.add_log(date.today().isoformat(), sid, "Math", 30)
    assert db.rename_subject(sid, "Calculus")
    assert db.get_summary_by_subject()[0]["subject_name"] == "Calculus"


def test_rename_duplicate_returns_false(db):
    a = db.add_subject("A")
    db.add_subject("B")
    assert db.rename_subject(a, "B") is False


def test_bulk_upsert_merges_same_day(db):
    sid = db.add_subject("Math")
    day = date.today().isoformat()
    entry = [{"subject_id": sid, "subject_name": "Math", "duration_minutes": 30}]
    db.add_logs_bulk(day, entry)
    db.add_logs_bulk(day, entry)
    assert len(db.get_logs_by_date(day)) == 1
    assert db.get_total_minutes(day, day) == 60


def test_percentages(db):
    a, b = db.add_subject("A"), db.add_subject("B")
    day = date.today().isoformat()
    db.add_log(day, a, "A", 75)
    db.add_log(day, b, "B", 25)
    result = {r["subject_name"]: r["percentage"] for r in db.get_subject_percentages()}
    assert result == {"A": 75.0, "B": 25.0}
