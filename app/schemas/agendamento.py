"""Esquemas relativos a agendamentos de serviços."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import AgendamentoStatus, PedidoOrigem


class AgendamentoCreate(BaseModel):
    """Payload enviado pelo cliente ao agendar um serviço."""

    prestador_id: UUID
    servico_id: UUID
    data_hora: datetime = Field(..., description="Data/hora pretendida no fuso do tenant")
    nome: str
    contacto: str
    observacoes: str | None = None
    canal: PedidoOrigem | None = PedidoOrigem.WEB
    endereco_atendimento: dict | None = None


class AgendamentoOut(BaseModel):
    """Resposta padrão de agendamento."""

    id: UUID
    cliente_id: UUID
    prestador_id: UUID
    servico_id: UUID
    data_hora: datetime
    status: AgendamentoStatus
    metadados_formulario: dict
    preco_confirmado: float | None = None
    endereco_atendimento: dict | None = None
    canal: PedidoOrigem | None = None
    data_confirmacao: datetime | None = None
    data_cancelamento: datetime | None = None
    motivo_cancelamento: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AgendamentoStatusUpdate(BaseModel):
    status: AgendamentoStatus
    preco_confirmado: float | None = None
    endereco_atendimento: dict | None = None
    data_confirmacao: datetime | None = None
    data_cancelamento: datetime | None = None
    motivo_cancelamento: str | None = None


class AgendamentoCancelCliente(BaseModel):
    motivo_cancelamento: str | None = None
