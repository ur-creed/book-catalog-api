from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Protocol

from catalog.models import Book

logger = logging.getLogger(__name__)


class BookCatalog(Protocol):
    """Persistence seam. HTTP depends on this, not on the dict implementation."""

    def load_seed(self) -> bool: ...

    def create_book(
        self,
        title: str,
        author: str,
        year: int,
        tags: list[str] | None = None,
    ) -> Book: ...

    def list_books(
        self,
        author: str | None = None,
        year: int | None = None,
        title: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> dict[str, Any]: ...

    def get_book_by_id(self, book_id: int) -> Book | None: ...

    def delete_book_by_id(self, book_id: int) -> bool: ...

    def get_stats(self) -> dict[str, int]: ...


class InMemoryCatalog:
    """Process-lifetime store. Seed JSON is the starting snapshot, not a database."""

    def __init__(self, seed_path: Path) -> None:
        self._seed_path = seed_path
        self._books: dict[int, Book] = {}
        self._next_id = 1

    def load_seed(self) -> bool:
        books = self._read_seed()
        if books is None:
            return False
        self._books = {book.id: book for book in books}
        self._next_id = max(self._books, default=0) + 1
        logger.info("Loaded %s books from %s", len(self._books), self._seed_path)
        return True

    def _read_seed(self) -> list[Book] | None:
        if not self._seed_path.exists():
            logger.error("Seed file not found: %s", self._seed_path)
            return None
        try:
            raw_books = json.loads(self._seed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to read seed books: %s", exc)
            return None

        books: list[Book] = []
        for index, item in enumerate(raw_books, start=1):
            books.append(
                Book(
                    id=index,
                    title=item["title"],
                    author=item["author"],
                    year=item["release_year"],
                    tags=item.get("tags"),
                )
            )
        return books

    def create_book(
        self,
        title: str,
        author: str,
        year: int,
        tags: list[str] | None = None,
    ) -> Book:
        book = Book(
            id=self._next_id,
            title=title,
            author=author,
            year=year,
            tags=tags,
        )
        self._books[book.id] = book
        self._next_id += 1
        return book

    def list_books(
        self,
        author: str | None = None,
        year: int | None = None,
        title: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> dict[str, Any]:
        books = list(self._books.values())

        if author:
            author_filter = author.lower()
            books = [book for book in books if book.author.lower() == author_filter]
        if year is not None:
            books = [book for book in books if book.year == year]
        if title:
            title_query = title.lower()
            books = [book for book in books if title_query in book.title.lower()]

        total = len(books)
        return {
            "books": books[offset : offset + limit],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def get_book_by_id(self, book_id: int) -> Book | None:
        return self._books.get(book_id)

    def delete_book_by_id(self, book_id: int) -> bool:
        if book_id not in self._books:
            return False
        del self._books[book_id]
        return True

    def get_stats(self) -> dict[str, int]:
        return {
            "total_books": len(self._books),
            "unique_authors": len({book.author for book in self._books.values()}),
        }
