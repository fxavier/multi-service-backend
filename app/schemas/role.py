"""Schemas para gestão de roles dinâmicos."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoleBase(BaseModel):
    name: str
    description: str | None = None
    permissions: dict | None = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    description: str | None = None
    permissions: dict | None = None


class RoleOut(RoleBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
