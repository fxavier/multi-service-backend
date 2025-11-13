"""Tipos personalizados reutilizados pelos modelos ORM."""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """Tipo genérico que armazena UUID de forma compatível entre Postgres e SQLite."""

    impl = PG_UUID
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Seleciona o tipo correto por dialeto, usando CHAR(36) fora de Postgres."""

        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        """Converte o valor python para string se necessário antes de persistir."""

        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        """Volta a instanciar UUID ao ler de bases que guardam texto."""

        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))
