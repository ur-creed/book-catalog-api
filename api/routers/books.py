from datetime import datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator
from book_handler import book_handler

router = APIRouter()

class CreateBooksRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(
        default=...,
        min_length=1,
        max_length=300,
        description="Required. Book title; cannot be blank.",
        examples=["The Hobbit"],
    )
    author: str = Field(
        default=...,
        min_length=1,
        max_length=200,
        description="Required. Author name; cannot be blank.",
        examples=["J.R.R. Tolkien"],
    )
    year: int = Field(
        default=...,
        ge=1400,
        description="Required. Publication year from 1400 through the current year.",
        examples=[1937],
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional list of non-empty tags.",
        examples=[["fantasy", "adventure"]],
    )

    @field_validator("title", "author")
    @classmethod
    def required_text(cls, value: str, info: ValidationInfo) -> str:
        if not value:
            raise ValueError(f"{info.field_name} is required and cannot be empty")
        return value

    @field_validator("year")
    @classmethod
    def year_in_range(cls, year: int) -> int:
        current_year = datetime.now().year
        if year < 1400:
            raise ValueError("year must be at least 1400")
        if year > current_year:
            raise ValueError(f"year cannot be later than {current_year}")
        return year

    @field_validator("tags")
    @classmethod
    def tags_are_labels(cls, tags: Optional[List[str]]) -> Optional[List[str]]:
        if tags is None:
            return None
        cleaned: List[str] = []
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError("tags must be a list of non-empty strings")
            cleaned.append(tag.strip())
        return cleaned

class GetBooksRequest(BaseModel):
    author: Optional[str] = Field(default=None, description="Filter by author (case-insensitive exact match)")
    year: Optional[int] = Field(default=None, description="Filter by publication year")
    title: Optional[str] = Field(default=None, description="Case-insensitive substring search on title")
    offset: int = Field(default=0, ge=0, description="Number of books to skip")
    limit: int = Field(default=10, ge=1, le=100, description="Page size")

class BookResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int = Field(description="Unique integer ID")
    title: str
    author: str
    year: int
    tags: Optional[List[str]] = None

class BooksListResponse(BaseModel):
    books: List[BookResponse]
    total: int = Field(description="Total matches before pagination")
    offset: int
    limit: int

class StatsResponse(BaseModel):
    total_books: int = Field(description="Number of books in the catalog")
    unique_authors: int = Field(description="Number of distinct authors")

@router.post(
    "/books/",
    status_code=status.HTTP_201_CREATED,
    response_model=BookResponse,
    tags=["books"],
    summary="Create a book",
    responses={
        422: {
            "description": "Missing or invalid title, author, or year",
        }
    },
)
def create_book(payload: CreateBooksRequest) -> BookResponse:
    book = book_handler.create_book(
        title=payload.title,
        author=payload.author,
        year=payload.year,
        tags=payload.tags,
    )
    return book

@router.get(
    "/books/",
    response_model=BooksListResponse,
    tags=["books"],
    summary="List books",
)
def get_books(query: Annotated[GetBooksRequest, Query()]) -> BooksListResponse:
    result = book_handler.list_books(
        author=query.author,
        year=query.year,
        title=query.title,
        offset=query.offset,
        limit=query.limit,
    )
    return result

@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    tags=["books"],
    summary="Get a book by ID",
    responses={404: {"description": "Book not found"}},
)
def get_book(book_id: int) -> BookResponse:
    book = book_handler.get_book_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book

@router.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["books"],
    summary="Delete a book by ID",
    responses={404: {"description": "Book not found"}},
)
def delete_book(book_id: int) -> None:
    deleted = book_handler.delete_book_by_id(book_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

@router.get(
    "/stats",
    response_model=StatsResponse,
    tags=["stats"],
    summary="Catalog stats",
)
def get_stats() -> StatsResponse:
    return book_handler.get_stats()