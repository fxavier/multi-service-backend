"""Esquemas de entrada/saída do fluxo de checkout."""

from __future__ import annotations

from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import PedidoOrigem


class CheckoutItem(BaseModel):
    """Item enviado no payload de checkout."""

    tipo: str = Field(pattern="^(produto|servico)$")
    ref_id: UUID
    quantidade: int = Field(ge=1)


class CheckoutRequest(BaseModel):
    """Payload completo do checkout."""

    itens: List[CheckoutItem] | None = None
    origem: PedidoOrigem | None = None
    metodo_pagamento: str | None = None
    estado_pagamento: str | None = None
    endereco_id: UUID | None = None


class PedidoItemOut(BaseModel):
    """Item retornado após criação do pedido."""

    id: UUID
    tipo: str
    ref_id: UUID
    quantidade: int
    preco_unitario: Decimal

    class Config:
        from_attributes = True


class PedidoOut(BaseModel):
    """Estrutura de resposta do pedido criado."""

    id: UUID
    subtotal: Decimal
    total: Decimal
    status: str
    itens: List[PedidoItemOut]

    class Config:
        from_attributes = True
