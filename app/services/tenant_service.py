"""Serviços auxiliares para gerir tenants."""

from __future__ import annotations

from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.db import models


def get_tenant_by_slug(db: Session, slug: str) -> models.Tenant | None:
    """Obtém um tenant a partir do slug único."""

    return db.query(models.Tenant).filter(models.Tenant.slug == slug).first()


def get_tenant_by_id(db: Session, tenant_id: UUID) -> models.Tenant | None:
    """Carrega um tenant pelo identificador UUID."""

    return db.get(models.Tenant, tenant_id)


def get_tenant_by_identifier(db: Session, identifier: str) -> models.Tenant | None:
    """Aceita slug ou UUID para resolver o tenant correspondente."""

    try:
        tenant_uuid = UUID(identifier)
    except ValueError:
        return get_tenant_by_slug(db, identifier)
    return get_tenant_by_id(db, tenant_uuid)


def list_tenants(db: Session) -> Iterable[models.Tenant]:
    """Lista todos os tenants ordenados pelo nome."""

    return db.query(models.Tenant).order_by(models.Tenant.nome.asc()).all()


def create_tenant(db: Session, *, nome: str, slug: str, ativo: bool) -> models.Tenant:
    """Cria e persiste um tenant."""

    tenant = models.Tenant(nome=nome, slug=slug, ativo=ativo)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def update_tenant(
    db: Session,
    tenant: models.Tenant,
    *,
    nome: str | None = None,
    ativo: bool | None = None,
) -> models.Tenant:
    """Atualiza campos mutáveis do tenant."""

    if nome is not None:
        tenant.nome = nome
    if ativo is not None:
        tenant.ativo = ativo

    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant
