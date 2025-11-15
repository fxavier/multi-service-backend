"""Endpoints para gestão e listagem de prestadores/serviços."""

from __future__ import annotations

from decimal import Decimal
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.core.deps import (
    TenantContext,
    get_current_active_tenant,
    get_current_prestador,
    get_db,
    get_tenant,
)
from app.infrastructure.db import models
from app.schemas.merchant import (
    PrestadorListResponse,
    ServicoCreate,
    ServicoListResponse,
    ServicoOut,
    ServicoUpdate,
)

router = APIRouter()


def _paginate(query, page: int, page_size: int):
    total = query.count()
    total_pages = ceil(total / page_size) if page_size else 1
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    return total, total_pages, results


def _get_prestador_for_user(
    prestador_id: UUID,
    tenant: TenantContext,
    db: Session,
    current_prestador: models.PrestadorServico,
) -> models.PrestadorServico:
    prestador = (
        db.query(models.PrestadorServico)
        .filter(models.PrestadorServico.tenant_id == tenant.id, models.PrestadorServico.id == prestador_id)
        .first()
    )
    if not prestador:
        raise HTTPException(status_code=404, detail="Prestador não encontrado")
    if prestador.user_id != current_prestador.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para este prestador")
    return prestador


def _get_servico(
    db: Session,
    tenant: TenantContext,
    prestador_id: UUID,
    servico_id: UUID,
    current_prestador: models.PrestadorServico,
) -> models.Servico:
    _get_prestador_for_user(
        prestador_id=prestador_id,
        tenant=tenant,
        db=db,
        current_prestador=current_prestador,
    )
    servico = (
        db.query(models.Servico)
        .filter(
            models.Servico.tenant_id == tenant.id,
            models.Servico.prestador_id == prestador_id,
            models.Servico.id == servico_id,
        )
        .first()
    )
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return servico


@router.post("/prestadores/{prestador_id}/servicos", response_model=ServicoOut, status_code=status.HTTP_201_CREATED)
def create_servico(
    prestador_id: UUID,
    payload: ServicoCreate,
    tenant: TenantContext = Depends(get_current_active_tenant),
    current_prestador: models.PrestadorServico = Depends(get_current_prestador),
    db: Session = Depends(get_db),
):
    _get_prestador_for_user(
        prestador_id=prestador_id, tenant=tenant, db=db, current_prestador=current_prestador
    )
    if payload.prestador_id != prestador_id:
        raise HTTPException(status_code=400, detail="prestador_id do payload não corresponde ao path")
    servico = models.Servico(
        tenant_id=tenant.id,
        prestador_id=prestador_id,
        nome=payload.nome,
        preco=payload.preco,
        descricao_curta=payload.descricao_curta,
        descricao_detalhada=payload.descricao_detalhada,
        duracao_minutos=payload.duracao_minutos,
        categoria_id=payload.categoria_id,
        imagens=payload.imagens or [],
        tags=payload.tags or [],
        politica_cancelamento=payload.politica_cancelamento,
        tipo_atendimento=payload.tipo_atendimento,
        ativo=payload.ativo,
    )
    db.add(servico)
    db.commit()
    db.refresh(servico)
    return servico


@router.get("/prestadores/{prestador_id}/servicos", response_model=ServicoListResponse)
def list_servicos_privado(
    prestador_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    categoria_id: UUID | None = None,
    tipo_atendimento: str | None = None,
    ativo: bool | None = None,
    nome: str | None = Query(default=None, min_length=2),
    tenant: TenantContext = Depends(get_current_active_tenant),
    current_prestador: models.PrestadorServico = Depends(get_current_prestador),
    db: Session = Depends(get_db),
):
    _get_prestador_for_user(
        prestador_id=prestador_id, tenant=tenant, db=db, current_prestador=current_prestador
    )
    query = (
        db.query(models.Servico)
        .filter(models.Servico.tenant_id == tenant.id, models.Servico.prestador_id == prestador_id)
        .order_by(models.Servico.nome)
    )
    if categoria_id:
        query = query.filter(models.Servico.categoria_id == categoria_id)
    if tipo_atendimento:
        query = query.filter(models.Servico.tipo_atendimento == tipo_atendimento)
    if ativo is not None:
        query = query.filter(models.Servico.ativo == ativo)
    if nome:
        ilike = f"%{nome.lower()}%"
        query = query.filter(models.Servico.nome.ilike(ilike))

    total, total_pages, servicos = _paginate(query, page, page_size)
    return ServicoListResponse(
        total=total,
        items=servicos,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/prestadores/{prestador_id}/servicos/{servico_id}", response_model=ServicoOut)
def get_servico_privado(
    prestador_id: UUID,
    servico_id: UUID,
    tenant: TenantContext = Depends(get_current_active_tenant),
    current_prestador: models.PrestadorServico = Depends(get_current_prestador),
    db: Session = Depends(get_db),
):
    return _get_servico(
        db=db,
        tenant=tenant,
        prestador_id=prestador_id,
        servico_id=servico_id,
        current_prestador=current_prestador,
    )


@router.patch("/prestadores/{prestador_id}/servicos/{servico_id}", response_model=ServicoOut)
def update_servico(
    prestador_id: UUID,
    servico_id: UUID,
    payload: ServicoUpdate,
    tenant: TenantContext = Depends(get_current_active_tenant),
    current_prestador: models.PrestadorServico = Depends(get_current_prestador),
    db: Session = Depends(get_db),
):
    servico = _get_servico(
        db=db,
        tenant=tenant,
        prestador_id=prestador_id,
        servico_id=servico_id,
        current_prestador=current_prestador,
    )
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(servico, key, value)
    db.add(servico)
    db.commit()
    db.refresh(servico)
    return servico


@router.delete("/prestadores/{prestador_id}/servicos/{servico_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_servico(
    prestador_id: UUID,
    servico_id: UUID,
    tenant: TenantContext = Depends(get_current_active_tenant),
    current_prestador: models.PrestadorServico = Depends(get_current_prestador),
    db: Session = Depends(get_db),
):
    servico = _get_servico(
        db=db,
        tenant=tenant,
        prestador_id=prestador_id,
        servico_id=servico_id,
        current_prestador=current_prestador,
    )
    servico.ativo = False
    db.add(servico)
    db.commit()
    return None


@router.get("/public/prestadores", response_model=PrestadorListResponse)
def listar_prestadores_publicos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    categoria_id: UUID | None = None,
    tipo_atendimento: str | None = None,
    preco_min: Decimal | None = None,
    preco_max: Decimal | None = None,
    localizacao: str | None = Query(default=None, min_length=2),
    search: str | None = Query(default=None, min_length=2),
    tenant: TenantContext = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    query = db.query(models.PrestadorServico).filter(
        models.PrestadorServico.tenant_id == tenant.id,
        models.PrestadorServico.ativo.is_(True),
    )

    service_filters = any([categoria_id, tipo_atendimento, preco_min, preco_max])
    if service_filters:
        query = query.join(
            models.Servico,
            (models.Servico.prestador_id == models.PrestadorServico.id)
            & (models.Servico.ativo.is_(True)),
        )
        if categoria_id:
            query = query.filter(models.Servico.categoria_id == categoria_id)
        if tipo_atendimento:
            query = query.filter(models.Servico.tipo_atendimento == tipo_atendimento)
        if preco_min is not None:
            query = query.filter(models.Servico.preco >= preco_min)
        if preco_max is not None:
            query = query.filter(models.Servico.preco <= preco_max)
    if search:
        ilike = f"%{search.lower()}%"
        query = query.filter(models.PrestadorServico.nome.ilike(ilike))
    if localizacao:
        ilike = f"%{localizacao.lower()}%"
        query = query.filter(cast(models.PrestadorServico.zona_atendimento, String).ilike(ilike))

    query = query.distinct().order_by(models.PrestadorServico.nome)

    total, total_pages, prestadores = _paginate(query, page, page_size)
    return PrestadorListResponse(
        total=total,
        items=prestadores,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/public/prestadores/{prestador_id}/servicos", response_model=ServicoListResponse)
def listar_servicos_publicos_prestador(
    prestador_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    categoria_id: UUID | None = None,
    tipo_atendimento: str | None = None,
    search: str | None = Query(default=None, min_length=2),
    tenant: TenantContext = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    query = db.query(models.Servico).filter(
        models.Servico.tenant_id == tenant.id,
        models.Servico.prestador_id == prestador_id,
        models.Servico.ativo.is_(True),
    )
    if categoria_id:
        query = query.filter(models.Servico.categoria_id == categoria_id)
    if tipo_atendimento:
        query = query.filter(models.Servico.tipo_atendimento == tipo_atendimento)
    if search:
        ilike = f"%{search.lower()}%"
        query = query.filter(models.Servico.nome.ilike(ilike))
    query = query.order_by(models.Servico.nome)

    total, total_pages, servicos = _paginate(query, page, page_size)
    return ServicoListResponse(
        total=total,
        items=servicos,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
