from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from app.core.security import create_access_token
from app.infrastructure.db.base_class import Base
from app.infrastructure.db import models
from app.domain.enums import UserRole
from app.core.deps import get_db
from app.main import app


@pytest.fixture()
def db_session() -> Session:
    """Cria uma sessão SQLite em memória para testes unitários."""
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        tenant = models.Tenant(nome="Tenant Teste", slug="tenant-teste", ativo=True)
        session.add(tenant)
        session.flush()

        user = models.User(
            email="cliente@example.com",
            password_hash="hash",
            role=UserRole.CLIENTE,
            tenant_id=tenant.id,
            is_active=True,
        )
        session.add(user)
        session.flush()

        cliente = models.Cliente(
            nome="Cliente",
            email="cliente@example.com",
            telefone="910000000",
            user_id=user.id,
            tenant_id=tenant.id,
        )
        session.add(cliente)
        session.flush()

        prestador_user = models.User(
            email="prestador@example.com",
            password_hash="hash",
            role=UserRole.PRESTADOR,
            tenant_id=tenant.id,
            is_active=True,
        )
        session.add(prestador_user)
        session.flush()

        prestador = models.PrestadorServico(
            nome="Prestador",
            profissoes=["massagista"],
            preco_base=50,
            tenant_id=tenant.id,
            user_id=prestador_user.id,
        )
        session.add(prestador)
        session.flush()

        servico = models.Servico(
            nome="Massagem",
            preco=80,
            prestador_id=prestador.id,
            tenant_id=tenant.id,
        )
        session.add(servico)
        session.flush()

        merchant_owner_user = models.User(
            email="merchant.owner@example.com",
            password_hash="hash",
            role=UserRole.MERCHANT,
            tenant_id=tenant.id,
            is_active=True,
        )
        session.add(merchant_owner_user)
        session.flush()

        merchant = models.Merchant(
            nome="Loja",
            slug="loja",
            tipo="produtos",
            avaliacao=4.5,
            destaque=True,
            tenant_id=tenant.id,
            owner_id=merchant_owner_user.id,
        )
        session.add(merchant)
        session.flush()

        produto = models.Produto(
            nome="Produto X",
            preco=25,
            merchant_id=merchant.id,
            tenant_id=tenant.id,
            disponivel=True,
        )
        session.add(produto)
        session.commit()

        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """Instancia um TestClient com a sessão de BD de testes."""

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def auth_headers():
    """Gera headers de autenticação + tenant para o utilizador indicado."""

    def _builder(user: models.User, *, tenant_override: str | None = None) -> dict[str, str]:
        token = create_access_token(str(user.id), tenant_id=str(user.tenant_id), role=user.role.value)
        tenant_header_value = tenant_override or str(user.tenant_id)
        return {
            "Authorization": f"Bearer {token}",
            settings.tenant_header: tenant_header_value,
        }

    return _builder
