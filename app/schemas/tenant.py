"""Esquemas para gestão de tenants (SUPERADMIN)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    """Campos partilhados entre create/update de tenant."""

    nome: str = Field(..., max_length=150)
    slug: str = Field(..., max_length=150)
    ativo: bool = True


class TenantCreate(TenantBase):
    """Payload de criação de tenant."""

    pass


class TenantUpdate(BaseModel):
    """Campos opcionais para atualização parcial de tenant."""

    nome: str | None = None
    ativo: bool | None = None


class TenantOut(TenantBase):
    """Resposta pública de tenant."""

    id: UUID

    class Config:
        from_attributes = True
