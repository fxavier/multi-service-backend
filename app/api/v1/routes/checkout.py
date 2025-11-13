"""Endpoints de checkout server-side."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import TenantContext, get_current_active_tenant, get_current_cliente, get_db
from app.schemas.checkout import CheckoutRequest, PedidoOut
from app.services.checkout_service import create_pedido

router = APIRouter()


@router.post("/", response_model=PedidoOut)
def checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_active_tenant),
    cliente=Depends(get_current_cliente),
):
    """Cria um pedido validando preços no servidor e limpa o carrinho."""

    pedido = create_pedido(db=db, tenant_id=tenant.id, cliente=cliente, itens=payload.itens)
    return pedido
