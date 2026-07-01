from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId
from config import (
    MONGO_HOST, MONGO_PORT, DB_NAME,
    SUBJECTS_COLLECTION, LOGS_COLLECTION
)
from utils.helpers import now_iso


class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(
                MONGO_HOST, MONGO_PORT, serverSelectionTimeoutMS=3000
            )
            self.client.admin.command("ping")
            self.db = self.client[DB_NAME]
        except ConnectionFailure as e:
            raise ConnectionError(
                f"{MONGO_HOST}:{MONGO_PORT} is running"
            ) from e

    # ---------------------------------------------------------------------
    # Subjects
    # ---------------------------------------------------------------------
    def add_subject(self, name: str):
        name = name.strip()
        if not name:
            return None
        existing = self.db[SUBJECTS_COLLECTION].find_one({"name": name})
        if existing:
            return existing["_id"]
        result = self.db[SUBJECTS_COLLECTION].insert_one({
            "name": name,
            "created_at": now_iso(),
        })
        return result.inserted_id

    def get_subjects(self):
        cursor = self.db[SUBJECTS_COLLECTION].find().sort("name", 1)
        return list(cursor)

    def delete_subject(self, subject_id):
        self.db[SUBJECTS_COLLECTION].delete_one({"_id": ObjectId(subject_id)})

    def rename_subject(self, subject_id, new_name: str):
        new_name = new_name.strip()
        if not new_name:
            return
        self.db[SUBJECTS_COLLECTION].update_one(
            {"_id": ObjectId(subject_id)},
            {"$set": {"name": new_name}}
        )

    # ---------------------------------------------------------------------
    # Study Logs
    # ---------------------------------------------------------------------
    def add_log(self, date: str, subject_id, subject_name: str, duration_minutes: int, note: str = ""):
        if duration_minutes <= 0:
            return None
        doc = {
            "date": date,
            "subject_id": ObjectId(subject_id) if subject_id else None,
            "subject_name": subject_name,
            "duration_minutes": duration_minutes,
            "note": note,
            "created_at": now_iso(),
        }
        result = self.db[LOGS_COLLECTION].insert_one(doc)
        return result.inserted_id

    def add_logs_bulk(self, date: str, entries: list):
        docs = []
        for e in entries:
            if e["duration_minutes"] <= 0:
                continue
            docs.append({
                "date": date,
                "subject_id": ObjectId(e["subject_id"]) if e.get("subject_id") else None,
                "subject_name": e["subject_name"],
                "duration_minutes": e["duration_minutes"],
                "note": e.get("note", ""),
                "created_at": now_iso(),
            })
        if docs:
            self.db[LOGS_COLLECTION].insert_many(docs)
        return len(docs)

    def get_logs_by_date(self, date: str):
        cursor = self.db[LOGS_COLLECTION].find({"date": date}).sort("subject_name", 1)
        return list(cursor)

    def get_logs_between(self, start_date: str, end_date: str):
        cursor = self.db[LOGS_COLLECTION].find({
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("date", 1)
        return list(cursor)

    def get_all_logs(self):
        cursor = self.db[LOGS_COLLECTION].find().sort("date", -1)
        return list(cursor)

    def delete_log(self, log_id):
        self.db[LOGS_COLLECTION].delete_one({"_id": ObjectId(log_id)})

    def update_log_duration(self, log_id, new_duration_minutes: int):
        if new_duration_minutes <= 0:
            return
        self.db[LOGS_COLLECTION].update_one(
            {"_id": ObjectId(log_id)},
            {"$set": {"duration_minutes": new_duration_minutes}}
        )

    def get_summary_by_subject(self, start_date: str = None, end_date: str = None):

        match_stage = {}
        if start_date and end_date:
            match_stage["date"] = {"$gte": start_date, "$lte": end_date}

        pipeline = []
        if match_stage:
            pipeline.append({"$match": match_stage})
        pipeline.extend([
            {"$group": {
                "_id": "$subject_name",
                "total_minutes": {"$sum": "$duration_minutes"}
            }},
            {"$sort": {"total_minutes": -1}}
        ])
        results = list(self.db[LOGS_COLLECTION].aggregate(pipeline))
        return [{"subject_name": r["_id"], "total_minutes": r["total_minutes"]} for r in results]

    # ---------------------------------------------------------------------
    # Reporting / analytics helpers
    # ---------------------------------------------------------------------
    def get_subject_percentages(self, start_date: str = None, end_date: str = None):
        """
        Return the study summary per subject, each entry annotated with its
        percentage share of the total study time in the given range.
        """
        summary = self.get_summary_by_subject(start_date, end_date)
        total = sum(item["total_minutes"] for item in summary)

        result = []
        for item in summary:
            percentage = (item["total_minutes"] / total * 100) if total > 0 else 0
            result.append({
                "subject_name": item["subject_name"],
                "total_minutes": item["total_minutes"],
                "percentage": percentage,
            })
        return result

    def get_total_minutes(self, start_date: str = None, end_date: str = None):
        """Return the total study minutes in the given date range (or all time)."""
        match_stage = {}
        if start_date and end_date:
            match_stage["date"] = {"$gte": start_date, "$lte": end_date}

        pipeline = []
        if match_stage:
            pipeline.append({"$match": match_stage})
        pipeline.append({"$group": {"_id": None, "total_minutes": {"$sum": "$duration_minutes"}}})

        results = list(self.db[LOGS_COLLECTION].aggregate(pipeline))
        return results[0]["total_minutes"] if results else 0

    def get_daily_totals(self, start_date: str, end_date: str):
        """
        Return a dict mapping 'YYYY-MM-DD' -> total study minutes for that day,
        for every day in the range that has at least one log. Used to feed the
        study activity heatmap.
        """
        pipeline = [
            {"$match": {"date": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {"_id": "$date", "total_minutes": {"$sum": "$duration_minutes"}}},
        ]
        results = list(self.db[LOGS_COLLECTION].aggregate(pipeline))
        return {r["_id"]: r["total_minutes"] for r in results}

    def get_current_streak(self):
        """
        Return the current study streak in days: the number of consecutive
        days (ending today) that have at least one study log.
        """
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

    def get_week_total(self):
        """Return total study minutes for the current week (Monday to today)."""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        return self.get_total_minutes(
            start_of_week.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d")
        )

    def get_month_total(self):
        """Return total study minutes for the current calendar month."""
        today = datetime.now()
        start_of_month = today.replace(day=1)
        return self.get_total_minutes(
            start_of_month.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d")
        )

    def close(self):
        if self.client:
            self.client.close()