from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from catalog.config import settings
from catalog.routers.books import router as books_router
from catalog.store import BookCatalog, InMemoryCatalog


def create_app(
    catalog: BookCatalog | None = None,
    *,
    load_seed: bool = True,
) -> FastAPI:
    """App factory so tests can inject a store without patching globals."""
    store = catalog or InMemoryCatalog(settings.seed_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if load_seed:
            store.load_seed()
        app.state.catalog = store
        yield

    app = FastAPI(
        title="Book Catalog API",
        version="1.0.0",
        description=(
            "In-memory book catalog: typed FastAPI routes, Pydantic validation, "
            "and a store protocol you can swap without touching HTTP. "
            "Interactive docs at **/docs**."
        ),
        lifespan=lifespan,
    )
    app.state.catalog = store
    app.include_router(books_router)

    @app.get("/", include_in_schema=False)
    def home() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    return app


app = create_app()
