from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class CreateBookRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Required. Book title; cannot be blank.",
        examples=["Neuromancer"],
    )
    author: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Required. Author name; cannot be blank.",
        examples=["William Gibson"],
    )
    year: int = Field(
        ...,
        ge=1400,
        description="Required. Publication year from 1400 through the current year.",
        examples=[1984],
    )
    tags: list[str] | None = Field(
        default=None,
        description="Optional list of non-empty tags.",
        examples=[["cyberpunk", "science fiction"]],
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
    def tags_are_labels(cls, tags: list[str] | None) -> list[str] | None:
        if tags is None:
            return None
        cleaned: list[str] = []
        for tag in tags:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError("tags must be a list of non-empty strings")
            cleaned.append(tag.strip())
        return cleaned


class ListBooksQuery(BaseModel):
    author: str | None = Field(
        default=None,
        description="Filter by author (case-insensitive exact match)",
    )
    year: int | None = Field(default=None, description="Filter by publication year")
    title: str | None = Field(
        default=None,
        description="Case-insensitive substring search on title",
    )
    offset: int = Field(default=0, ge=0, description="Number of books to skip")
    limit: int = Field(default=10, ge=1, le=100, description="Page size")


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique integer ID")
    title: str
    author: str
    year: int
    tags: list[str] | None = None


class BookListResponse(BaseModel):
    books: list[BookResponse]
    total: int = Field(description="Total matches before pagination")
    offset: int
    limit: int


class StatsResponse(BaseModel):
    total_books: int = Field(description="Number of books in the catalog")
    unique_authors: int = Field(description="Number of distinct authors")
