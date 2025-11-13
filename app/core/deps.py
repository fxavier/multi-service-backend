"""Dependências partilhadas do FastAPI (DB, tenant e auth)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generator
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import database
from app.core.config import settings
from app.core.security import decode_token
from app.domain.enums import UserRole
from app.infrastructure.db import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@dataclass
class TenantContext:
    """Estrutura simples com o tenant ativo a ser usado pelo request."""

    id: UUID
    slug: str
    is_active: bool


def get_db() -> Generator[Session, None, None]:
    """Gera sessões de base de dados com cleanup automático."""

    yield from database.get_session()


def get_tenant(request: Request, db: Session = Depends(get_db)) -> TenantContext:
    """Resolve o tenant através do header X-Tenant-ID (UUID ou slug)."""

    tenant_header = settings.tenant_header
    tenant_identifier = request.headers.get(tenant_header)
    if not tenant_identifier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant não informado")

    tenant = None
    try:
        tenant_uuid = UUID(tenant_identifier)
        tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_uuid).first()
    except ValueError:
        tenant = db.query(models.Tenant).filter(models.Tenant.slug == tenant_identifier).first()

    if not tenant or not tenant.ativo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant inválido/inativo")

    return TenantContext(id=tenant.id, slug=tenant.slug, is_active=tenant.ativo)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """Obtém o utilizador autenticado a partir do JWT bearer."""

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from None

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from None

    user = db.get(models.User, user_uuid)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilizador não encontrado")
    return user


def get_current_active_tenant(
    tenant: TenantContext = Depends(get_tenant), user: models.User = Depends(get_current_user)
) -> TenantContext:
    """Garante que o utilizador está autorizado a agir sobre o tenant corrente."""

    if user.role != UserRole.SUPERADMIN and user.tenant_id != tenant.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inválido para este utilizador")
    return tenant


def require_role(required_role: UserRole):
    """Dependência factory para validar roles específicos."""

    def dependency(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissões insuficientes")
        return user

    return dependency


def get_current_cliente(
    user: models.User = Depends(require_role(UserRole.CLIENTE)), db: Session = Depends(get_db)
) -> models.Cliente:
    """Carrega o cliente associado ao utilizador autenticado."""

    cliente = db.query(models.Cliente).filter(models.Cliente.user_id == user.id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


def get_current_merchant(
    user: models.User = Depends(require_role(UserRole.MERCHANT)), db: Session = Depends(get_db)
) -> models.Merchant:
    """Carrega o merchant dono do utilizador autenticado."""

    merchant = db.query(models.Merchant).filter(models.Merchant.owner_id == user.id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant não encontrado para o utilizador")
    return merchant


def get_current_prestador(
    user: models.User = Depends(require_role(UserRole.PRESTADOR)), db: Session = Depends(get_db)
) -> models.PrestadorServico:
    """Carrega o prestador associado ao utilizador autenticado."""

    prestador = db.query(models.PrestadorServico).filter(models.PrestadorServico.user_id == user.id).first()
    if not prestador:
        raise HTTPException(status_code=404, detail="Prestador não encontrado para o utilizador")
    return prestador
