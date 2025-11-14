"""Testes do módulo de autenticação."""

from __future__ import annotations

from app.infrastructure.db import models


def test_recusa_registo_para_tenant_inativo(client, db_session):
    """Garante que o endpoint /register devolve 403 quando o tenant está inativo."""

    tenant_inativo = models.Tenant(nome="Tenant Inativo", slug="tenant-inativo", ativo=False)
    db_session.add(tenant_inativo)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "novo.cliente@example.com",
            "password": "SenhaForte123",
            "nome": "Cliente Novo",
            "telefone": "910000001",
            "tenant_slug": tenant_inativo.slug,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant inativo: não é possível registar utilizadores"
