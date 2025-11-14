from __future__ import annotations

from app.services import tenant_service
from app.infrastructure.db import models


def test_get_tenant_by_identifier_accepts_slug(db_session):
    tenant = tenant_service.get_tenant_by_identifier(db_session, "tenant-teste")
    assert tenant is not None
    assert tenant.slug == "tenant-teste"


def test_get_tenant_by_identifier_accepts_uuid(db_session):
    existing = db_session.query(models.Tenant).first()
    tenant = tenant_service.get_tenant_by_identifier(db_session, str(existing.id))
    assert tenant is not None
    assert tenant.id == existing.id


def test_create_and_update_tenant(db_session):
    novo = tenant_service.create_tenant(
        db_session,
        nome="Tenant Novo",
        slug="tenant-novo",
        ativo=True,
    )
    assert tenant_service.get_tenant_by_slug(db_session, "tenant-novo").id == novo.id

    atualizado = tenant_service.update_tenant(db_session, novo, nome="Tenant Atualizado", ativo=False)
    assert atualizado.nome == "Tenant Atualizado"
    assert atualizado.ativo is False
