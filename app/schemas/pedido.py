"""Schemas para pedidos na visão de merchants."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums import PedidoStatus


class ItemPedidoResumo(BaseModel):
    id: UUID
    tipo: str
    ref_id: UUID
    nome_snapshot: str | None
    quantidade: int
    preco_unitario: Decimal
    total_linha: Decimal
    categoria_id_snapshot: UUID | None

    model_config = ConfigDict(from_attributes=True)


class PedidoResumo(BaseModel):
    id: UUID
    subtotal: Decimal
    total: Decimal
    status: PedidoStatus
    estado_pagamento: str | None
    origem: str
    created_at: datetime | None

    cliente_nome_snapshot: str | None
    cliente_email_snapshot: str | None
    cliente_telefone_snapshot: str | None

    itens: List[ItemPedidoResumo]

    model_config = ConfigDict(from_attributes=True)


class PedidoDetalhe(PedidoResumo):
    endereco_entrega_snapshot: dict | None = None


class PedidoStatusUpdate(BaseModel):
    status: PedidoStatus
