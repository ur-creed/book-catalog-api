"""Standalone entrypoint. Prefer: uvicorn catalog.main:app --reload"""

from catalog.config import settings
from catalog.main import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "catalog.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
