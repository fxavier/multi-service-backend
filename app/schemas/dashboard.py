"""Esquemas Pydantic para respostas do dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import UUID

from pydantic import BaseModel


class MerchantTopProduto(BaseModel):
    """Produto mais vendido por merchant."""

    produto_id: UUID
    nome: str
    total_vendido: int


class MerchantPedidoRecente(BaseModel):
    """Pedido recente retornado no dashboard."""

    pedido_id: UUID
    total: float
    data: datetime
    status: str


class MerchantSummary(BaseModel):
    """Resumo consolidado de métricas do merchant autenticado."""

    merchant_id: UUID
    total_pedidos: int
    faturacao_total: float
    total_pedidos_por_status: Dict[str, int]
    top_produtos: List[MerchantTopProduto]
    ultimos_pedidos: List[MerchantPedidoRecente]


__all__ = [
    "MerchantSummary",
    "MerchantTopProduto",
    "MerchantPedidoRecente",
]
