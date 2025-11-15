"""Testes do serviço de agendamentos."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.domain.enums import AgendamentoStatus, PedidoOrigem
from app.infrastructure.db import models
from app.schemas.agendamento import AgendamentoCreate, AgendamentoStatusUpdate
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


def test_prestador_lista_e_atualiza_agendamentos(client, db_session, auth_headers):
    """Prestador consegue listar e atualizar o status dos seus agendamentos."""

    cliente = db_session.query(models.Cliente).first()
    prestador = db_session.query(models.PrestadorServico).first()
    prestador_user = db_session.query(models.User).filter(models.User.id == prestador.user_id).first()
    servico = db_session.query(models.Servico).first()

    payload = AgendamentoCreate(
        prestador_id=prestador.id,
        servico_id=servico.id,
        data_hora=datetime.now(timezone.utc) + timedelta(days=2),
        nome="Cliente",
        contacto="910000000",
        canal=PedidoOrigem.WEB,
    )
    agendamento = criar_agendamento(
        db=db_session,
        tenant_id=cliente.tenant_id,
        cliente=cliente,
        payload=payload,
    )

    headers = auth_headers(prestador_user)
    lista = client.get("/api/v1/prestadores/me/agendamentos", headers=headers)
    assert lista.status_code == 200
    assert any(item["id"] == str(agendamento.id) for item in lista.json())

    confirma = client.patch(
        f"/api/v1/prestadores/me/agendamentos/{agendamento.id}",
        json=AgendamentoStatusUpdate(status=AgendamentoStatus.CONFIRMADO).model_dump(),
        headers=headers,
    )
    assert confirma.status_code == 200
    assert confirma.json()["status"] == AgendamentoStatus.CONFIRMADO
    assert confirma.json()["data_confirmacao"] is not None

    cancela = client.patch(
        f"/api/v1/prestadores/me/agendamentos/{agendamento.id}",
        json=AgendamentoStatusUpdate(
            status=AgendamentoStatus.CANCELADO,
            motivo_cancelamento="Cliente indisponível",
        ).model_dump(),
        headers=headers,
    )
    assert cancela.status_code == 200
    body = cancela.json()
    assert body["status"] == AgendamentoStatus.CANCELADO
    assert body["motivo_cancelamento"] == "Cliente indisponível"
