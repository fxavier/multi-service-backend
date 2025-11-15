"""Serviços de aplicação para o fluxo de checkout."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.enums import PedidoOrigem, PedidoStatus
from app.infrastructure.db import models
from app.schemas.checkout import CheckoutItem


def _cart_items_for_cliente(
    *, db: Session, cliente: models.Cliente, tenant_id: UUID
) -> List[CheckoutItem]:
    itens = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.cliente_id == cliente.id,
            models.CartItem.tenant_id == tenant_id,
        )
        .all()
    )
    return [
        CheckoutItem(tipo=item.tipo, ref_id=item.ref_id, quantidade=item.quantidade)
        for item in itens
    ]


def _endereco_snapshot(
    *, db: Session, cliente: models.Cliente, endereco_id: UUID | None
) -> dict:
    endereco = None
    if endereco_id:
        endereco = (
            db.query(models.ClienteEndereco)
            .filter(
                models.ClienteEndereco.id == endereco_id,
                models.ClienteEndereco.cliente_id == cliente.id,
                models.ClienteEndereco.tenant_id == cliente.tenant_id,
            )
            .first()
        )
        if not endereco:
            raise HTTPException(status_code=404, detail="Endereço não encontrado")
    elif cliente.default_address_id:
        endereco = (
            db.query(models.ClienteEndereco)
            .filter(
                models.ClienteEndereco.id == cliente.default_address_id,
                models.ClienteEndereco.cliente_id == cliente.id,
            )
            .first()
        )

    if not endereco:
        return {}
    return {
        "apelido": endereco.apelido,
        "linha1": endereco.linha1,
        "linha2": endereco.linha2,
        "cidade": endereco.cidade,
        "codigo_postal": endereco.codigo_postal,
        "pais": endereco.pais,
        "telefone": endereco.telefone,
        "latitude": float(endereco.latitude) if endereco.latitude is not None else None,
        "longitude": float(endereco.longitude) if endereco.longitude is not None else None,
    }


def create_pedido(
    *,
    db: Session,
    tenant_id: UUID,
    cliente: models.Cliente,
    itens_payload: Iterable[CheckoutItem] | None,
    origem: PedidoOrigem | str | None,
    metodo_pagamento: str | None,
    estado_pagamento: str | None,
    endereco_id: UUID | None,
) -> models.Pedido:
    """Valida itens/carrinho, recalcula preços e cria o pedido."""

    itens = (
        list(itens_payload)
        if itens_payload
        else _cart_items_for_cliente(db=db, cliente=cliente, tenant_id=tenant_id)
    )
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
                    models.Produto.ativo.is_(True),
                    models.Produto.disponivel.is_(True),
                )
                .first()
            )
            if not produto:
                raise HTTPException(status_code=404, detail="Produto indisponível")
            if produto.stock_atual < payload_item.quantidade:
                raise HTTPException(status_code=400, detail="Stock insuficiente para o produto")
            produto.stock_atual -= payload_item.quantidade
            preco = Decimal(produto.preco)
            merchant_id = produto.merchant_id
            prestador_id = None
            categoria_snapshot = produto.categoria_id
            nome_snapshot = produto.nome
        elif payload_item.tipo == "servico":
            servico = (
                db.query(models.Servico)
                .join(models.PrestadorServico)
                .filter(
                    models.Servico.id == payload_item.ref_id,
                    models.Servico.tenant_id == tenant_id,
                    models.Servico.ativo.is_(True),
                    models.PrestadorServico.ativo.is_(True),
                )
                .first()
            )
            if not servico:
                raise HTTPException(status_code=404, detail="Serviço indisponível")
            preco = Decimal(servico.preco)
            merchant_id = None
            prestador_id = servico.prestador_id
            categoria_snapshot = servico.categoria_id
            nome_snapshot = servico.nome
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
                nome_snapshot=nome_snapshot,
                merchant_id=merchant_id,
                prestador_id=prestador_id,
                categoria_id_snapshot=categoria_snapshot,
                total_linha=linha_total,
            )
        )

    try:
        origem_enum = PedidoOrigem(origem) if origem else PedidoOrigem.WEB
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Origem inválida") from exc

    pedido = models.Pedido(
        tenant_id=tenant_id,
        cliente_id=cliente.id,
        subtotal=subtotal,
        total=subtotal,
        status=PedidoStatus.CRIADO,
        origem=origem_enum,
        metodo_pagamento=metodo_pagamento,
        estado_pagamento=estado_pagamento,
        endereco_entrega_snapshot=_endereco_snapshot(
            db=db, cliente=cliente, endereco_id=endereco_id
        ),
        cliente_nome_snapshot=cliente.nome,
        cliente_email_snapshot=cliente.email,
        cliente_telefone_snapshot=cliente.telefone,
        itens=pedido_itens,
    )

    db.add(pedido)
    db.query(models.CartItem).filter(
        models.CartItem.cliente_id == cliente.id, models.CartItem.tenant_id == tenant_id
    ).delete(synchronize_session=False)

    db.commit()
    db.refresh(pedido)
    return pedido
