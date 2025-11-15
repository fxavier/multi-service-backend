"""Schemas para operações de carrinho."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartItemBase(BaseModel):
    tipo: Literal["produto", "servico"]
    ref_id: UUID


class CartItemCreate(CartItemBase):
    quantidade: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantidade: int = Field(ge=1)


class CartItemOut(CartItemBase):
    id: UUID
    quantidade: int
    preco_unitario: Decimal

    model_config = ConfigDict(from_attributes=True)
