"""Testes para o resumo do dashboard do merchant."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.api.v1.routes.dashboard import merchant_summary
from app.core.deps import TenantContext
from app.domain.enums import PedidoStatus
from app.infrastructure.db import models


@pytest.fixture()
def merchant_context(db_session):
    tenant = db_session.query(models.Tenant).first()
    merchant = db_session.query(models.Merchant).first()
    assert tenant is not None
    assert merchant is not None
    return TenantContext(id=tenant.id, slug=tenant.slug, is_active=tenant.ativo), merchant


def _criar_pedido(
    db_session,
    *,
    tenant,
    cliente,
    produto,
    status: PedidoStatus,
    quantidade: int,
):
    unitario = Decimal(str(produto.preco))
    total = unitario * quantidade
    pedido = models.Pedido(
        cliente_id=cliente.id,
        tenant_id=tenant.id,
        subtotal=total,
        total=total,
        status=status,
    )
    db_session.add(pedido)
    db_session.flush()

    item = models.ItemPedido(
        pedido_id=pedido.id,
        tipo="produto",
        ref_id=produto.id,
        quantidade=quantidade,
        preco_unitario=unitario,
        tenant_id=tenant.id,
    )
    db_session.add(item)
    db_session.flush()
    return pedido


def test_merchant_summary_considera_apenas_pedidos_pagos(db_session, merchant_context):
    tenant_context, merchant = merchant_context
    tenant = db_session.query(models.Tenant).first()
    cliente = db_session.query(models.Cliente).first()
    produto = db_session.query(models.Produto).first()

    assert tenant is not None
    assert cliente is not None
    assert produto is not None

    _criar_pedido(
        db_session,
        tenant=tenant,
        cliente=cliente,
        produto=produto,
        status=PedidoStatus.PAGO,
        quantidade=2,
    )
    _criar_pedido(
        db_session,
        tenant=tenant,
        cliente=cliente,
        produto=produto,
        status=PedidoStatus.PAGO,
        quantidade=1,
    )
    _criar_pedido(
        db_session,
        tenant=tenant,
        cliente=cliente,
        produto=produto,
        status=PedidoStatus.CANCELADO,
        quantidade=5,
    )
    db_session.commit()

    resultado = merchant_summary(db=db_session, tenant=tenant_context, merchant=merchant)

    assert resultado["total_pedidos"] == 2
    assert resultado["faturacao_total"] == pytest.approx(75.0)
    assert resultado["total_pedidos_por_status"][PedidoStatus.PAGO.value] == 2
    assert resultado["total_pedidos_por_status"][PedidoStatus.CANCELADO.value] == 1
    assert resultado["top_produtos"][0]["total_vendido"] == 3
    statuses = {pedido["status"] for pedido in resultado["ultimos_pedidos"]}
    assert PedidoStatus.PAGO.value in statuses
    assert PedidoStatus.CANCELADO.value in statuses
