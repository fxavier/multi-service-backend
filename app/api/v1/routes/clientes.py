"""Endpoints de perfil e endereços para clientes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_cliente, get_db
from app.infrastructure.db import models
from app.schemas.cliente import (
    ClienteEnderecoCreate,
    ClienteEnderecoOut,
    ClienteEnderecoUpdate,
    ClienteOut,
    ClienteUpdate,
)

router = APIRouter()


@router.get("/me/cliente", response_model=ClienteOut)
def get_me(cliente: models.Cliente = Depends(get_current_cliente)):
    return cliente


@router.put("/me/cliente", response_model=ClienteOut)
def update_me(
    payload: ClienteUpdate,
    cliente: models.Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cliente, key, value)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def _get_endereco(
    *, cliente: models.Cliente, endereco_id: UUID, db: Session
) -> models.ClienteEndereco:
    endereco = (
        db.query(models.ClienteEndereco)
        .filter(
            models.ClienteEndereco.id == endereco_id,
            models.ClienteEndereco.cliente_id == cliente.id,
            models.ClienteEndereco.tenant_id == cliente.tenant_id,
        )
        .first()
    )
    if not endereco:
        raise HTTPException(status_code=404, detail="Endereço não encontrado")
    return endereco


@router.get("/me/enderecos", response_model=list[ClienteEnderecoOut])
def list_enderecos(cliente: models.Cliente = Depends(get_current_cliente), db: Session = Depends(get_db)):
    enderecos = (
        db.query(models.ClienteEndereco)
        .filter(
            models.ClienteEndereco.cliente_id == cliente.id,
            models.ClienteEndereco.tenant_id == cliente.tenant_id,
        )
        .order_by(models.ClienteEndereco.created_at.desc())
        .all()
    )
    return enderecos


@router.post("/me/enderecos", response_model=ClienteEnderecoOut, status_code=status.HTTP_201_CREATED)
def create_endereco(
    payload: ClienteEnderecoCreate,
    cliente: models.Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    endereco = models.ClienteEndereco(
        tenant_id=cliente.tenant_id,
        cliente_id=cliente.id,
        apelido=payload.apelido,
        linha1=payload.linha1,
        linha2=payload.linha2,
        cidade=payload.cidade,
        codigo_postal=payload.codigo_postal,
        pais=payload.pais,
        telefone=payload.telefone,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(endereco)
    db.commit()
    db.refresh(endereco)
    if payload.definir_como_padrao:
        cliente.default_address_id = endereco.id
        db.add(cliente)
        db.commit()
    return endereco


@router.put("/me/enderecos/{endereco_id}", response_model=ClienteEnderecoOut)
def update_endereco(
    endereco_id: UUID,
    payload: ClienteEnderecoUpdate,
    cliente: models.Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    endereco = _get_endereco(cliente=cliente, endereco_id=endereco_id, db=db)
    update_data = payload.model_dump(exclude_unset=True)
    definir_padrao = update_data.pop("definir_como_padrao", None)
    for key, value in update_data.items():
        setattr(endereco, key, value)
    db.add(endereco)
    db.commit()
    if definir_padrao:
        cliente.default_address_id = endereco.id
        db.add(cliente)
        db.commit()
    db.refresh(endereco)
    return endereco


@router.delete("/me/enderecos/{endereco_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_endereco(
    endereco_id: UUID,
    cliente: models.Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db),
):
    endereco = _get_endereco(cliente=cliente, endereco_id=endereco_id, db=db)
    if cliente.default_address_id == endereco.id:
        cliente.default_address_id = None
        db.add(cliente)
    db.delete(endereco)
    db.commit()
    return None
