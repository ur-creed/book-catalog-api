from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from api.routers.books import router as books_router
from book_handler import book_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    book_handler.load_books()
    yield

app = FastAPI(
    title="Book Catalog API",
    version="1.0.0",
    description=(
        "Minimal REST API for an in-memory book catalog. "
        "Use **/docs** for Swagger UI and **/redoc** for ReDoc."
    ),
    lifespan=lifespan,
)
app.include_router(books_router)


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web_server:app", host="127.0.0.1", port=8000, reload=True)
