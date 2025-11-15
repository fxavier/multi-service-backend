"""Endpoints públicos do catálogo de merchants e produtos."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import (
    TenantContext,
    get_current_active_tenant,
    get_current_user,
    get_db,
    get_tenant,
)
from app.infrastructure.db import models
from app.schemas import merchant as merchant_schemas
from app.schemas.merchant import (
    CategoriaCreate,
    CategoriaListResponse,
    CategoriaOut,
    CategoriaUpdate,
    ProdutoCreate,
    ProdutoListResponse,
    ProdutoOut,
    ProdutoUpdate,
)
from app.domain.enums import UserRole
from fastapi import status

router = APIRouter()


@router.get("/", response_model=merchant_schemas.MerchantListResponse)
def list_merchants(
    destaque: bool | None = None,
    tipo: str | None = None,
    search: str | None = Query(default=None, min_length=2),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
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

    total = query.count()
    offset = (page - 1) * page_size
    merchants = query.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total else 0

    return merchant_schemas.MerchantListResponse(
        items=merchants,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


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


@router.get("/{merchant_id}/produtos", response_model=ProdutoListResponse)
def list_produtos_privado(
    merchant_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    categoria_id: UUID | None = None,
    nome: str | None = Query(default=None, min_length=2),
    ativo: bool | None = None,
    disponivel: bool | None = None,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista privada de produtos para gestão do merchant."""

    _get_merchant_for_user(merchant_id=merchant_id, tenant=tenant, db=db, user=user)
    query = (
        db.query(models.Produto)
        .filter(
            models.Produto.tenant_id == tenant.id,
            models.Produto.merchant_id == merchant_id,
        )
        .order_by(models.Produto.nome)
    )
    if categoria_id:
        query = query.filter(models.Produto.categoria_id == categoria_id)
    if nome:
        ilike = f"%{nome.lower()}%"
        query = query.filter(models.Produto.nome.ilike(ilike))
    if ativo is not None:
        query = query.filter(models.Produto.ativo == ativo)
    if disponivel is not None:
        query = query.filter(models.Produto.disponivel == disponivel)

    total = query.count()
    offset = (page - 1) * page_size
    produtos = query.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return ProdutoListResponse(
        total=total,
        items=produtos,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# Categorias CRUD para merchants autenticados


def _get_merchant_for_user(
    *, merchant_id: UUID, tenant: TenantContext, db: Session, user: models.User
) -> models.Merchant:
    merchant = (
        db.query(models.Merchant)
        .filter(models.Merchant.tenant_id == tenant.id, models.Merchant.id == merchant_id)
        .first()
    )
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant não encontrado")
    if user.role == UserRole.MERCHANT and merchant.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para este merchant")
    return merchant


def _produto_base_query(db: Session, tenant_id: UUID, merchant_id: UUID):
    return db.query(models.Produto).filter(
        models.Produto.tenant_id == tenant_id,
        models.Produto.merchant_id == merchant_id,
    )


def _get_produto(
    *,
    db: Session,
    tenant: TenantContext,
    merchant_id: UUID,
    produto_id: UUID,
    user: models.User,
) -> models.Produto:
    _get_merchant_for_user(merchant_id=merchant_id, tenant=tenant, db=db, user=user)
    produto = _produto_base_query(db, tenant.id, merchant_id).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


@router.post(
    "/{merchant_id}/categorias",
    response_model=CategoriaOut,
    status_code=status.HTTP_201_CREATED,
)
def create_categoria(
    merchant_id: UUID,
    payload: CategoriaCreate,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant = _get_merchant_for_user(merchant_id=merchant_id, tenant=tenant, db=db, user=user)
    categoria = models.Categoria(
        tenant_id=tenant.id,
        merchant_id=merchant.id,
        nome=payload.nome,
        slug=payload.slug,
        descricao=payload.descricao,
        ordem=payload.ordem,
        ativa=payload.ativa,
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.post(
    "/{merchant_id}/produtos",
    response_model=ProdutoOut,
    status_code=status.HTTP_201_CREATED,
)
def create_produto(
    merchant_id: UUID,
    payload: ProdutoCreate,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_merchant_for_user(merchant_id=merchant_id, tenant=tenant, db=db, user=user)
    if payload.merchant_id != merchant_id:
        raise HTTPException(status_code=400, detail="merchant_id do payload não corresponde ao path")
    produto = models.Produto(
        tenant_id=tenant.id,
        merchant_id=merchant_id,
        nome=payload.nome,
        preco=payload.preco,
        categoria_id=payload.categoria_id,
        descricao_curta=payload.descricao_curta,
        descricao_detalhada=payload.descricao_detalhada,
        sku=payload.sku,
        stock_atual=payload.stock_atual,
        stock_minimo=payload.stock_minimo,
        imagens=payload.imagens or [],
        atributos_extras=payload.atributos_extras or {},
        permitir_backorder=payload.permitir_backorder,
        max_por_pedido=payload.max_por_pedido,
        disponivel=payload.disponivel,
        ativo=payload.ativo,
    )
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.get("/{merchant_id}/produtos", response_model=ProdutoListResponse)
def list_produtos_privado(
    merchant_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    categoria_id: UUID | None = None,
    nome: str | None = Query(default=None, min_length=2),
    ativo: bool | None = None,
    disponivel: bool | None = None,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_merchant_for_user(merchant_id=merchant_id, tenant=tenant, db=db, user=user)
    query = _produto_base_query(db, tenant.id, merchant_id).order_by(models.Produto.nome)
    if categoria_id:
        query = query.filter(models.Produto.categoria_id == categoria_id)
    if nome:
        ilike = f"%{nome.lower()}%"
        query = query.filter(models.Produto.nome.ilike(ilike))
    if ativo is not None:
        query = query.filter(models.Produto.ativo == ativo)
    if disponivel is not None:
        query = query.filter(models.Produto.disponivel == disponivel)

    total = query.count()
    offset = (page - 1) * page_size
    produtos = query.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return ProdutoListResponse(
        total=total,
        items=produtos,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{merchant_id}/produtos/{produto_id}", response_model=ProdutoOut)
def get_produto_privado(
    merchant_id: UUID,
    produto_id: UUID,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_produto(db=db, tenant=tenant, merchant_id=merchant_id, produto_id=produto_id, user=user)


@router.patch("/{merchant_id}/produtos/{produto_id}", response_model=ProdutoOut)
def update_produto(
    merchant_id: UUID,
    produto_id: UUID,
    payload: ProdutoUpdate,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    produto = _get_produto(db=db, tenant=tenant, merchant_id=merchant_id, produto_id=produto_id, user=user)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(produto, key, value)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.delete("/{merchant_id}/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_produto(
    merchant_id: UUID,
    produto_id: UUID,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    produto = _get_produto(db=db, tenant=tenant, merchant_id=merchant_id, produto_id=produto_id, user=user)
    produto.ativo = False
    db.add(produto)
    db.commit()
    return None


@router.get("/{merchant_id}/categorias", response_model=CategoriaListResponse)
def list_categorias_merchant(
    merchant_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ativa: bool | None = None,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_merchant_for_user(merchant_id=merchant_id, tenant=tenant, db=db, user=user)
    query = (
        db.query(models.Categoria)
        .filter(models.Categoria.tenant_id == tenant.id, models.Categoria.merchant_id == merchant_id)
        .order_by(models.Categoria.ordem, models.Categoria.nome)
    )
    if ativa is not None:
        query = query.filter(models.Categoria.ativa == ativa)
    total = query.count()
    offset = (page - 1) * page_size
    categorias = query.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    return CategoriaListResponse(
        total=total,
        items=categorias,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{merchant_id}/categorias/{categoria_id}", response_model=CategoriaOut)
def get_categoria(
    merchant_id: UUID,
    categoria_id: UUID,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_merchant_for_user(merchant_id=merchant_id, tenant=tenant, db=db, user=user)
    categoria = (
        db.query(models.Categoria)
        .filter(
            models.Categoria.tenant_id == tenant.id,
            models.Categoria.merchant_id == merchant_id,
            models.Categoria.id == categoria_id,
        )
        .first()
    )
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return categoria


@router.patch("/{merchant_id}/categorias/{categoria_id}", response_model=CategoriaOut)
def update_categoria(
    merchant_id: UUID,
    categoria_id: UUID,
    payload: CategoriaUpdate,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_merchant_for_user(merchant_id=merchant_id, tenant=tenant, db=db, user=user)
    categoria = (
        db.query(models.Categoria)
        .filter(
            models.Categoria.tenant_id == tenant.id,
            models.Categoria.merchant_id == merchant_id,
            models.Categoria.id == categoria_id,
        )
        .first()
    )
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(categoria, key, value)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{merchant_id}/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    merchant_id: UUID,
    categoria_id: UUID,
    tenant: TenantContext = Depends(get_current_active_tenant),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_merchant_for_user(merchant_id=merchant_id, tenant=tenant, db=db, user=user)
    categoria = (
        db.query(models.Categoria)
        .filter(
            models.Categoria.tenant_id == tenant.id,
            models.Categoria.merchant_id == merchant_id,
            models.Categoria.id == categoria_id,
        )
        .first()
    )
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    categoria.ativa = False
    db.add(categoria)
    db.commit()
    return None
