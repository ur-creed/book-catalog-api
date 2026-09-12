from fastapi import Request

from catalog.store import BookCatalog


def get_catalog(request: Request) -> BookCatalog:
    return request.app.state.catalog
