"""Unit tests for in-memory Book_Handler and Book."""
from book_handler import Book, Book_Handler

SEED_COUNT = 12
SEED_UNIQUE_AUTHORS = 11


class TestBook:
    def test_to_json_includes_all_fields(self) -> None:
        book = Book(
            id=7,
            title="Hyperion",
            author="Dan Simmons",
            year=1989,
            tags=["science fiction"],
        )
        assert book.to_json() == {
            "id": 7,
            "title": "Hyperion",
            "author": "Dan Simmons",
            "year": 1989,
            "tags": ["science fiction"],
        }


class TestLoadBooks:
    def test_load_books_populates_library_from_json(self, catalog: Book_Handler) -> None:
        assert len(catalog.library.books) == SEED_COUNT
        first = catalog.get_book_by_id(1)
        assert first is not None
        assert first.title == "Neuromancer"
        assert first.year == 1984
        assert catalog._next_id == SEED_COUNT + 1

    def test_load_books_maps_release_year_and_optional_tags(self, catalog: Book_Handler) -> None:
        kindred = catalog.get_book_by_id(2)
        assert kindred is not None
        assert kindred.title == "Kindred"
        assert kindred.year == 1979
        assert kindred.tags is None

    def test_load_books_json_returns_none_when_file_missing(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("book_handler.DATA_PATH", tmp_path / "missing.json")
        handler = Book_Handler()
        assert handler.load_books_json() is None
        assert handler.load_books() is False
        assert handler.library.books == {}

    def test_load_books_json_returns_none_for_invalid_json(self, tmp_path, monkeypatch) -> None:
        bad_file = tmp_path / "books.json"
        bad_file.write_text("{not-json", encoding="utf-8")
        monkeypatch.setattr("book_handler.DATA_PATH", bad_file)
        handler = Book_Handler()
        assert handler.load_books_json() is None
        assert handler.load_books() is False

    def test_load_books_replaces_existing_catalog(self, catalog: Book_Handler) -> None:
        catalog.create_book("Temporary", "Someone", 2000)
        assert catalog.load_books() is True
        assert catalog.get_stats()["total_books"] == SEED_COUNT
        assert catalog.get_book_by_id(SEED_COUNT + 1) is None


class TestCreateAndGet:
    def test_create_book_assigns_unique_integer_ids(self, empty_catalog: Book_Handler) -> None:
        first = empty_catalog.create_book("A", "Author A", 2000, ["x"])
        second = empty_catalog.create_book("B", "Author B", 2001)
        assert first.id == 1
        assert second.id == 2
        assert empty_catalog.get_book_by_id(1) is first
        assert empty_catalog.get_book_by_id(2) is second

    def test_get_book_by_id_returns_none_when_missing(self, empty_catalog: Book_Handler) -> None:
        assert empty_catalog.get_book_by_id(1) is None

    def test_ids_are_not_reused_after_delete(self, empty_catalog: Book_Handler) -> None:
        empty_catalog.create_book("A", "Author", 2000)
        assert empty_catalog.delete_book_by_id(1) is True
        replacement = empty_catalog.create_book("B", "Author", 2001)
        assert replacement.id == 2
        assert empty_catalog.get_book_by_id(1) is None


class TestDelete:
    def test_delete_book_by_id_returns_false_when_missing(self, empty_catalog: Book_Handler) -> None:
        assert empty_catalog.delete_book_by_id(99) is False

    def test_delete_book_by_id_removes_book(self, catalog: Book_Handler) -> None:
        assert catalog.delete_book_by_id(1) is True
        assert catalog.get_book_by_id(1) is None
        assert catalog.get_stats()["total_books"] == SEED_COUNT - 1


class TestListBooks:
    def test_list_books_default_pagination(self, catalog: Book_Handler) -> None:
        result = catalog.list_books()
        assert result["total"] == SEED_COUNT
        assert result["offset"] == 0
        assert result["limit"] == 10
        assert len(result["books"]) == 10

    def test_list_books_filters_author_case_insensitively(self, catalog: Book_Handler) -> None:
        result = catalog.list_books(author="OCTAVIA E. BUTLER", limit=100)
        titles = [book.title for book in result["books"]]
        assert result["total"] == 2
        assert "Kindred" in titles
        assert "Parable of the Sower" in titles

    def test_list_books_filters_by_year(self, catalog: Book_Handler) -> None:
        result = catalog.list_books(year=2018)
        assert result["total"] == 2
        assert {book.year for book in result["books"]} == {2018}

    def test_list_books_title_search_is_substring(self, catalog: Book_Handler) -> None:
        result = catalog.list_books(title="HAIL")
        assert result["total"] == 1
        assert result["books"][0].title == "Project Hail Mary"

    def test_list_books_combines_filters(self, catalog: Book_Handler) -> None:
        result = catalog.list_books(author="Octavia E. Butler", year=1979)
        assert result["total"] == 1
        assert result["books"][0].title == "Kindred"

    def test_list_books_empty_catalog(self, empty_catalog: Book_Handler) -> None:
        result = empty_catalog.list_books()
        assert result == {"books": [], "total": 0, "offset": 0, "limit": 10}


class TestStats:
    def test_stats_count_unique_authors(self, catalog: Book_Handler) -> None:
        assert catalog.get_stats() == {
            "total_books": SEED_COUNT,
            "unique_authors": SEED_UNIQUE_AUTHORS,
        }

    def test_stats_on_empty_library(self, empty_catalog: Book_Handler) -> None:
        assert empty_catalog.get_stats() == {"total_books": 0, "unique_authors": 0}

    def test_stats_do_not_count_duplicate_authors_twice(self, empty_catalog: Book_Handler) -> None:
        empty_catalog.create_book("One", "Same Author", 2000)
        empty_catalog.create_book("Two", "Same Author", 2001)
        assert empty_catalog.get_stats() == {"total_books": 2, "unique_authors": 1}
