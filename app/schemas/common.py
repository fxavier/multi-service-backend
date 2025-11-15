"""Esquemas utilitários partilhados entre módulos."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class TenantAware(BaseModel):
    """Mixin de schemas que transportam o tenant associado."""

    tenant_id: UUID = Field(..., description="Identificador do tenant")


class Timestamped(BaseModel):
    """Campos standard de auditoria."""

    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginatedResponse(GenericModel, Generic[T]):
    """Resposta genérica paginada."""

    total: int
    items: list[T]
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None
