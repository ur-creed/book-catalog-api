import pytest
from fastapi.testclient import TestClient

from catalog.config import settings
from catalog.main import create_app
from catalog.store import InMemoryCatalog


@pytest.fixture
def catalog() -> InMemoryCatalog:
    store = InMemoryCatalog(settings.seed_path)
    assert store.load_seed() is True
    return store


@pytest.fixture
def empty_catalog(tmp_path) -> InMemoryCatalog:
    missing = tmp_path / "empty.json"
    return InMemoryCatalog(missing)


@pytest.fixture
def client(catalog: InMemoryCatalog) -> TestClient:
    app = create_app(catalog, load_seed=False)
    with TestClient(app) as test_client:
        yield test_client
