# Fahamo Multi Service Backend

Backend FastAPI multi-tenant que suporta o marketplace Next.js (produtos + serviços) com Postgres, SQLAlchemy 2 e JWT.

## Stack e Principais Dependências
- **Python 3.11+** com FastAPI, Pydantic v2, SQLAlchemy 2.x e Alembic.
- **PostgreSQL 16** para persistência (UUIDs como chaves primárias).
- **Passlib + PyJWT** para autenticação com tokens Bearer.
- **Poetry** para gestão de dependências e scripts (`pyproject.toml`).
- **Docker Compose** com serviços `db` e `api` para desenvolvimento rápido.

## Estrutura de Pastas
```
app/
  api/v1/routes       # Routers FastAPI separados por domínio (auth, tenants, catálogo, checkout, agendamentos, dashboard)
  core                # Config, sessão de BD, segurança e dependências multi-tenant
  domain              # Enums/domain primitives
  infrastructure      # Modelos SQLAlchemy, migrations e repositórios base
  schemas             # Modelos Pydantic (request/response)
  services            # Casos de uso (checkout, agendamentos, etc.)
```
Documentação adicional encontra-se em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Como arrancar localmente
```bash
poetry install                               # instala dependências
poetry run alembic upgrade head              # aplica migration inicial (UUIDs)
poetry run python scripts/seed_data.py       # cria tenant + utilizadores demo
poetry run uvicorn app.main:app --reload     # arranca API local em http://127.0.0.1:8000
```

### Via Docker Compose
```bash
docker-compose up --build                   # levanta Postgres + API em hot reload
```

Configure variáveis (.env) para `DATABASE_URL`, `JWT_SECRET_KEY`, etc., conforme `app/core/config.py`.

### Migrations via Docker (comandos tipo `sh -c`)
```bash
# aplica migrations
docker-compose run --rm api sh -c "alembic upgrade head"

# gera nova migration
docker-compose run --rm api sh -c "alembic revision --autogenerate -m 'descricao'"

# rollback um passo
docker-compose run --rm api sh -c "alembic downgrade -1"

### Seed inicial via Docker
```bash
docker-compose run --rm api sh -c "python scripts/seed_data.py"
```
```
(garante que a variável `PYTHONPATH=/app` está definida no serviço `api`, já configurada no `docker-compose.yml`.)

## Swagger / OpenAPI
- Swagger UI ativo em **`/docs`** (graças a `FastAPI(..., docs_url="/docs")`).
- Redoc em **`/redoc`**.
- OpenAPI JSON em **`/openapi.json`**.

Estas rotas expõem todos os endpoints versionados (`/api/v1/...`), já organizados por tags: Auth, Tenants, Merchants, Checkout, Agendamentos e Dashboard.

## Multi-Tenancy
- Estrutura row-based: todas as tabelas possuem `tenant_id` (`UUID`).
- Header `X-Tenant-ID` aceita **slug** ou **UUID**. A dependência `get_tenant` valida e injeta `TenantContext` em cada request.
- SUPERADMIN pode gerir tenants e aceder cross-tenant; restantes roles são confinados ao `tenant_id` correspondente.
- `app/infrastructure/db/types.py` define o tipo custom `GUID` compatível com Postgres e SQLite (tests).

## Autenticação e Perfis
- JWT emitido via `/api/v1/auth/login` (token Bearer); refresh opcional futuro.
- Roles (`UserRole`): `SUPERADMIN`, `CLIENTE`, `MERCHANT`, `PRESTADOR`.
- Cada role possui endpoints protegidos em routers específicos (ex.: `/api/v1/dashboard/merchant/me/resumo`).

## Scripts úteis
- `scripts/seed_data.py` – popula tenant demo, utilizadores por role, merchant, prestador, produtos/serviços.
- `pytest` – roda testes unitários (`tests/test_checkout.py`, `tests/test_agendamentos.py`) garantindo regras críticas.

## Contribuição
1. Criar branch feature.
2. Adicionar/ajustar testes (`pytest`).
3. Executar linters (sugestão: `ruff`).
4. Abrir PR descrevendo alterações e impacto multi-tenant.

## Endpoints Exemplificativos
Ver ficheiro [`docs/API_CALLS.md`](docs/API_CALLS.md) com `curl` para criar tenant, registar cliente, login, listar merchants, checkout, agendamento e dashboards.
# multi-service-backend
