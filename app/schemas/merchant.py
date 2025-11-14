"""Esquemas do catálogo de merchants e produtos."""

from __future__ import annotations

from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel


class MerchantOut(BaseModel):
    """Resposta resumida de merchant para o frontend."""

    id: UUID
    nome: str
    slug: str
    tipo: str
    avaliacao: Decimal | None
    destaque: bool

    class Config:
        from_attributes = True


class MerchantListResponse(BaseModel):
    """Envelope de paginação para resultados de merchants."""

    items: list[MerchantOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProdutoOut(BaseModel):
    """Resposta resumida de produto de um merchant."""

    id: UUID
    nome: str
    preco: Decimal
    disponivel: bool

    class Config:
        from_attributes = True
