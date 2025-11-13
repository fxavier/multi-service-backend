"""Testes do serviço de agendamentos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.infrastructure.db import models
from app.schemas.agendamento import AgendamentoCreate
from app.services.agendamento_service import criar_agendamento


def test_criar_agendamento(db_session):
    """Cria um agendamento válido no futuro."""

    cliente = db_session.query(models.Cliente).first()
    prestador = db_session.query(models.PrestadorServico).first()
    servico = db_session.query(models.Servico).first()

    payload = AgendamentoCreate(
        prestador_id=prestador.id,
        servico_id=servico.id,
        data_hora=datetime.now(timezone.utc) + timedelta(days=1),
        nome="Cliente",
        contacto="910000000",
    )

    agendamento = criar_agendamento(
        db=db_session,
        tenant_id=cliente.tenant_id,
        cliente=cliente,
        payload=payload,
    )

    assert agendamento.id is not None
    assert agendamento.prestador_id == prestador.id


def test_agendamento_nao_permite_passado(db_session):
    """Falha ao tentar criar agendamento no passado."""

    cliente = db_session.query(models.Cliente).first()
    prestador = db_session.query(models.PrestadorServico).first()
    servico = db_session.query(models.Servico).first()

    payload = AgendamentoCreate(
        prestador_id=prestador.id,
        servico_id=servico.id,
        data_hora=datetime.now(timezone.utc) - timedelta(hours=1),
        nome="Cliente",
        contacto="910000000",
    )

    with pytest.raises(HTTPException):
        criar_agendamento(db=db_session, tenant_id=cliente.tenant_id, cliente=cliente, payload=payload)
