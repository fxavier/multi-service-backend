"""Serviços de aplicação para o fluxo de checkout."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.enums import PedidoStatus
from app.infrastructure.db import models
from app.schemas.checkout import CheckoutItem


def create_pedido(
    *, db: Session, tenant_id: UUID, cliente: models.Cliente, itens: list[CheckoutItem]
) -> models.Pedido:
    """Valida itens, recalcula preços e cria o pedido persistente."""

    if not itens:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Carrinho vazio")

    subtotal = Decimal("0.00")
    pedido_itens: list[models.ItemPedido] = []

    for payload_item in itens:
        if payload_item.tipo == "produto":
            produto = (
                db.query(models.Produto)
                .filter(
                    models.Produto.id == payload_item.ref_id,
                    models.Produto.tenant_id == tenant_id,
                    models.Produto.disponivel.is_(True),
                )
                .first()
            )
            if not produto:
                raise HTTPException(status_code=404, detail=f"Produto {payload_item.ref_id} indisponível")
            preco = Decimal(produto.preco)
        elif payload_item.tipo == "servico":
            servico = (
                db.query(models.Servico)
                .filter(models.Servico.id == payload_item.ref_id, models.Servico.tenant_id == tenant_id)
                .first()
            )
            if not servico:
                raise HTTPException(status_code=404, detail=f"Serviço {payload_item.ref_id} indisponível")
            preco = Decimal(servico.preco)
        else:
            raise HTTPException(status_code=400, detail="Tipo de item inválido")

        linha_total = preco * payload_item.quantidade
        subtotal += linha_total
        pedido_itens.append(
            models.ItemPedido(
                tenant_id=tenant_id,
                tipo=payload_item.tipo,
                ref_id=payload_item.ref_id,
                quantidade=payload_item.quantidade,
                preco_unitario=preco,
            )
        )

    pedido = models.Pedido(
        tenant_id=tenant_id,
        cliente_id=cliente.id,
        subtotal=subtotal,
        total=subtotal,
        status=PedidoStatus.CRIADO,
        itens=pedido_itens,
    )

    db.add(pedido)
    db.query(models.CartItem).filter(
        models.CartItem.cliente_id == cliente.id, models.CartItem.tenant_id == tenant_id
    ).delete(synchronize_session=False)

    db.commit()
    db.refresh(pedido)
    return pedido
