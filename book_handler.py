import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent / "data" / "books.json"


@dataclass
class Book:
    author: str
    title: str
    year: int
    id: int
    tags: Optional[List[str]]

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "tags": self.tags,
        }


@dataclass
class Library:
    books: Dict[int, Book]

class Book_Handler:
    def __init__(self) -> None:
        self.library = Library(books={})
        self._next_id = 1

    def load_books_json(self) -> Optional[List[Book]]:
        """Load seed books from data/books.json."""
        if not DATA_PATH.exists():
            logger.error("JSON file not found: %s", DATA_PATH)
            return None
        try:
            with DATA_PATH.open(encoding="utf-8") as handle:
                raw_books = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to read seed books: %s", exc)
            return None

        books: List[Book] = []
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

    def load_books(self) -> bool:
        """Populate the in-memory library from JSON."""
        books = self.load_books_json()
        if books is None:
            return False
        self.library.books = {book.id: book for book in books}
        self._next_id = max(self.library.books, default=0) + 1
        logger.info("Loaded %s books into library", len(self.library.books))
        return True

    def create_book(self, title: str, author: str, year: int, tags: Optional[List[str]] = None) -> Book:
        """Creates a new book and assigns it a unique ID."""
        book = Book(
            id=self._next_id,
            title=title,
            author=author,
            year=year,
            tags=tags,
        )
        self.library.books[book.id] = book
        self._next_id += 1
        return book

    def list_books(self, author: Optional[str] = None, year: Optional[int] = None, title: Optional[str] = None,
                   offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        """Returns a list of books matching the given filters."""

        books = list(self.library.books.values())

        if author:
            author_filter = author.lower()
            books = [book for book in books if book.author.lower() == author_filter]

        if year is not None:
            books = [book for book in books if book.year == year]

        if title:
            title_query = title.lower()
            books = [book for book in books if title_query in book.title.lower()]

        total = len(books)
        page = books[offset : offset + limit]
        return {
            "books": page,
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """Returns a book by its ID, or None if not found."""
        return self.library.books.get(book_id)

    def delete_book_by_id(self, book_id: int) -> bool:
        """Deletes a book by its ID, returning True if successful."""
        if book_id not in self.library.books:
            return False
        del self.library.books[book_id]
        return True

    def get_stats(self) -> Dict[str, int]:
        """Returns statistics about the library."""
        return {
            "total_books": len(self.library.books),
            "unique_authors": len({book.author for book in self.library.books.values()}),
        }

book_handler = Book_Handler()