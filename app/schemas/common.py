"""Esquemas utilitários partilhados entre módulos."""

from __future__ import annotations

from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class TenantAware(BaseModel):
    """Mixin de schemas que transportam o tenant associado."""

    tenant_id: UUID = Field(..., description="Identificador do tenant")


class Timestamped(BaseModel):
    """Campos standard de auditoria."""

    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginatedResponse(BaseModel):
    """Resposta genérica paginada."""

    total: int
    items: list
