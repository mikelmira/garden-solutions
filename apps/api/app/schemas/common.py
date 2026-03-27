"""
Common schemas for standardized API responses per docs.

Success (Single):
{
    "data": { "id": "...", ... },
    "meta": { ... }  // Optional
}

Success (List):
{
    "data": [ ... ],
    "pagination": {
        "total": 100,
        "page": 1,
        "size": 20
    }
}
"""
from typing import TypeVar, Generic, Any
from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    total: int
    page: int
    size: int


class DataResponse(BaseModel, Generic[T]):
    """Standard single-item response wrapper."""
    data: T
    meta: dict[str, Any] | None = None


class ListResponse(BaseModel, Generic[T]):
    """Standard list response wrapper with pagination."""
    data: list[T]
    pagination: PaginationMeta
