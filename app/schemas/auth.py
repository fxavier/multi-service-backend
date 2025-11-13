"""Esquemas Pydantic relacionados com autenticação e utilizadores."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.domain.enums import UserRole


class Token(BaseModel):
    """Resposta padrão para emissão de tokens JWT."""

    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    """Payload de login com email/password."""

    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """Payload para registo de cliente associado a um tenant."""

    email: EmailStr
    password: str
    nome: str
    telefone: str
    tenant_slug: str


class UserRead(BaseModel):
    """Representação pública de um utilizador autenticado."""

    id: UUID
    email: EmailStr
    role: UserRole
    tenant_id: UUID | None

    class Config:
        from_attributes = True
