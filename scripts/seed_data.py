"""Seed inicial para popular a BD."""

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.domain.enums import UserRole
from app.infrastructure.db import models


def seed():
    """Executa seed mínima com utilizadores e dados demo."""
    db: Session = SessionLocal()
    try:
        if db.query(models.Tenant).count():
            print("⚠️  Já existem dados, seed ignorado.")
            return

        tenant = models.Tenant(nome="Fahamo Demo", slug="fahamo-demo", ativo=True)
        db.add(tenant)
        db.flush()

        superadmin = models.User(
            email="superadmin@fahamo.dev",
            password_hash=get_password_hash("admin123"),
            role=UserRole.SUPERADMIN,
            tenant_id=tenant.id,
            is_active=True,
        )
        db.add(superadmin)

        merchant_owner = models.User(
            email="merchant@fahamo.dev",
            password_hash=get_password_hash("merchant123"),
            role=UserRole.MERCHANT,
            tenant_id=tenant.id,
            is_active=True,
        )
        db.add(merchant_owner)
        db.flush()

        merchant = models.Merchant(
            nome="Loja Central",
            slug="loja-central",
            tipo="produtos",
            avaliacao=4.8,
            destaque=True,
            tenant_id=tenant.id,
            owner_id=merchant_owner.id,
        )
        db.add(merchant)
        db.flush()

        produto = models.Produto(
            nome="Bouquet Premium",
            preco=45.5,
            merchant_id=merchant.id,
            tenant_id=tenant.id,
            disponivel=True,
        )
        db.add(produto)

        prestador_user = models.User(
            email="prestador@fahamo.dev",
            password_hash=get_password_hash("prestador123"),
            role=UserRole.PRESTADOR,
            tenant_id=tenant.id,
            is_active=True,
        )
        db.add(prestador_user)
        db.flush()

        prestador = models.PrestadorServico(
            nome="Clínica Relax",
            profissoes=["massagista", "esteticista"],
            preco_base=60,
            tenant_id=tenant.id,
            user_id=prestador_user.id,
        )
        db.add(prestador)
        db.flush()

        servico = models.Servico(
            nome="Massagem Relax",
            preco=75,
            prestador_id=prestador.id,
            tenant_id=tenant.id,
        )
        db.add(servico)

        cliente_user = models.User(
            email="cliente@fahamo.dev",
            password_hash=get_password_hash("cliente123"),
            role=UserRole.CLIENTE,
            tenant_id=tenant.id,
            is_active=True,
        )
        db.add(cliente_user)
        db.flush()

        cliente = models.Cliente(
            nome="Cliente Demo",
            email="cliente@fahamo.dev",
            telefone="910000000",
            tenant_id=tenant.id,
            user_id=cliente_user.id,
        )
        db.add(cliente)
        db.commit()
        print("✅ Seed concluído")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
