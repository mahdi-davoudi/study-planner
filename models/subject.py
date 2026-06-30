class Subject:
    def __init__(self, name: str, _id=None):
        self.id = _id
        self.name = name

    @staticmethod
    def from_doc(doc: dict) -> "Subject":
        return Subject(name=doc.get("name", ""), _id=doc.get("_id"))

    def __repr__(self):
        return f"Subject(id={self.id}, name={self.name!r})"