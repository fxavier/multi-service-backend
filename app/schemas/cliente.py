"""Schemas para gestão de clientes e endereços."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClienteOut(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    telefone: str
    metadata_extra: dict[str, Any]
    default_address_id: UUID | None
    tenant_id: UUID

    model_config = ConfigDict(from_attributes=True)


class ClienteUpdate(BaseModel):
    nome: str | None = None
    telefone: str | None = None
    metadata_extra: dict[str, Any] | None = None


class ClienteEnderecoBase(BaseModel):
    apelido: str | None = None
    linha1: str
    linha2: str | None = None
    cidade: str
    codigo_postal: str
    pais: str
    telefone: str | None = None
    latitude: float | None = Field(default=None, description="Latitude em graus decimais")
    longitude: float | None = Field(default=None, description="Longitude em graus decimais")


class ClienteEnderecoCreate(ClienteEnderecoBase):
    definir_como_padrao: bool = False


class ClienteEnderecoUpdate(BaseModel):
    apelido: str | None = None
    linha1: str | None = None
    linha2: str | None = None
    cidade: str | None = None
    codigo_postal: str | None = None
    pais: str | None = None
    telefone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    definir_como_padrao: bool | None = None
    ativo: bool | None = None


class ClienteEnderecoOut(ClienteEnderecoBase):
    id: UUID
    cliente_id: UUID
    ativo: bool

    model_config = ConfigDict(from_attributes=True)
