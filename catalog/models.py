from dataclasses import dataclass


@dataclass(slots=True)
class Book:
    author: str
    title: str
    year: int
    id: int
    tags: list[str] | None = None

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "tags": self.tags,
        }
