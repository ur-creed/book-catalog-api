# Book Catalog API

A small REST API for an in-memory book catalog. FastAPI + Pydantic for the HTTP layer, a dict-backed handler for storage, pytest for tests.

I built this to practice a focused catalog API: typed routes, request validation, pagination/filtering, and a test suite you can run with one command. Swagger UI is at `/docs`.

## Stack

- **FastAPI** — typed routes, status codes, OpenAPI
- **Pydantic** — request/response models and field rules
- **Uvicorn** — run as `python web_server.py`
- **pytest** + FastAPI `TestClient` — HTTP tests and handler tests
- **In-memory `dict`** — no database; seed data loads from `data/books.json` at startup

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/books/` | Create a book (`title`, `author`, `year`, optional `tags`) |
| `GET` | `/books/` | Paginated list; optional `author`, `year`, `title` search |
| `GET` | `/books/{id}` | Fetch one book |
| `DELETE` | `/books/{id}` | Remove a book |
| `GET` | `/stats` | Total books and unique authors |

`GET /` redirects to `/docs`.

Created books exist only for the life of the process.

## Run

Python 3.12 recommended.

```
python -m venv .venv
```

Windows:

```
.venv\Scripts\activate
pip install -r requirements.txt
python web_server.py
```

macOS/Linux:

```
source .venv/bin/activate
pip install -r requirements.txt
python web_server.py
```

Open http://127.0.0.1:8000/

## Tests

```
pytest
pytest --cov=book_handler --cov=api --cov=web_server --cov-report=term-missing
```
