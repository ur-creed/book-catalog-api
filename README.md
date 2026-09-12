# Book Catalog API

A small FastAPI service for an in-memory book catalog. I use it as a clean example of how I structure Python APIs: HTTP at the edge, domain/store behind a protocol, Pydantic for contracts, pytest for behavior.

This is not a tutorial dump. Constraints are intentional — process-lifetime storage, no database — so the interesting parts are validation, pagination, and a seam you can swap without rewriting routes.

## What it shows

- **App factory** (`create_app`) so tests inject a store instead of patching globals
- **`Depends()`** for the catalog; routers type against a `BookCatalog` protocol, not a dict
- **Pydantic v2** models for create/list/stats, including year bounds and non-empty tags
- **Settings** via `pydantic-settings` (`CATALOG_` env prefix)
- **OpenAPI / Swagger** at `/docs` from the same models
- **pytest** with `TestClient`, parametrized 422 cases, and isolated in-memory fixtures

Python 3.12+, `list[str] | None` throughout. In-memory on purpose: a SQL store would implement the same protocol.

## Layout

```
catalog/
  main.py           # FastAPI app factory
  config.py         # settings
  dependencies.py   # get_catalog
  models.py         # Book
  store.py          # protocol + InMemoryCatalog
  schemas.py        # request/response
  routers/books.py
data/books.json     # seed snapshot
tests/
web_server.py       # python web_server.py
```

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/books/` | Create (`title`, `author`, `year` 1400–now, optional `tags`) |
| `GET` | `/books/` | Paginated list; `author`, `year`, `title` substring |
| `GET` | `/books/{id}` | Fetch one |
| `DELETE` | `/books/{id}` | Remove |
| `GET` | `/stats` | Totals and unique authors |

`GET /` redirects to `/docs`. Writes live only until the process exits.

## Run

```
python -m venv .venv
```

Windows: `.venv\Scripts\activate`  
macOS/Linux: `source .venv/bin/activate`

```
pip install -e ".[dev]"
python web_server.py
```

Or `uvicorn catalog.main:app --reload`. Open http://127.0.0.1:8000/

`pip install -r requirements.txt` works if you do not want an editable install.

## Tests

```
pytest
pytest --cov=catalog --cov-report=term-missing
ruff check catalog tests
```
