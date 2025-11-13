"""Endpoints públicos do catálogo de merchants e produtos."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import TenantContext, get_db, get_tenant
from app.infrastructure.db import models
from app.schemas import merchant as merchant_schemas

router = APIRouter()


@router.get("/", response_model=list[merchant_schemas.MerchantOut])
def list_merchants(
    destaque: bool | None = None,
    tipo: str | None = None,
    search: str | None = Query(default=None, min_length=2),
    page: int = 1,
    page_size: int = 20,
    tenant: TenantContext = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    """Lista merchants do tenant ativo com filtros opcionais."""

    query = db.query(models.Merchant).filter(models.Merchant.tenant_id == tenant.id)

    if destaque is not None:
        query = query.filter(models.Merchant.destaque == destaque)
    if tipo:
        query = query.filter(models.Merchant.tipo == tipo)
    if search:
        ilike = f"%{search.lower()}%"
        query = query.filter(func.lower(models.Merchant.nome).like(ilike))

    offset = (page - 1) * page_size
    merchants = query.offset(offset).limit(page_size).all()
    return merchants


@router.get("/{merchant_identifier}", response_model=merchant_schemas.MerchantOut)
def get_merchant(
    merchant_identifier: str,
    tenant: TenantContext = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    """Obtém um merchant por UUID ou slug dentro do tenant atual."""

    query = db.query(models.Merchant).filter(models.Merchant.tenant_id == tenant.id)
    merchant = None
    try:
        merchant_uuid = UUID(merchant_identifier)
        merchant = query.filter(models.Merchant.id == merchant_uuid).first()
    except ValueError:
        merchant = query.filter(models.Merchant.slug == merchant_identifier).first()

    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant não encontrado")
    return merchant


@router.get("/{merchant_id}/produtos", response_model=list[merchant_schemas.ProdutoOut])
def list_produtos(
    merchant_id: UUID, tenant: TenantContext = Depends(get_tenant), db: Session = Depends(get_db)
):
    """Lista produtos de um merchant específico do tenant atual."""

    produtos = (
        db.query(models.Produto)
        .filter(models.Produto.tenant_id == tenant.id, models.Produto.merchant_id == merchant_id)
        .all()
    )
    return produtos
