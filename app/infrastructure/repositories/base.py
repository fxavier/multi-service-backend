"""Infraestrutura padrão de repositórios com escopo por tenant."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session


class BaseRepository:
    """Aplica automaticamente filtros por tenant_id para queries."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def scoped_query(self, model):
        """Constrói uma query filtrada pelo tenant corrente."""

        return self.db.query(model).filter(model.tenant_id == self.tenant_id)
