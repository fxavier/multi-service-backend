"""Serviços de aplicação para agendamentos."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.db import models
from app.schemas.agendamento import AgendamentoCreate


def criar_agendamento(
    *, db: Session, tenant_id: UUID, cliente: models.Cliente, payload: AgendamentoCreate
) -> models.Agendamento:
    """Valida requisitos do agendamento e persiste-o."""

    if payload.data_hora <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data/hora no passado")

    prestador = (
        db.query(models.PrestadorServico)
        .filter(models.PrestadorServico.id == payload.prestador_id, models.PrestadorServico.tenant_id == tenant_id)
        .first()
    )
    servico = (
        db.query(models.Servico)
        .filter(models.Servico.id == payload.servico_id, models.Servico.tenant_id == tenant_id)
        .first()
    )

    if not prestador or not servico or servico.prestador_id != prestador.id:
        raise HTTPException(status_code=400, detail="Prestador/serviço inválidos para o tenant")

    agendamento = models.Agendamento(
        tenant_id=tenant_id,
        cliente_id=cliente.id,
        prestador_id=prestador.id,
        servico_id=servico.id,
        data_hora=payload.data_hora,
        metadados_formulario={
            "nome": payload.nome,
            "contacto": payload.contacto,
            "observacoes": payload.observacoes,
        },
        preco_confirmado=float(servico.preco),
        canal=payload.canal,
        endereco_atendimento=payload.endereco_atendimento or {},
    )
    db.add(agendamento)
    db.commit()
    db.refresh(agendamento)
    return agendamento
