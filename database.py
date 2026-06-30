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
    # عملیات روی درس‌ها (Subjects)
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
    # عملیات روی ثبت مطالعه روزانه (Study Logs)
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

    def close(self):
        if self.client:
            self.client.close()