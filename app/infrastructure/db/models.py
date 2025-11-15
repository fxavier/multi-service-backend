"""Modelos ORM alinhados com a estratégia multi-tenant."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    AgendamentoStatus,
    PedidoOrigem,
    PedidoStatus,
    ServicoTipoAtendimento,
    UserRole,
)
from app.infrastructure.db.base_class import Base
from app.infrastructure.db.types import GUID


class TimestampMixin:
    """Mixin padrão para colunas de auditoria."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Tenant(Base, TimestampMixin):
    """Representa um tenant (instância lógica do marketplace)."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    moeda_padrao: Mapped[str] = mapped_column(String(10), default="EUR")
    config_checkout: Mapped[dict] = mapped_column(JSON, default=dict)
    branding: Mapped[dict] = mapped_column(JSON, default=dict)

    merchants: Mapped[List["Merchant"]] = relationship(back_populates="tenant")
    prestadores: Mapped[List["PrestadorServico"]] = relationship(back_populates="tenant")


class TenantScopedMixin:
    """Mixin para entidades que pertencem a um tenant específico."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), index=True)


class Role(Base, TimestampMixin):
    """Representa um role configurável para autorização."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)


class User(Base, TimestampMixin, TenantScopedMixin):
    """Utilizador autenticado, associado a perfis funcionais."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant: Mapped[Tenant] = relationship()
    cliente: Mapped[Optional["Cliente"]] = relationship(back_populates="user", uselist=False)
    merchant: Mapped[Optional["Merchant"]] = relationship(back_populates="owner", uselist=False)
    prestador: Mapped[Optional["PrestadorServico"]] = relationship(back_populates="user", uselist=False)


class Merchant(Base, TimestampMixin, TenantScopedMixin):
    """Loja do marketplace, dona de produtos."""

    __tablename__ = "merchants"
    __table_args__ = (Index("ix_merchants_slug", "slug"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    avaliacao: Mapped[float] = mapped_column(Numeric(3, 2), default=0)
    destaque: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    banner_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email_contacto: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    endereco_rua: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    endereco_cidade: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    endereco_codigo_postal: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    endereco_pais: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    horario_funcionamento: Mapped[dict] = mapped_column(JSON, default=dict)
    pedido_minimo: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tempo_medio_preparacao_min: Mapped[int] = mapped_column(Integer, default=0)
    aceita_produtos: Mapped[bool] = mapped_column(Boolean, default=True)
    aceita_servicos: Mapped[bool] = mapped_column(Boolean, default=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant: Mapped[Tenant] = relationship(back_populates="merchants")
    categorias: Mapped[List["Categoria"]] = relationship(back_populates="merchant")
    produtos: Mapped[List["Produto"]] = relationship(back_populates="merchant")
    owner: Mapped[Optional[User]] = relationship(back_populates="merchant")


class Categoria(Base, TimestampMixin, TenantScopedMixin):
    """Categoria de produtos dentro de um merchant."""

    __tablename__ = "categorias"
    __table_args__ = (Index("ix_categoria_tenant_merchant", "tenant_id", "merchant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)

    merchant: Mapped[Merchant] = relationship(back_populates="categorias")
    produtos: Mapped[List["Produto"]] = relationship(back_populates="categoria")
    servicos: Mapped[List["Servico"]] = relationship(back_populates="categoria")


class Produto(Base, TimestampMixin, TenantScopedMixin):
    """Produto físico associado a um merchant."""

    __tablename__ = "produtos"
    __table_args__ = (Index("ix_produtos_tenant_merchant", "tenant_id", "merchant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    preco: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    disponivel: Mapped[bool] = mapped_column(Boolean, default=True)
    descricao_curta: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    descricao_detalhada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stock_atual: Mapped[int] = mapped_column(Integer, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=0)
    categoria_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True
    )
    imagens: Mapped[List[str]] = mapped_column(JSON, default=list)
    atributos_extras: Mapped[dict] = mapped_column(JSON, default=dict)
    permitir_backorder: Mapped[bool] = mapped_column(Boolean, default=False)
    max_por_pedido: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    merchant: Mapped[Merchant] = relationship(back_populates="produtos")
    categoria: Mapped[Optional["Categoria"]] = relationship(back_populates="produtos")


class PrestadorServico(Base, TimestampMixin, TenantScopedMixin):
    """Prestador de serviços (profissional) multi-tenant."""

    __tablename__ = "prestadores"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    profissoes: Mapped[List[str]] = mapped_column(JSON, default=list)
    preco_base: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    foto_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    avaliacao_media: Mapped[float] = mapped_column(Numeric(3, 2), default=0)
    total_avaliacoes: Mapped[int] = mapped_column(Integer, default=0)
    zona_atendimento: Mapped[dict] = mapped_column(JSON, default=dict)
    atende_ao_domicilio: Mapped[bool] = mapped_column(Boolean, default=False)
    atende_online: Mapped[bool] = mapped_column(Boolean, default=False)
    linguas: Mapped[List[str]] = mapped_column(JSON, default=list)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant: Mapped[Tenant] = relationship(back_populates="prestadores")
    servicos: Mapped[List["Servico"]] = relationship(back_populates="prestador")
    user: Mapped[Optional[User]] = relationship(back_populates="prestador")


class Servico(Base, TimestampMixin, TenantScopedMixin):
    """Serviço comercializado por um prestador."""

    __tablename__ = "servicos"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    preco: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    prestador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prestadores.id", ondelete="CASCADE"), nullable=False)
    descricao_curta: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    descricao_detalhada: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duracao_minutos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    categoria_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True
    )
    imagens: Mapped[List[str]] = mapped_column(JSON, default=list)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    politica_cancelamento: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo_atendimento: Mapped[ServicoTipoAtendimento] = mapped_column(
        Enum(ServicoTipoAtendimento), default=ServicoTipoAtendimento.PRESENCIAL
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    prestador: Mapped[PrestadorServico] = relationship(back_populates="servicos")
    categoria: Mapped[Optional["Categoria"]] = relationship(back_populates="servicos")


class Cliente(Base, TimestampMixin, TenantScopedMixin):
    """Cliente final que pode ter pedidos e agendamentos."""

    __tablename__ = "clientes"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    default_address_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("clientes_enderecos.id", ondelete="SET NULL"), nullable=True
    )
    metadata_extra: Mapped[dict] = mapped_column(JSON, default=dict)

    user: Mapped[User] = relationship(back_populates="cliente")
    pedidos: Mapped[List["Pedido"]] = relationship(back_populates="cliente")
    agendamentos: Mapped[List["Agendamento"]] = relationship(back_populates="cliente")
    enderecos: Mapped[List["ClienteEndereco"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )
    default_address: Mapped[Optional["ClienteEndereco"]] = relationship(
        "ClienteEndereco", foreign_keys=[default_address_id], post_update=True
    )


class ClienteEndereco(Base, TimestampMixin, TenantScopedMixin):
    """Endereços de cliente para entregas/atendimentos."""

    __tablename__ = "clientes_enderecos"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"))
    apelido: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    linha1: Mapped[str] = mapped_column(String(255))
    linha2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cidade: Mapped[str] = mapped_column(String(120))
    codigo_postal: Mapped[str] = mapped_column(String(60))
    pais: Mapped[str] = mapped_column(String(120))
    telefone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    cliente: Mapped[Cliente] = relationship(back_populates="enderecos")


class CartItem(Base, TimestampMixin, TenantScopedMixin):
    """Item de carrinho persistido do lado do servidor."""

    __tablename__ = "cart_items"
    __table_args__ = (Index("ix_cart_item_cliente", "tenant_id", "cliente_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    ref_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=1)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    cliente: Mapped[Cliente] = relationship(backref="cart_items")


class Pedido(Base, TimestampMixin, TenantScopedMixin):
    """Pedido de checkout composto por itens."""

    __tablename__ = "pedidos"
    __table_args__ = (Index("ix_pedido_cliente", "tenant_id", "cliente_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"))
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PedidoStatus] = mapped_column(Enum(PedidoStatus), default=PedidoStatus.CRIADO)
    codigo_externo: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    origem: Mapped[PedidoOrigem] = mapped_column(Enum(PedidoOrigem), default=PedidoOrigem.WEB)
    metodo_pagamento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    estado_pagamento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    endereco_entrega_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    cliente_nome_snapshot: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    cliente_email_snapshot: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cliente_telefone_snapshot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    data_confirmacao: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data_envio: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data_conclusao: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    cliente: Mapped[Cliente] = relationship(back_populates="pedidos")
    itens: Mapped[List["ItemPedido"]] = relationship(back_populates="pedido", cascade="all, delete-orphan")


class ItemPedido(Base, TimestampMixin, TenantScopedMixin):
    """Item pertencente a um pedido (produto ou serviço)."""

    __tablename__ = "itens_pedido"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    pedido_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pedidos.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    ref_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, default=1)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    nome_snapshot: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True
    )
    prestador_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("prestadores.id", ondelete="SET NULL"), nullable=True
    )
    categoria_id_snapshot: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    total_linha: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    pedido: Mapped[Pedido] = relationship(back_populates="itens")


class Agendamento(Base, TimestampMixin, TenantScopedMixin):
    """Agendamento de serviço entre cliente e prestador."""

    __tablename__ = "agendamentos"
    __table_args__ = (Index("ix_agendamento_cliente", "tenant_id", "cliente_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"))
    prestador_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prestadores.id", ondelete="CASCADE"))
    servico_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("servicos.id", ondelete="CASCADE"))
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AgendamentoStatus] = mapped_column(Enum(AgendamentoStatus), default=AgendamentoStatus.PENDENTE)
    metadados_formulario: Mapped[dict] = mapped_column(JSON, default=dict)
    preco_confirmado: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    endereco_atendimento: Mapped[dict] = mapped_column(JSON, default=dict)
    canal: Mapped[PedidoOrigem] = mapped_column(Enum(PedidoOrigem), default=PedidoOrigem.WEB)
    notas_internas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_confirmacao: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data_cancelamento: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo_cancelamento: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    cliente: Mapped[Cliente] = relationship(back_populates="agendamentos")
    prestador: Mapped[PrestadorServico] = relationship()
    servico: Mapped[Servico] = relationship()
