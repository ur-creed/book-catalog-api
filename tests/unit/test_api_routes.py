"""HTTP tests for Book Catalog API endpoints."""
from datetime import datetime

from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.routers.books import CreateBooksRequest

SEED_COUNT = 12
SEED_UNIQUE_AUTHORS = 11


class TestDocs:
    def test_openapi_includes_catalog_paths(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        paths = response.json()["paths"]
        assert "/books/" in paths
        assert "/books/{book_id}" in paths
        assert "/stats" in paths

    def test_swagger_ui_is_available(self, client: TestClient) -> None:
        response = client.get("/docs")
        assert response.status_code == 200

    def test_root_redirects_to_docs(self, client: TestClient) -> None:
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (302, 307)
        assert response.headers["location"] == "/docs"


class TestCreateBookValidation:
    def test_year_validator_rejects_year_below_1400(self) -> None:
        try:
            CreateBooksRequest.year_in_range(1399)
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert "1400" in str(exc)

    def test_tags_validator_returns_none(self) -> None:
        assert CreateBooksRequest.tags_are_labels(None) is None

    def test_required_text_rejects_empty_string(self) -> None:
        class FieldInfo:
            field_name = "title"

        try:
            CreateBooksRequest.required_text("", FieldInfo())
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert "title is required" in str(exc)

    def test_model_rejects_missing_required_fields(self) -> None:
        try:
            CreateBooksRequest.model_validate({})
            raise AssertionError("expected ValidationError")
        except ValidationError as exc:
            fields = {err["loc"][-1] for err in exc.errors()}
            assert {"title", "author", "year"} <= fields


class TestCreateBook:
    def test_create_book_returns_201_with_generated_id(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={
                "title": "The Name of the Rose",
                "author": "Umberto Eco",
                "year": 1980,
                "tags": ["mystery", "historical"],
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["id"] == SEED_COUNT + 1
        assert body["title"] == "The Name of the Rose"
        assert body["author"] == "Umberto Eco"
        assert body["year"] == 1980
        assert body["tags"] == ["mystery", "historical"]

    def test_create_book_without_tags_is_allowed(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={"title": "Untagged Book", "author": "A. Author", "year": 2001},
        )
        assert response.status_code == 201
        assert response.json()["tags"] is None

    def test_create_book_strips_whitespace(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={"title": "  Dune  ", "author": "  Frank Herbert  ", "year": 1965},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Dune"
        assert body["author"] == "Frank Herbert"

    def test_create_book_missing_required_fields_returns_422(self, client: TestClient) -> None:
        response = client.post("/books/", json={})
        assert response.status_code == 422
        fields = {error["loc"][-1] for error in response.json()["detail"]}
        assert {"title", "author", "year"} <= fields

    def test_create_book_blank_title_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={"title": "   ", "author": "Someone", "year": 2000},
        )
        assert response.status_code == 422

    def test_create_book_year_below_1400_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={"title": "Too Old", "author": "Anon", "year": 1399},
        )
        assert response.status_code == 422

    def test_create_book_year_in_the_future_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={
                "title": "From the Future",
                "author": "Anon",
                "year": datetime.now().year + 1,
            },
        )
        assert response.status_code == 422

    def test_create_book_non_integer_year_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={"title": "Bad Year", "author": "Anon", "year": "nineteen-eighty"},
        )
        assert response.status_code == 422

    def test_create_book_empty_tag_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={
                "title": "Tagged",
                "author": "Anon",
                "year": 2000,
                "tags": ["ok", "  "],
            },
        )
        assert response.status_code == 422

    def test_failed_create_does_not_change_catalog(self, client: TestClient) -> None:
        before = client.get("/stats").json()
        response = client.post("/books/", json={"title": "Nope"})
        assert response.status_code == 422
        after = client.get("/stats").json()
        assert after == before


class TestListBooks:
    def test_list_books_is_paginated(self, client: TestClient) -> None:
        response = client.get("/books/")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == SEED_COUNT
        assert body["offset"] == 0
        assert body["limit"] == 10
        assert len(body["books"]) == 10
        assert body["books"][0]["title"] == "Neuromancer"

    def test_list_books_second_page(self, client: TestClient) -> None:
        response = client.get("/books/", params={"offset": 10, "limit": 10})
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == SEED_COUNT
        assert len(body["books"]) == 2
        assert body["books"][0]["id"] == 11

    def test_list_books_offset_past_end_returns_empty_page(self, client: TestClient) -> None:
        response = client.get("/books/", params={"offset": 50, "limit": 10})
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == SEED_COUNT
        assert body["books"] == []

    def test_list_books_filters_by_author_case_insensitive(self, client: TestClient) -> None:
        response = client.get("/books/", params={"author": "william gibson"})
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["books"][0]["title"] == "Neuromancer"

    def test_list_books_author_filter_is_exact_not_substring(self, client: TestClient) -> None:
        response = client.get("/books/", params={"author": "William"})
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_list_books_filters_by_year(self, client: TestClient) -> None:
        response = client.get("/books/", params={"year": 2018})
        assert response.status_code == 200
        body = response.json()
        titles = {book["title"] for book in body["books"]}
        assert body["total"] == 2
        assert titles == {"The Calculating Stars", "Circe"}

    def test_list_books_searches_title_substring(self, client: TestClient) -> None:
        response = client.get("/books/", params={"title": "the", "limit": 100})
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1
        assert all("the" in book["title"].lower() for book in body["books"])

    def test_list_books_invalid_offset_returns_422(self, client: TestClient) -> None:
        response = client.get("/books/", params={"offset": -1})
        assert response.status_code == 422

    def test_list_books_limit_out_of_range_returns_422(self, client: TestClient) -> None:
        assert client.get("/books/", params={"limit": 0}).status_code == 422
        assert client.get("/books/", params={"limit": 101}).status_code == 422


class TestGetBook:
    def test_get_book_by_id_returns_seed_book(self, client: TestClient) -> None:
        response = client.get("/books/1")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["title"] == "Neuromancer"
        assert body["author"] == "William Gibson"
        assert body["year"] == 1984
        assert body["tags"] == ["cyberpunk", "science fiction"]

    def test_get_book_missing_id_returns_404(self, client: TestClient) -> None:
        response = client.get("/books/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"

    def test_get_book_non_integer_id_returns_422(self, client: TestClient) -> None:
        response = client.get("/books/stats")
        assert response.status_code == 422


class TestDeleteBook:
    def test_delete_book_returns_204_and_removes_it(self, client: TestClient) -> None:
        assert client.delete("/books/1").status_code == 204
        response = client.get("/books/1")
        assert response.status_code == 404

    def test_delete_missing_book_returns_404(self, client: TestClient) -> None:
        response = client.delete("/books/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"


class TestStats:
    def test_stats_for_seed_catalog(self, client: TestClient) -> None:
        response = client.get("/stats")
        assert response.status_code == 200
        assert response.json() == {
            "total_books": SEED_COUNT,
            "unique_authors": SEED_UNIQUE_AUTHORS,
        }

    def test_stats_update_after_create_and_delete(self, client: TestClient) -> None:
        created = client.post(
            "/books/",
            json={"title": "New", "author": "Brand New Author", "year": 2020},
        )
        assert created.status_code == 201
        after_create = client.get("/stats").json()
        assert after_create["total_books"] == SEED_COUNT + 1
        assert after_create["unique_authors"] == SEED_UNIQUE_AUTHORS + 1

        assert client.delete(f"/books/{created.json()['id']}").status_code == 204
        after_delete = client.get("/stats").json()
        assert after_delete == {
            "total_books": SEED_COUNT,
            "unique_authors": SEED_UNIQUE_AUTHORS,
        }
