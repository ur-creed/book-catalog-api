import pytest
from fastapi.testclient import TestClient
from book_handler import Book_Handler

@pytest.fixture
def catalog() -> Book_Handler:
    handler = Book_Handler()
    assert handler.load_books() is True
    return handler

@pytest.fixture
def empty_catalog() -> Book_Handler:
    return Book_Handler()

@pytest.fixture
def client(catalog: Book_Handler, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr("api.routers.books.book_handler", catalog)
    monkeypatch.setattr("web_server.book_handler", catalog)
    from web_server import app

    with TestClient(app) as test_client:
        yield test_client
