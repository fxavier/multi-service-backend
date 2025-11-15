"""Endpoints de catálogo genérico (categorias e produtos)."""

from __future__ import annotations

from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import TenantContext, get_db, get_tenant
from app.infrastructure.db import models
from app.schemas.merchant import (
    CategoriaListResponse,
    ProdutoListResponse,
)

router = APIRouter()


def _paginate(query, page: int, page_size: int):
    total = query.count()
    total_pages = ceil(total / page_size) if page_size else 1
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    return total, total_pages, results


@router.get("/categorias", response_model=CategoriaListResponse, tags=["Catálogo"])
def listar_categorias(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    merchant_id: UUID | None = None,
    tenant: TenantContext = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    query = db.query(models.Categoria).filter(models.Categoria.tenant_id == tenant.id)
    if merchant_id:
        query = query.filter(models.Categoria.merchant_id == merchant_id)

    total, total_pages, categorias = _paginate(query, page, page_size)
    return CategoriaListResponse(
        total=total,
        items=categorias,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/produtos", response_model=ProdutoListResponse, tags=["Catálogo"])
def listar_produtos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    merchant_id: UUID | None = None,
    categoria_id: UUID | None = None,
    disponivel: bool | None = None,
    ativo: bool | None = None,
    search: str | None = Query(default=None, min_length=2),
    tenant: TenantContext = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    query = db.query(models.Produto).filter(models.Produto.tenant_id == tenant.id)

    if merchant_id:
        query = query.filter(models.Produto.merchant_id == merchant_id)
    if categoria_id:
        query = query.filter(models.Produto.categoria_id == categoria_id)
    if disponivel is not None:
        query = query.filter(models.Produto.disponivel == disponivel)
    if ativo is not None:
        query = query.filter(models.Produto.ativo == ativo)
    if search:
        ilike = f"%{search.lower()}%"
        query = query.filter(models.Produto.nome.ilike(ilike))

    total, total_pages, produtos = _paginate(query, page, page_size)
    return ProdutoListResponse(
        total=total,
        items=produtos,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/public/merchants/{merchant_slug}/produtos",
    response_model=ProdutoListResponse,
    tags=["Catálogo"],
)
def listar_produtos_publicos_por_slug(
    merchant_slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    categoria_id: UUID | None = None,
    search: str | None = Query(default=None, min_length=2),
    tenant: TenantContext = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    merchant = (
        db.query(models.Merchant)
        .filter(models.Merchant.tenant_id == tenant.id, models.Merchant.slug == merchant_slug)
        .first()
    )
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant não encontrado")

    query = (
        db.query(models.Produto)
        .filter(
            models.Produto.tenant_id == tenant.id,
            models.Produto.merchant_id == merchant.id,
            models.Produto.ativo.is_(True),
            models.Produto.disponivel.is_(True),
        )
        .order_by(models.Produto.nome)
    )
    if categoria_id:
        query = query.filter(models.Produto.categoria_id == categoria_id)
    if search:
        ilike = f"%{search.lower()}%"
        query = query.filter(models.Produto.nome.ilike(ilike))

    total, total_pages, produtos = _paginate(query, page, page_size)
    return ProdutoListResponse(
        total=total,
        items=produtos,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
