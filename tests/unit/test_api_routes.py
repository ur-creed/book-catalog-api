from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from catalog.schemas import CreateBookRequest

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
        assert client.get("/docs").status_code == 200

    def test_root_redirects_to_docs(self, client: TestClient) -> None:
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (302, 307)
        assert response.headers["location"] == "/docs"


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

    def test_create_accepts_classical_year(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={
                "title": "Discourses",
                "author": "Epictetus",
                "year": 108,
                "tags": ["stoicism"],
            },
        )
        assert response.status_code == 201
        assert response.json()["year"] == 108

    def test_create_accepts_bce_year(self, client: TestClient) -> None:
        response = client.post(
            "/books/",
            json={
                "title": "Republic",
                "author": "Plato",
                "year": -380,
                "tags": ["philosophy"],
            },
        )
        assert response.status_code == 201
        assert response.json()["year"] == -380

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"title": "   ", "author": "Someone", "year": 2000},
            {"title": "Too Old", "author": "Anon", "year": -3001},
            {
                "title": "From the Future",
                "author": "Anon",
                "year": datetime.now().year + 1,
            },
            {"title": "Bad Year", "author": "Anon", "year": "nineteen-eighty"},
            {"title": "Tagged", "author": "Anon", "year": 2000, "tags": ["ok", "  "]},
        ],
        ids=[
            "missing_fields",
            "blank_title",
            "year_before_3000_bce",
            "year_in_future",
            "year_not_int",
            "empty_tag",
        ],
    )
    def test_invalid_create_returns_422(self, client: TestClient, payload: dict) -> None:
        assert client.post("/books/", json=payload).status_code == 422

    def test_missing_required_fields_are_named(self, client: TestClient) -> None:
        response = client.post("/books/", json={})
        fields = {error["loc"][-1] for error in response.json()["detail"]}
        assert {"title", "author", "year"} <= fields

    def test_failed_create_does_not_change_catalog(self, client: TestClient) -> None:
        before = client.get("/stats").json()
        assert client.post("/books/", json={"title": "Nope"}).status_code == 422
        assert client.get("/stats").json() == before

    def test_create_schema_rejects_empty_body(self) -> None:
        with pytest.raises(Exception):
            CreateBookRequest.model_validate({})


class TestListBooks:
    def test_list_books_is_paginated(self, client: TestClient) -> None:
        response = client.get("/books/")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == SEED_COUNT
        assert body["offset"] == 0
        assert body["limit"] == 10
        assert len(body["books"]) == 10
        assert body["books"][0]["title"] == "Meditations"

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
        response = client.get("/books/", params={"author": "marcus aurelius"})
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["books"][0]["title"] == "Meditations"

    def test_list_books_author_filter_is_exact_not_substring(self, client: TestClient) -> None:
        response = client.get("/books/", params={"author": "Marcus"})
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_list_books_filters_by_year(self, client: TestClient) -> None:
        response = client.get("/books/", params={"year": 1969})
        assert response.status_code == 200
        body = response.json()
        titles = {book["title"] for book in body["books"]}
        assert body["total"] == 2
        assert titles == {"The Left Hand of Darkness", "Ubik"}

    def test_list_books_searches_title_substring(self, client: TestClient) -> None:
        response = client.get("/books/", params={"title": "the", "limit": 100})
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1
        assert all("the" in book["title"].lower() for book in body["books"])

    @pytest.mark.parametrize("params", [{"offset": -1}, {"limit": 0}, {"limit": 101}])
    def test_list_books_bad_pagination_returns_422(
        self, client: TestClient, params: dict
    ) -> None:
        assert client.get("/books/", params=params).status_code == 422


class TestGetBook:
    def test_get_book_by_id_returns_seed_book(self, client: TestClient) -> None:
        response = client.get("/books/1")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["title"] == "Meditations"
        assert body["author"] == "Marcus Aurelius"
        assert body["year"] == 180
        assert body["tags"] == ["stoicism", "philosophy"]

    def test_get_book_missing_id_returns_404(self, client: TestClient) -> None:
        response = client.get("/books/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"

    def test_get_book_non_integer_id_returns_422(self, client: TestClient) -> None:
        assert client.get("/books/stats").status_code == 422


class TestDeleteBook:
    def test_delete_book_returns_204_and_removes_it(self, client: TestClient) -> None:
        assert client.delete("/books/1").status_code == 204
        assert client.get("/books/1").status_code == 404

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
        assert client.get("/stats").json() == {
            "total_books": SEED_COUNT,
            "unique_authors": SEED_UNIQUE_AUTHORS,
        }
