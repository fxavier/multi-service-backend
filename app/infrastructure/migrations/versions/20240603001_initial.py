"""estrutura inicial multi-tenant com UUID."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.domain.enums import AgendamentoStatus, PedidoStatus, UserRole

# revision identifiers, used by Alembic.
revision: str = "20240603001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria todas as tabelas multi-tenant usando UUID como PK."""

    guid = postgresql.UUID(as_uuid=True)

    role_enum = postgresql.ENUM(
        *[role.value for role in UserRole], name="userrole", create_type=False
    )
    pedido_enum = postgresql.ENUM(
        *[status.value for status in PedidoStatus], name="pedidostatus", create_type=False
    )
    agendamento_enum = postgresql.ENUM(
        *[status.value for status in AgendamentoStatus], name="agendamentostatus", create_type=False
    )

    # limpa enums existentes caso o banco já tenha resíduos de execuções anteriores
    op.execute("DROP TYPE IF EXISTS userrole CASCADE")
    op.execute("DROP TYPE IF EXISTS pedidostatus CASCADE")
    op.execute("DROP TYPE IF EXISTS agendamentostatus CASCADE")

    role_enum.create(op.get_bind(), checkfirst=True)
    pedido_enum.create(op.get_bind(), checkfirst=True)
    agendamento_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tenants",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(150), nullable=False, unique=True),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "merchants",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(150), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("avaliacao", sa.Numeric(3, 2), server_default="0"),
        sa.Column("destaque", sa.Boolean, server_default=sa.false()),
        sa.Column("owner_id", guid, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_merchants_slug", "merchants", ["slug"])

    op.create_table(
        "prestadores",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("profissoes", sa.JSON, server_default=sa.text("'[]'::json")),
        sa.Column("preco_base", sa.Numeric(10, 2), nullable=False),
        sa.Column("user_id", guid, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "clientes",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("telefone", sa.String(50), nullable=False),
        sa.Column("user_id", guid, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "categorias",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("merchant_id", guid, sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_categoria_tenant_merchant", "categorias", ["tenant_id", "merchant_id"])

    op.create_table(
        "produtos",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("preco", sa.Numeric(10, 2), nullable=False),
        sa.Column("merchant_id", guid, sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("disponivel", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_produtos_tenant_merchant", "produtos", ["tenant_id", "merchant_id"])

    op.create_table(
        "servicos",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("preco", sa.Numeric(10, 2), nullable=False),
        sa.Column("prestador_id", guid, sa.ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cart_items",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("cliente_id", guid, sa.ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("ref_id", guid, nullable=False),
        sa.Column("quantidade", sa.Integer, server_default="1"),
        sa.Column("preco_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_cart_item_cliente", "cart_items", ["tenant_id", "cliente_id"])

    op.create_table(
        "pedidos",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("cliente_id", guid, sa.ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", pedido_enum, server_default=PedidoStatus.CRIADO.value),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_pedido_cliente", "pedidos", ["tenant_id", "cliente_id"])

    op.create_table(
        "itens_pedido",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("pedido_id", guid, sa.ForeignKey("pedidos.id", ondelete="CASCADE")),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("ref_id", guid, nullable=False),
        sa.Column("quantidade", sa.Integer, server_default="1"),
        sa.Column("preco_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "agendamentos",
        sa.Column("id", guid, primary_key=True, nullable=False),
        sa.Column("tenant_id", guid, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("cliente_id", guid, sa.ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prestador_id", guid, sa.ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("servico_id", guid, sa.ForeignKey("servicos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("data_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", agendamento_enum, server_default=AgendamentoStatus.PENDENTE.value),
        sa.Column("metadados_formulario", sa.JSON, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agendamento_cliente", "agendamentos", ["tenant_id", "cliente_id"])


def downgrade() -> None:
    """Remove as tabelas e enums criados nesta revisão."""

    op.drop_table("agendamentos")
    op.drop_table("itens_pedido")
    op.drop_table("pedidos")
    op.drop_table("cart_items")
    op.drop_table("servicos")
    op.drop_table("produtos")
    op.drop_table("categorias")
    op.drop_table("clientes")
    op.drop_table("prestadores")
    op.drop_table("merchants")
    op.drop_table("users")
    op.drop_table("tenants")

    sa.Enum(AgendamentoStatus, name="agendamentostatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(PedidoStatus, name="pedidostatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(UserRole, name="userrole").drop(op.get_bind(), checkfirst=True)
