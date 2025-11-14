"""Endpoints de resumo operacional para merchants e prestadores."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import (
    TenantContext,
    get_current_active_tenant,
    get_current_merchant,
    get_current_prestador,
    get_db,
)
from app.infrastructure.db import models
from app.domain.enums import PedidoStatus
from app.schemas import dashboard as dashboard_schemas

router = APIRouter()


PAID_PEDIDO_STATUSES: tuple[PedidoStatus, ...] = (PedidoStatus.PAGO,)


def _merchant_pedidos_query(db: Session, tenant: TenantContext, merchant: models.Merchant):
    return (
        db.query(models.Pedido)
        .join(models.ItemPedido, models.ItemPedido.pedido_id == models.Pedido.id)
        .join(
            models.Produto,
            (models.ItemPedido.ref_id == models.Produto.id)
            & (models.ItemPedido.tipo == "produto"),
        )
        .filter(
            models.Pedido.tenant_id == tenant.id,
            models.Produto.merchant_id == merchant.id,
        )
    )


@router.get("/merchant/me/resumo", response_model=dashboard_schemas.MerchantSummary)
def merchant_summary(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_active_tenant),
    merchant: models.Merchant = Depends(get_current_merchant),
):
    """Calcula KPIs principais para o merchant autenticado."""

    status_counts_rows = (
        _merchant_pedidos_query(db, tenant, merchant)
        .with_entities(
            models.Pedido.status,
            func.count(func.distinct(models.Pedido.id)).label("total_por_status"),
        )
        .group_by(models.Pedido.status)
        .all()
    )
    total_por_status = {status.value: int(count) for status, count in status_counts_rows}

    total_pedidos = sum(
        total_por_status.get(status.value, 0) for status in PAID_PEDIDO_STATUSES
    )

    faturacao_total = (
        db.query(func.coalesce(func.sum(models.ItemPedido.preco_unitario * models.ItemPedido.quantidade), 0))
        .join(models.Pedido, models.ItemPedido.pedido_id == models.Pedido.id)
        .join(
            models.Produto,
            (models.ItemPedido.ref_id == models.Produto.id) & (models.ItemPedido.tipo == "produto"),
        )
        .filter(
            models.ItemPedido.tenant_id == tenant.id,
            models.Produto.merchant_id == merchant.id,
            models.Pedido.status.in_(PAID_PEDIDO_STATUSES),
        )
        .scalar()
        or 0
    )

    top_produtos_rows = (
        db.query(
            models.Produto.id.label("produto_id"),
            models.Produto.nome,
            func.sum(models.ItemPedido.quantidade).label("total_vendido"),
        )
        .join(
            models.ItemPedido,
            (models.ItemPedido.ref_id == models.Produto.id) & (models.ItemPedido.tipo == "produto"),
        )
        .join(models.Pedido, models.ItemPedido.pedido_id == models.Pedido.id)
        .filter(models.Produto.merchant_id == merchant.id, models.Produto.tenant_id == tenant.id)
        .filter(models.Pedido.status.in_(PAID_PEDIDO_STATUSES))
        .group_by(models.Produto.id, models.Produto.nome)
        .order_by(func.sum(models.ItemPedido.quantidade).desc())
        .limit(3)
        .all()
    )
    top_produtos = [
        {
            "produto_id": row.produto_id,
            "nome": row.nome,
            "total_vendido": int(row.total_vendido or 0),
        }
        for row in top_produtos_rows
    ]

    ultimos_pedidos_rows = (
        _merchant_pedidos_query(db, tenant, merchant)
        .order_by(models.Pedido.created_at.desc())
        .limit(5)
        .all()
    )
    ultimos_pedidos = [
        {
            "pedido_id": pedido.id,
            "total": float(pedido.total),
            "data": pedido.created_at,
            "status": pedido.status.value,
        }
        for pedido in ultimos_pedidos_rows
    ]

    return {
        "merchant_id": merchant.id,
        "total_pedidos": int(total_pedidos),
        "faturacao_total": float(faturacao_total),
        "total_pedidos_por_status": total_por_status,
        "top_produtos": top_produtos,
        "ultimos_pedidos": ultimos_pedidos,
    }


@router.get("/prestador/me/resumo")
def prestador_summary(
    db: Session = Depends(get_db),
    tenant: TenantContext = Depends(get_current_active_tenant),
    prestador: models.PrestadorServico = Depends(get_current_prestador),
):
    """Mostra estatísticas básicas para o prestador autenticado."""

    status_counts = (
        db.query(models.Agendamento.status, func.count(models.Agendamento.id))
        .filter(
            models.Agendamento.tenant_id == tenant.id,
            models.Agendamento.prestador_id == prestador.id,
        )
        .group_by(models.Agendamento.status)
        .all()
    )
    total_por_status = {status.value: count for status, count in status_counts}

    proximos = (
        db.query(models.Agendamento)
        .filter(
            models.Agendamento.tenant_id == tenant.id,
            models.Agendamento.prestador_id == prestador.id,
            models.Agendamento.data_hora >= datetime.now(timezone.utc),
        )
        .order_by(models.Agendamento.data_hora.asc())
        .limit(5)
        .all()
    )
    proximos_agendamentos = [
        {
            "agendamento_id": ag.id,
            "cliente_id": ag.cliente_id,
            "servico_id": ag.servico_id,
            "data_hora": ag.data_hora,
            "status": ag.status.value,
        }
        for ag in proximos
    ]

    return {
        "prestador_id": prestador.id,
        "total_por_status": total_por_status,
        "proximos_agendamentos": proximos_agendamentos,
    }
