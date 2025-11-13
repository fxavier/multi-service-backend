# Arquitectura do Backend

## Visão Geral
- **FastAPI** com routers por bounded context (`app/api/v1/routes`).
- **Serviços** (`app/services`) encapsulam regras de negócio (checkout, agendamentos, dashboards futuros).
- **Infraestrutura** (`app/infrastructure`) contém modelos SQLAlchemy, migrations Alembic e repositório base.
- **Multi-tenancy** implementado via header `X-Tenant-ID` e mixin `TenantScopedMixin`.

## Fluxo de Request
1. **Dependency** `get_tenant` lê `X-Tenant-ID`, aceita slug ou UUID.
2. **Auth** (OAuth2 Bearer) injeta `User` via `get_current_user` e garante role certa (`require_role`).
3. **Routers** chamam serviços, evitando lógica complexa nos endpoints.
4. **Serviços** usam SQLAlchemy ORM com UUIDs, garantindo filtros por `tenant_id`.

## Estrutura de Dados (UUID everywhere)
- Todas as tabelas usam `UUID` como PK/FK (`app/infrastructure/db/models.py`).
- Tipo custom `GUID` permite testes SQLite sem perder compatibilidade com Postgres.
- Índices multi-coluna (`tenant_id`, `merchant_id`, etc.) suportam queries com filtros multi-tenant.

## Autenticação e Roles
- `User.role` controla acesso a routers específicos.
- `SUPERADMIN` pode gerir tenants (`/api/v1/tenants`).
- `CLIENTE`, `MERCHANT`, `PRESTADOR` têm dependências dedicadas (`get_current_cliente`, `get_current_merchant`, `get_current_prestador`).
- JWT inclui `tenant_id` para auditoria / futuras features.

## Swagger / Documentação Automática
- `FastAPI(docs_url="/docs", redoc_url="/redoc")` ativa Swagger UI e Redoc.
- Tags organizam endpoints (Auth, Tenants, Merchants, Checkout, Agendamentos, Dashboard).

## Testes
- `tests/conftest.py` cria base SQLite com dados mínimos (tenant, merchant, prestador, produto, serviço).
- `tests/test_checkout.py` valida criação de pedidos e isolamento multi-tenant.
- `tests/test_agendamentos.py` cobre regras de data e integridade.

## Próximos Passos
- Expandir routers de carrinho server-side e dashboards (CRUDs).
- Adicionar cobertura adicional de testes (auth, dashboards, carrinho).
- Automatizar pipelines CI (pytest + lint).
