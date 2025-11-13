"""Endpoints para criação e gestão de agendamentos."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import TenantContext, get_current_active_tenant, get_current_cliente, get_db
from app.schemas.agendamento import AgendamentoCreate, AgendamentoOut
from app.services.agendamento_service import criar_agendamento

router = APIRouter()


@router.post("/", response_model=AgendamentoOut)
def criar(
    payload: AgendamentoCreate,
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_active_tenant),
    cliente=Depends(get_current_cliente),
):
    """Cria um agendamento garantindo a coerência multi-tenant."""

    agendamento = criar_agendamento(db=db, tenant_id=tenant.id, cliente=cliente, payload=payload)
    return agendamento
