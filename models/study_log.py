class StudyLog:
    def __init__(self, date: str, subject_id, subject_name: str,
                 duration_minutes: int, note: str = "", _id=None,
                 created_at: str = None):
        self.id = _id
        self.date = date
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.duration_minutes = duration_minutes
        self.note = note
        self.created_at = created_at

    @staticmethod
    def from_doc(doc: dict) -> "StudyLog":
        return StudyLog(
            _id=doc.get("_id"),
            date=doc.get("date"),
            subject_id=doc.get("subject_id"),
            subject_name=doc.get("subject_name"),
            duration_minutes=doc.get("duration_minutes", 0),
            note=doc.get("note", ""),
            created_at=doc.get("created_at"),
        )

    def to_doc(self) -> dict:
        return {
            "date": self.date,
            "subject_id": self.subject_id,
            "subject_name": self.subject_name,
            "duration_minutes": self.duration_minutes,
            "note": self.note,
            "created_at": self.created_at,
        }

    def __repr__(self):
        return (f"StudyLog(date={self.date}, subject={self.subject_name!r}, "
                f"minutes={self.duration_minutes})")