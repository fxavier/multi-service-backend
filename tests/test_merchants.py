"""Testes para o endpoint público de merchants."""

from __future__ import annotations

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
