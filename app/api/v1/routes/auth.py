"""Endpoints de autenticação e registo."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.domain.enums import UserRole
from app.infrastructure.db import models
from app.schemas import auth as auth_schemas

router = APIRouter()


@router.post("/register", response_model=auth_schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: auth_schemas.UserRegister, db: Session = Depends(get_db)):
    """Regista um novo cliente associado a um tenant existente."""

    tenant = db.query(models.Tenant).filter(models.Tenant.slug == payload.tenant_slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant inválido")

    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já utilizado")

    user = models.User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role=UserRole.CLIENTE,
        tenant_id=tenant.id,
    )
    cliente = models.Cliente(
        nome=payload.nome,
        email=payload.email,
        telefone=payload.telefone,
        tenant_id=tenant.id,
        user=user,
    )

    db.add_all([user, cliente])
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=auth_schemas.Token)
def login(payload: auth_schemas.UserLogin, db: Session = Depends(get_db)):
    """Autentica um utilizador via email/password devolvendo o JWT."""

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    token = create_access_token(str(user.id), tenant_id=str(user.tenant_id), role=user.role.value)
    return auth_schemas.Token(access_token=token)


@router.get("/me", response_model=auth_schemas.UserRead)
def read_me(user: models.User = Depends(get_current_user)):
    """Retorna os dados básicos do utilizador autenticado."""

    return user
