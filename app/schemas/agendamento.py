"""Esquemas relativos a agendamentos de serviços."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import AgendamentoStatus


class AgendamentoCreate(BaseModel):
    """Payload enviado pelo cliente ao agendar um serviço."""

    prestador_id: UUID
    servico_id: UUID
    data_hora: datetime = Field(..., description="Data/hora pretendida no fuso do tenant")
    nome: str
    contacto: str
    observacoes: str | None = None


class AgendamentoOut(BaseModel):
    """Resposta padrão de agendamento."""

    id: UUID
    prestador_id: UUID
    servico_id: UUID
    data_hora: datetime
    status: AgendamentoStatus
    metadados_formulario: dict

    class Config:
        from_attributes = True
