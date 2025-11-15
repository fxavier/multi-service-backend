"""Esquemas relacionados com o catálogo de marketplace (merchants, categorias, produtos, prestadores e serviços)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums import ServicoTipoAtendimento
from app.schemas.common import PaginatedResponse


# ------------------------------------------------------------------------------
# Merchants
# ------------------------------------------------------------------------------


class MerchantBase(BaseModel):
    nome: str
    slug: str
    tipo: str
    descricao: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    telefone: str | None = None
    email_contacto: EmailStr | None = None
    endereco_rua: str | None = None
    endereco_cidade: str | None = None
    endereco_codigo_postal: str | None = None
    endereco_pais: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    horario_funcionamento: dict[str, Any] | None = None
    pedido_minimo: Decimal | None = None
    tempo_medio_preparacao_min: int | None = None
    aceita_produtos: bool = True
    aceita_servicos: bool = True
    ativo: bool = True


class MerchantCreate(MerchantBase):
    destaque: bool = False


class MerchantUpdate(BaseModel):
    nome: str | None = None
    slug: str | None = None
    tipo: str | None = None
    descricao: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    telefone: str | None = None
    email_contacto: EmailStr | None = None
    endereco_rua: str | None = None
    endereco_cidade: str | None = None
    endereco_codigo_postal: str | None = None
    endereco_pais: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    horario_funcionamento: dict[str, Any] | None = None
    pedido_minimo: Decimal | None = None
    tempo_medio_preparacao_min: int | None = None
    aceita_produtos: bool | None = None
    aceita_servicos: bool | None = None
    ativo: bool | None = None
    destaque: bool | None = None


class MerchantOut(MerchantBase):
    id: UUID
    avaliacao: Decimal | None = None
    destaque: bool
    owner_id: UUID | None = None
    tenant_id: UUID

    model_config = ConfigDict(from_attributes=True)


class MerchantListResponse(PaginatedResponse[MerchantOut]):
    """Lista paginada de merchants."""

    pass


# ------------------------------------------------------------------------------
# Categorias
# ------------------------------------------------------------------------------


class CategoriaBase(BaseModel):
    nome: str
    slug: str | None = None
    descricao: str | None = None
    ordem: int = 0
    ativa: bool = True


class CategoriaCreate(CategoriaBase):
    merchant_id: UUID


class CategoriaUpdate(BaseModel):
    nome: str | None = None
    slug: str | None = None
    descricao: str | None = None
    ordem: int | None = None
    ativa: bool | None = None


class CategoriaOut(CategoriaBase):
    id: UUID
    merchant_id: UUID

    model_config = ConfigDict(from_attributes=True)


class CategoriaListResponse(PaginatedResponse[CategoriaOut]):
    """Lista paginada de categorias."""

    pass


# ------------------------------------------------------------------------------
# Produtos
# ------------------------------------------------------------------------------


class ProdutoBase(BaseModel):
    nome: str
    preco: Decimal
    merchant_id: UUID
    categoria_id: UUID | None = None
    descricao_curta: str | None = None
    descricao_detalhada: str | None = None
    sku: str | None = None
    stock_atual: int = 0
    stock_minimo: int = 0
    imagens: list[str] | None = None
    atributos_extras: dict[str, Any] | None = None
    permitir_backorder: bool = False
    max_por_pedido: int | None = None
    disponivel: bool = True
    ativo: bool = True


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    nome: str | None = None
    preco: Decimal | None = None
    categoria_id: UUID | None = None
    descricao_curta: str | None = None
    descricao_detalhada: str | None = None
    sku: str | None = None
    stock_atual: int | None = None
    stock_minimo: int | None = None
    imagens: list[str] | None = None
    atributos_extras: dict[str, Any] | None = None
    permitir_backorder: bool | None = None
    max_por_pedido: int | None = None
    disponivel: bool | None = None
    ativo: bool | None = None


class ProdutoOut(ProdutoBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class ProdutoListResponse(PaginatedResponse[ProdutoOut]):
    """Lista paginada de produtos."""

    pass


# ------------------------------------------------------------------------------
# Prestadores de Serviço
# ------------------------------------------------------------------------------


class PrestadorServicoBase(BaseModel):
    nome: str
    profissoes: list[str] = Field(default_factory=list)
    preco_base: Decimal
    bio: str | None = None
    foto_url: str | None = None
    zona_atendimento: dict[str, Any] | None = None
    atende_ao_domicilio: bool = False
    atende_online: bool = False
    linguas: list[str] = Field(default_factory=list)
    ativo: bool = True
    user_id: UUID | None = None


class PrestadorServicoCreate(PrestadorServicoBase):
    pass


class PrestadorServicoUpdate(BaseModel):
    nome: str | None = None
    profissoes: list[str] | None = None
    preco_base: Decimal | None = None
    bio: str | None = None
    foto_url: str | None = None
    zona_atendimento: dict[str, Any] | None = None
    atende_ao_domicilio: bool | None = None
    atende_online: bool | None = None
    linguas: list[str] | None = None
    ativo: bool | None = None
    user_id: UUID | None = None


class PrestadorServicoOut(PrestadorServicoBase):
    id: UUID
    avaliacao_media: Decimal | None = None
    total_avaliacoes: int = 0

    model_config = ConfigDict(from_attributes=True)


class PrestadorListResponse(PaginatedResponse[PrestadorServicoOut]):
    """Lista paginada de prestadores."""

    pass


# ------------------------------------------------------------------------------
# Serviços
# ------------------------------------------------------------------------------


class ServicoBase(BaseModel):
    nome: str
    preco: Decimal
    prestador_id: UUID
    descricao_curta: str | None = None
    descricao_detalhada: str | None = None
    duracao_minutos: int | None = None
    categoria_id: UUID | None = None
    imagens: list[str] | None = None
    tags: list[str] | None = None
    politica_cancelamento: str | None = None
    tipo_atendimento: ServicoTipoAtendimento = ServicoTipoAtendimento.PRESENCIAL
    ativo: bool = True


class ServicoCreate(ServicoBase):
    pass


class ServicoUpdate(BaseModel):
    nome: str | None = None
    preco: Decimal | None = None
    descricao_curta: str | None = None
    descricao_detalhada: str | None = None
    duracao_minutos: int | None = None
    categoria_id: UUID | None = None
    imagens: list[str] | None = None
    tags: list[str] | None = None
    politica_cancelamento: str | None = None
    tipo_atendimento: ServicoTipoAtendimento | None = None
    ativo: bool | None = None


class ServicoOut(ServicoBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class ServicoListResponse(PaginatedResponse[ServicoOut]):
    """Lista paginada de serviços."""

    pass
