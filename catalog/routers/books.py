from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from catalog.dependencies import get_catalog
from catalog.schemas import (
    BookListResponse,
    BookResponse,
    CreateBookRequest,
    ListBooksQuery,
    StatsResponse,
)
from catalog.store import BookCatalog

router = APIRouter()


@router.post(
    "/books/",
    status_code=status.HTTP_201_CREATED,
    response_model=BookResponse,
    tags=["books"],
    summary="Create a book",
    responses={422: {"description": "Missing or invalid title, author, or year"}},
)
def create_book(
    payload: CreateBookRequest,
    catalog: Annotated[BookCatalog, Depends(get_catalog)],
) -> BookResponse:
    book = catalog.create_book(
        title=payload.title,
        author=payload.author,
        year=payload.year,
        tags=payload.tags,
    )
    return BookResponse.model_validate(book)


@router.get(
    "/books/",
    response_model=BookListResponse,
    tags=["books"],
    summary="List books",
)
def list_books(
    query: Annotated[ListBooksQuery, Query()],
    catalog: Annotated[BookCatalog, Depends(get_catalog)],
) -> BookListResponse:
    result = catalog.list_books(
        author=query.author,
        year=query.year,
        title=query.title,
        offset=query.offset,
        limit=query.limit,
    )
    return BookListResponse.model_validate(result)


@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    tags=["books"],
    summary="Get a book by ID",
    responses={404: {"description": "Book not found"}},
)
def get_book(
    book_id: int,
    catalog: Annotated[BookCatalog, Depends(get_catalog)],
) -> BookResponse:
    book = catalog.get_book_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return BookResponse.model_validate(book)


@router.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["books"],
    summary="Delete a book by ID",
    responses={404: {"description": "Book not found"}},
)
def delete_book(
    book_id: int,
    catalog: Annotated[BookCatalog, Depends(get_catalog)],
) -> None:
    if not catalog.delete_book_by_id(book_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")


@router.get(
    "/stats",
    response_model=StatsResponse,
    tags=["stats"],
    summary="Catalog stats",
)
def get_stats(catalog: Annotated[BookCatalog, Depends(get_catalog)]) -> StatsResponse:
    return StatsResponse.model_validate(catalog.get_stats())
