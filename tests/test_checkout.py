"""Testes unitários do serviço de checkout."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.infrastructure.db import models
from app.schemas.checkout import CheckoutItem
from app.services.checkout_service import create_pedido


def test_criar_pedido_sucesso(db_session):
    """Garante que o pedido é criado com total recalculado."""

    cliente = db_session.query(models.Cliente).first()
    produto = db_session.query(models.Produto).first()

    pedido = create_pedido(
        db=db_session,
        tenant_id=cliente.tenant_id,
        cliente=cliente,
        itens=[CheckoutItem(tipo="produto", ref_id=produto.id, quantidade=2)],
    )

    assert pedido.total == produto.preco * 2
    assert len(pedido.itens) == 1


def test_bloqueia_produto_de_outro_tenant(db_session):
    """Não permite adicionar produtos de tenant distinto."""

    cliente = db_session.query(models.Cliente).first()
    produto = db_session.query(models.Produto).first()

    outro_tenant = models.Tenant(nome="Outro", slug="outro", ativo=True)
    db_session.add(outro_tenant)
    db_session.flush()

    produto.tenant_id = outro_tenant.id
    db_session.commit()

    with pytest.raises(HTTPException):
        create_pedido(
            db=db_session,
            tenant_id=cliente.tenant_id,
            cliente=cliente,
            itens=[CheckoutItem(tipo="produto", ref_id=produto.id, quantidade=1)],
        )
