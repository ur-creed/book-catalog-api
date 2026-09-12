from catalog.models import Book
from catalog.store import InMemoryCatalog

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


class TestLoadSeed:
    def test_load_seed_populates_catalog(self, catalog: InMemoryCatalog) -> None:
        assert catalog.get_stats()["total_books"] == SEED_COUNT
        first = catalog.get_book_by_id(1)
        assert first is not None
        assert first.title == "Meditations"
        assert first.year == 180
        assert catalog._next_id == SEED_COUNT + 1

    def test_load_seed_maps_release_year_and_optional_tags(
        self, catalog: InMemoryCatalog
    ) -> None:
        handbook = catalog.get_book_by_id(2)
        assert handbook is not None
        assert handbook.title == "Enchiridion"
        assert handbook.year == 125
        assert handbook.tags is None

    def test_load_seed_returns_false_when_file_missing(
        self, empty_catalog: InMemoryCatalog
    ) -> None:
        assert empty_catalog.load_seed() is False
        assert empty_catalog.get_stats()["total_books"] == 0

    def test_load_seed_returns_false_for_invalid_json(self, tmp_path) -> None:
        bad_file = tmp_path / "books.json"
        bad_file.write_text("{not-json", encoding="utf-8")
        store = InMemoryCatalog(bad_file)
        assert store.load_seed() is False

    def test_load_seed_replaces_existing_catalog(self, catalog: InMemoryCatalog) -> None:
        catalog.create_book("Temporary", "Someone", 2000)
        assert catalog.load_seed() is True
        assert catalog.get_stats()["total_books"] == SEED_COUNT
        assert catalog.get_book_by_id(SEED_COUNT + 1) is None


class TestCreateAndGet:
    def test_create_book_assigns_unique_integer_ids(
        self, empty_catalog: InMemoryCatalog
    ) -> None:
        first = empty_catalog.create_book("A", "Author A", 2000, ["x"])
        second = empty_catalog.create_book("B", "Author B", 2001)
        assert first.id == 1
        assert second.id == 2
        assert empty_catalog.get_book_by_id(1) is first
        assert empty_catalog.get_book_by_id(2) is second

    def test_get_book_by_id_returns_none_when_missing(
        self, empty_catalog: InMemoryCatalog
    ) -> None:
        assert empty_catalog.get_book_by_id(1) is None

    def test_ids_are_not_reused_after_delete(self, empty_catalog: InMemoryCatalog) -> None:
        empty_catalog.create_book("A", "Author", 2000)
        assert empty_catalog.delete_book_by_id(1) is True
        replacement = empty_catalog.create_book("B", "Author", 2001)
        assert replacement.id == 2
        assert empty_catalog.get_book_by_id(1) is None


class TestDelete:
    def test_delete_book_by_id_returns_false_when_missing(
        self, empty_catalog: InMemoryCatalog
    ) -> None:
        assert empty_catalog.delete_book_by_id(99) is False

    def test_delete_book_by_id_removes_book(self, catalog: InMemoryCatalog) -> None:
        assert catalog.delete_book_by_id(1) is True
        assert catalog.get_book_by_id(1) is None
        assert catalog.get_stats()["total_books"] == SEED_COUNT - 1


class TestListBooks:
    def test_list_books_default_pagination(self, catalog: InMemoryCatalog) -> None:
        result = catalog.list_books()
        assert result["total"] == SEED_COUNT
        assert result["offset"] == 0
        assert result["limit"] == 10
        assert len(result["books"]) == 10

    def test_list_books_filters_author_case_insensitively(
        self, catalog: InMemoryCatalog
    ) -> None:
        result = catalog.list_books(author="MADELINE MILLER", limit=100)
        titles = [book.title for book in result["books"]]
        assert result["total"] == 2
        assert "Circe" in titles
        assert "The Song of Achilles" in titles

    def test_list_books_filters_by_year(self, catalog: InMemoryCatalog) -> None:
        result = catalog.list_books(year=1969)
        assert result["total"] == 2
        assert {book.year for book in result["books"]} == {1969}

    def test_list_books_title_search_is_substring(self, catalog: InMemoryCatalog) -> None:
        result = catalog.list_books(title="ENCHIRIDION")
        assert result["total"] == 1
        assert result["books"][0].title == "Enchiridion"

    def test_list_books_combines_filters(self, catalog: InMemoryCatalog) -> None:
        result = catalog.list_books(author="Madeline Miller", year=2018)
        assert result["total"] == 1
        assert result["books"][0].title == "Circe"

    def test_list_books_empty_catalog(self, empty_catalog: InMemoryCatalog) -> None:
        result = empty_catalog.list_books()
        assert result == {"books": [], "total": 0, "offset": 0, "limit": 10}


class TestStats:
    def test_stats_count_unique_authors(self, catalog: InMemoryCatalog) -> None:
        assert catalog.get_stats() == {
            "total_books": SEED_COUNT,
            "unique_authors": SEED_UNIQUE_AUTHORS,
        }

    def test_stats_on_empty_library(self, empty_catalog: InMemoryCatalog) -> None:
        assert empty_catalog.get_stats() == {"total_books": 0, "unique_authors": 0}

    def test_stats_do_not_count_duplicate_authors_twice(
        self, empty_catalog: InMemoryCatalog
    ) -> None:
        empty_catalog.create_book("One", "Same Author", 2000)
        empty_catalog.create_book("Two", "Same Author", 2001)
        assert empty_catalog.get_stats() == {"total_books": 2, "unique_authors": 1}
