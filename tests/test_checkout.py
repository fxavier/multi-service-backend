"""Testes unitários do serviço de checkout."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.domain.enums import PedidoOrigem
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
        itens_payload=[CheckoutItem(tipo="produto", ref_id=produto.id, quantidade=2)],
        origem=PedidoOrigem.WEB,
        metodo_pagamento=None,
        estado_pagamento=None,
        endereco_id=None,
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
            itens_payload=[CheckoutItem(tipo="produto", ref_id=produto.id, quantidade=1)],
            origem=PedidoOrigem.WEB,
            metodo_pagamento=None,
            estado_pagamento=None,
            endereco_id=None,
        )


def test_checkout_captura_snapshots_e_limpa_carrinho(db_session):
    """Fluxo completo com carrinho contendo produto e serviço, validando snapshots."""

    cliente = db_session.query(models.Cliente).first()
    produto = db_session.query(models.Produto).first()
    servico = db_session.query(models.Servico).first()
    tenant_id = cliente.tenant_id

    endereco = models.ClienteEndereco(
        tenant_id=tenant_id,
        cliente_id=cliente.id,
        apelido="Casa",
        linha1="Rua 123",
        linha2=None,
        cidade="Lisboa",
        codigo_postal="1000-000",
        pais="PT",
        telefone="+351910000000",
    )
    db_session.add(endereco)
    db_session.flush()
    cliente.default_address_id = endereco.id
    db_session.add(cliente)

    db_session.add_all(
        [
            models.CartItem(
                tenant_id=tenant_id,
                cliente_id=cliente.id,
                tipo="produto",
                ref_id=produto.id,
                quantidade=2,
            ),
            models.CartItem(
                tenant_id=tenant_id,
                cliente_id=cliente.id,
                tipo="servico",
                ref_id=servico.id,
                quantidade=1,
            ),
        ]
    )
    db_session.commit()

    pedido = create_pedido(
        db=db_session,
        tenant_id=tenant_id,
        cliente=cliente,
        itens_payload=None,
        origem=PedidoOrigem.MOBILE,
        metodo_pagamento="MBWAY",
        estado_pagamento="PAGO",
        endereco_id=None,
    )

    assert len(pedido.itens) == 2
    assert pedido.cliente_nome_snapshot == cliente.nome
    assert pedido.cliente_email_snapshot == cliente.email
    assert pedido.endereco_entrega_snapshot["cidade"] == "Lisboa"
    assert all(item.total_linha > 0 for item in pedido.itens)
    assert db_session.query(models.CartItem).count() == 0
