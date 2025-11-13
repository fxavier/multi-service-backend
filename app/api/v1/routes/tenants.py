"""Routers de gestão de tenants reservados ao SUPERADMIN."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.domain.enums import UserRole
from app.infrastructure.db import models
from app.schemas.tenant import TenantCreate, TenantOut, TenantUpdate

router = APIRouter()


@router.post("/", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """Cria um novo tenant multi-tenant."""

    if db.query(models.Tenant).filter(models.Tenant.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail="Slug já existe")

    tenant = models.Tenant(nome=payload.nome, slug=payload.slug, ativo=payload.ativo)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/", response_model=list[TenantOut])
def list_tenants(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """Lista todos os tenants existentes."""

    return db.query(models.Tenant).all()


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """Obtém detalhes de um tenant específico."""

    tenant = db.get(models.Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role(UserRole.SUPERADMIN)),
):
    """Atualiza parcialmente um tenant (nome ou estado)."""

    tenant = db.get(models.Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")

    if payload.nome is not None:
        tenant.nome = payload.nome
    if payload.ativo is not None:
        tenant.ativo = payload.ativo

    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant
