"""CRUD de roles configuráveis."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.domain.enums import UserRole
from app.infrastructure.db import models
from app.schemas.role import RoleCreate, RoleOut, RoleUpdate

router = APIRouter()

require_superadmin = Depends(require_role(UserRole.SUPERADMIN))


@router.get("/", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), _: models.User = require_superadmin):
    return db.query(models.Role).order_by(models.Role.name).all()


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    _: models.User = require_superadmin,
):
    existing = db.query(models.Role).filter(models.Role.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role já existe")
    role = models.Role(
        name=payload.name,
        description=payload.description,
        permissions=payload.permissions or {},
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.get("/{role_id}", response_model=RoleOut)
def get_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    _: models.User = require_superadmin,
):
    role = db.get(models.Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role não encontrado")
    return role


@router.patch("/{role_id}", response_model=RoleOut)
def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    _: models.User = require_superadmin,
):
    role = db.get(models.Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role não encontrado")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    _: models.User = require_superadmin,
):
    role = db.get(models.Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role não encontrado")
    db.delete(role)
    db.commit()
    return None
