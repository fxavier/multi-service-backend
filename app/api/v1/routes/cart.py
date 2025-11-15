"""Endpoints para gestão do carrinho de clientes."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_tenant, get_current_cliente, get_db
from app.infrastructure.db import models
from app.schemas.cart import CartItemCreate, CartItemOut, CartItemUpdate

router = APIRouter()


def _get_reference_price(
    *, db: Session, tenant_id: UUID, tipo: str, ref_id: UUID
) -> Decimal:
    if tipo == "produto":
        produto = (
            db.query(models.Produto)
            .filter(
                models.Produto.id == ref_id,
                models.Produto.tenant_id == tenant_id,
                models.Produto.ativo.is_(True),
                models.Produto.disponivel.is_(True),
            )
            .first()
        )
        if not produto:
            raise HTTPException(status_code=404, detail="Produto indisponível")
        return Decimal(produto.preco)
    if tipo == "servico":
        servico = (
            db.query(models.Servico)
            .join(models.PrestadorServico, models.PrestadorServico.id == models.Servico.prestador_id)
            .filter(
                models.Servico.id == ref_id,
                models.Servico.tenant_id == tenant_id,
                models.Servico.ativo.is_(True),
                models.PrestadorServico.ativo.is_(True),
            )
            .first()
        )
        if not servico:
            raise HTTPException(status_code=404, detail="Serviço indisponível")
        return Decimal(servico.preco)
    raise HTTPException(status_code=400, detail="Tipo de item inválido")


def _get_cart_item(
    *, db: Session, cliente: models.Cliente, item_id: UUID
) -> models.CartItem:
    item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.id == item_id,
            models.CartItem.cliente_id == cliente.id,
            models.CartItem.tenant_id == cliente.tenant_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item


@router.get("/me/carrinho", response_model=list[CartItemOut])
def listar_carrinho(
    cliente: models.Cliente = Depends(get_current_cliente),
    tenant = Depends(get_current_active_tenant),
    db: Session = Depends(get_db),
):
    itens = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.cliente_id == cliente.id,
            models.CartItem.tenant_id == tenant.id,
        )
        .order_by(models.CartItem.created_at.asc())
        .all()
    )
    return itens


@router.post(
    "/me/carrinho/itens",
    response_model=CartItemOut,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_item(
    payload: CartItemCreate,
    cliente: models.Cliente = Depends(get_current_cliente),
    tenant = Depends(get_current_active_tenant),
    db: Session = Depends(get_db),
):
    preco = _get_reference_price(
        db=db, tenant_id=tenant.id, tipo=payload.tipo, ref_id=payload.ref_id
    )
    existente = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.cliente_id == cliente.id,
            models.CartItem.tenant_id == tenant.id,
            models.CartItem.tipo == payload.tipo,
            models.CartItem.ref_id == payload.ref_id,
        )
        .first()
    )
    if existente:
        existente.quantidade += payload.quantidade
        existente.preco_unitario = preco
        item = existente
    else:
        item = models.CartItem(
            tenant_id=tenant.id,
            cliente_id=cliente.id,
            tipo=payload.tipo,
            ref_id=payload.ref_id,
            quantidade=payload.quantidade,
            preco_unitario=preco,
        )
        db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/me/carrinho/itens/{item_id}", response_model=CartItemOut)
def atualizar_item(
    item_id: UUID,
    payload: CartItemUpdate,
    cliente: models.Cliente = Depends(get_current_cliente),
    tenant = Depends(get_current_active_tenant),
    db: Session = Depends(get_db),
):
    item = _get_cart_item(db=db, cliente=cliente, item_id=item_id)
    item.quantidade = payload.quantidade
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/me/carrinho/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_item(
    item_id: UUID,
    cliente: models.Cliente = Depends(get_current_cliente),
    tenant = Depends(get_current_active_tenant),
    db: Session = Depends(get_db),
):
    item = _get_cart_item(db=db, cliente=cliente, item_id=item_id)
    db.delete(item)
    db.commit()
    return None
