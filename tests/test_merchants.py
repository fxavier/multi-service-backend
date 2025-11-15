"""Testes para endpoints relacionados a merchants."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.domain.enums import PedidoOrigem, PedidoStatus
from app.infrastructure.db import models


def test_list_merchants_retorna_metadata_de_paginacao(client, db_session):
    tenant = db_session.query(models.Tenant).first()
    assert tenant is not None

    # Cria merchants adicionais para testar paginação
    for indice in range(1, 26):
        merchant = models.Merchant(
            nome=f"Loja {indice}",
            slug=f"loja-{indice}",
            tipo="produtos",
            avaliacao=4.0,
            destaque=False,
            tenant_id=tenant.id,
        )
        db_session.add(merchant)
    db_session.commit()

    response = client.get(
        "/api/v1/merchants",
        params={"page": 2, "page_size": 10},
        headers={"X-Tenant-ID": str(tenant.id)},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["page"] == 2
    assert payload["page_size"] == 10
    assert payload["total"] == 26  # 1 merchant da fixture + 25 criados aqui
    assert payload["total_pages"] == 3
    assert len(payload["items"]) == 10
    assert all(item["slug"].startswith("loja-") for item in payload["items"])


def test_merchant_crud_categoria_produto_isolado_por_tenant(client, db_session, auth_headers):
    tenant = db_session.query(models.Tenant).first()
    merchant = db_session.query(models.Merchant).filter(models.Merchant.tenant_id == tenant.id).first()
    owner = db_session.query(models.User).filter(models.User.id == merchant.owner_id).first()
    headers = auth_headers(owner)

    categoria_payload = {
        "merchant_id": str(merchant.id),
        "nome": "Bebidas",
        "slug": "bebidas",
        "descricao": "Tudo para matar a sede",
        "ordem": 1,
        "ativa": True,
    }
    categoria_resp = client.post(
        f"/api/v1/merchants/{merchant.id}/categorias",
        json=categoria_payload,
        headers=headers,
    )
    assert categoria_resp.status_code == 201
    categoria_id = categoria_resp.json()["id"]

    produto_payload = {
        "merchant_id": str(merchant.id),
        "nome": "Água Premium",
        "preco": 3.5,
        "categoria_id": categoria_id,
        "descricao_curta": "500ml",
        "stock_atual": 10,
        "stock_minimo": 1,
        "permitir_backorder": False,
        "disponivel": True,
        "ativo": True,
    }
    produto_resp = client.post(
        f"/api/v1/merchants/{merchant.id}/produtos",
        json=produto_payload,
        headers=headers,
    )
    assert produto_resp.status_code == 201
    produto_json = produto_resp.json()
    assert produto_json["merchant_id"] == str(merchant.id)
    assert produto_json["categoria_id"] == categoria_id

    categorias_list = client.get(
        f"/api/v1/merchants/{merchant.id}/categorias",
        headers=headers,
    )
    assert categorias_list.status_code == 200
    assert categorias_list.json()["total"] == 1

    produtos_list = client.get(
        f"/api/v1/merchants/{merchant.id}/produtos",
        headers=headers,
    )
    assert produtos_list.status_code == 200
    nomes = [item["nome"] for item in produtos_list.json()["items"]]
    assert "Água Premium" in nomes

    outro_tenant = models.Tenant(nome="Tenant B", slug="tenant-b", ativo=True)
    db_session.add(outro_tenant)
    db_session.flush()
    merchant_outro = models.Merchant(
        nome="Loja B",
        slug="loja-b",
        tipo="produtos",
        avaliacao=4.0,
        destaque=False,
        tenant_id=outro_tenant.id,
    )
    db_session.add(merchant_outro)
    db_session.commit()

    denied = client.get(
        f"/api/v1/merchants/{merchant_outro.id}/produtos",
        headers=auth_headers(owner, tenant_override=str(outro_tenant.id)),
    )
    assert denied.status_code == 403


def test_merchant_visualiza_pedidos_relevantes(client, db_session, auth_headers):
    tenant = db_session.query(models.Tenant).first()
    merchant = db_session.query(models.Merchant).filter(models.Merchant.tenant_id == tenant.id).first()
    owner = db_session.query(models.User).filter(models.User.id == merchant.owner_id).first()
    cliente = db_session.query(models.Cliente).first()
    produto = db_session.query(models.Produto).first()

    pedido = models.Pedido(
        tenant_id=tenant.id,
        cliente_id=cliente.id,
        subtotal=produto.preco,
        total=produto.preco,
        status=PedidoStatus.PAGO,
        origem=PedidoOrigem.WEB,
        metodo_pagamento="CARTAO",
        estado_pagamento="PAGO",
        endereco_entrega_snapshot={"cidade": "Lisboa"},
        cliente_nome_snapshot=cliente.nome,
        cliente_email_snapshot=cliente.email,
        cliente_telefone_snapshot=cliente.telefone,
        data_confirmacao=datetime.now(timezone.utc),
    )
    pedido.itens = [
        models.ItemPedido(
            tenant_id=tenant.id,
            tipo="produto",
            ref_id=produto.id,
            quantidade=1,
            preco_unitario=produto.preco,
            nome_snapshot=produto.nome,
            merchant_id=merchant.id,
            total_linha=produto.preco,
        )
    ]
    db_session.add(pedido)
    db_session.commit()

    headers = auth_headers(owner)
    lista = client.get("/api/v1/merchants/me/pedidos", headers=headers)
    assert lista.status_code == 200
    pedidos = lista.json()
    assert len(pedidos) == 1
    assert pedidos[0]["cliente_nome_snapshot"] == cliente.nome
    assert pedidos[0]["itens"][0]["merchant_id"] == str(merchant.id)

    detalhe = client.get(f"/api/v1/merchants/me/pedidos/{pedido.id}", headers=headers)
    assert detalhe.status_code == 200
    detalhe_json = detalhe.json()
    assert float(detalhe_json["total"]) == pytest.approx(float(produto.preco))
    assert detalhe_json["endereco_entrega_snapshot"]["cidade"] == "Lisboa"
    assert detalhe_json["itens"][0]["nome_snapshot"] == produto.nome
