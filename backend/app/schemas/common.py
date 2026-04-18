"""Shared response fragments reused across domains."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class OrmBase(BaseModel):
    """Base for schemas that read from SQLAlchemy rows."""

    model_config = ConfigDict(from_attributes=True)


class TimestampedOrm(OrmBase):
    created_at: datetime
    updated_at: datetime


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
