import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.base_class import Base
from app.infrastructure.db import models
from app.domain.enums import UserRole


@pytest.fixture()
def db_session() -> Session:
    """Cria uma sessão SQLite em memória para testes unitários."""
    engine = create_engine("sqlite:///:memory:", future=True)
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

        merchant = models.Merchant(
            nome="Loja",
            slug="loja",
            tipo="produtos",
            avaliacao=4.5,
            destaque=True,
            tenant_id=tenant.id,
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
