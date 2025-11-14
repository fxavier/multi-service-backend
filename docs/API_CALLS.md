# Exemplos de Chamadas HTTP

Os exemplos abaixo assumem que a API está disponível em `http://localhost:8000` e que o Swagger UI pode ser consultado em `http://localhost:8000/docs` para explorar schemas completos.

## Convenções Gerais

- Substitua `{{TOKEN}}`, `{{SUPERADMIN_TOKEN}}`, `{{MERCHANT_TOKEN}}` e `{{PRESTADOR_TOKEN}}` por JWTs válidos obtidos através do endpoint de login.
- O cabeçalho multi-tenant definido em `settings.tenant_header` é `X-Tenant-ID`. Aceita *slug* ou UUID do tenant ativo.
- Todos os exemplos usam `curl`; ajuste conforme necessário para outras ferramentas (HTTPie, Postman, etc.).

```bash
BASE_URL="http://localhost:8000/api/v1"
TENANT_SLUG="lisboa"
TENANT_ID="00000000-0000-0000-0000-000000000001" # opcional: pode ser o mesmo slug
```

---

## Tenants (SUPERADMIN)

```bash
# Criar tenant
curl -X POST "$BASE_URL/tenants" \
  -H "Authorization: Bearer {{SUPERADMIN_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Lisboa Hub","slug":"lisboa","ativo":true}'

# Listar tenants
curl "$BASE_URL/tenants" \
  -H "Authorization: Bearer {{SUPERADMIN_TOKEN}}"

# Obter tenant específico
curl "$BASE_URL/tenants/${TENANT_ID}" \
  -H "Authorization: Bearer {{SUPERADMIN_TOKEN}}"

# Atualização parcial (nome ou estado)
curl -X PATCH "$BASE_URL/tenants/${TENANT_ID}" \
  -H "Authorization: Bearer {{SUPERADMIN_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Lisboa Hub Central","ativo":false}'
```

Exemplo de resposta (`GET /tenants`):

```json
[
  {
    "id": "<UUID>",
    "nome": "Lisboa Hub",
    "slug": "lisboa",
    "ativo": true
  }
]
```

---

## Autenticação e Utilizadores

```bash
# Registar cliente associado a um tenant ativo
curl -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"cliente@acme.com","password":"Teste123","nome":"Cliente","telefone":"+351910000000","tenant_slug":"lisboa"}'

# Login (retorna JWT)
curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"cliente@acme.com","password":"Teste123"}'

# Perfil do utilizador autenticado
curl "$BASE_URL/auth/me" \
  -H "Authorization: Bearer {{TOKEN}}"
```

Resposta de `GET /auth/me` (exemplo):

```json
{
  "id": "<UUID>",
  "email": "cliente@acme.com",
  "role": "CLIENTE",
  "tenant_id": "<UUID_TENANT>"
}
```

---

## Catálogo de Merchants e Produtos

```bash
# Listar merchants com filtros opcionais
curl "$BASE_URL/merchants?destaque=true&tipo=produtos&search=loja&page=1&page_size=20" \
  -H "X-Tenant-ID: ${TENANT_SLUG}"

# Obter merchant por slug ou UUID
curl "$BASE_URL/merchants/loja-do-centro" \
  -H "X-Tenant-ID: ${TENANT_SLUG}"

# Listar produtos de um merchant específico
MERCHANT_ID="11111111-1111-1111-1111-111111111111"
curl "$BASE_URL/merchants/${MERCHANT_ID}/produtos" \
  -H "X-Tenant-ID: ${TENANT_SLUG}"
```

Resposta paginada de `GET /merchants`:

```json
{
  "items": [
    {
      "id": "<UUID_MERCHANT>",
      "nome": "Loja",
      "slug": "loja",
      "tipo": "produtos",
      "avaliacao": 4.5,
      "destaque": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

Exemplo de resposta de `GET /merchants/{merchant_id}/produtos`:

```json
[
  {
    "id": "<UUID_PRODUTO>",
    "nome": "Produto X",
    "preco": 25.5,
    "disponivel": true
  }
]
```

---

## Checkout (Cliente autenticado)

```bash
TOKEN_CLIENTE="{{TOKEN}}"

curl -X POST "$BASE_URL/checkout" \
  -H "Authorization: Bearer ${TOKEN_CLIENTE}" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"itens":[{"tipo":"produto","ref_id":"<UUID_DO_PRODUTO>","quantidade":2}]}'
```

Resposta (exemplo):

```json
{
  "id": "<UUID_PEDIDO>",
  "subtotal": 51.0,
  "total": 51.0,
  "status": "PENDENTE",
  "itens": [
    {
      "id": "<UUID_ITEM>",
      "tipo": "produto",
      "ref_id": "<UUID_DO_PRODUTO>",
      "quantidade": 2,
      "preco_unitario": 25.5
    }
  ]
}
```

---

## Agendamentos (Cliente autenticado)

```bash
curl -X POST "$BASE_URL/agendamentos" \
  -H "Authorization: Bearer ${TOKEN_CLIENTE}" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
        "prestador_id":"<UUID_PRESTADOR>",
        "servico_id":"<UUID_SERVICO>",
        "data_hora":"2024-07-01T10:00:00Z",
        "nome":"Cliente",
        "contacto":"+351910000000",
        "observacoes":"Trazer documentação"
      }'
```

Resposta (exemplo):

```json
{
  "id": "<UUID_AGENDAMENTO>",
  "prestador_id": "<UUID_PRESTADOR>",
  "servico_id": "<UUID_SERVICO>",
  "data_hora": "2024-07-01T10:00:00+00:00",
  "status": "PENDENTE",
  "metadados_formulario": {}
}
```

---

## Dashboards

```bash
# Resumo do merchant autenticado
curl "$BASE_URL/dashboard/merchant/me/resumo" \
  -H "Authorization: Bearer {{MERCHANT_TOKEN}}" \
  -H "X-Tenant-ID: ${TENANT_ID}"

# Resumo do prestador autenticado
curl "$BASE_URL/dashboard/prestador/me/resumo" \
  -H "Authorization: Bearer {{PRESTADOR_TOKEN}}" \
  -H "X-Tenant-ID: ${TENANT_ID}"
```

Resposta de `GET /dashboard/merchant/me/resumo` (exemplo):

```json
{
  "merchant_id": "<UUID_MERCHANT>",
  "total_pedidos": 12,
  "faturacao_total": 845.5,
  "total_pedidos_por_status": {
    "PAGO": 12,
    "CANCELADO": 1
  },
  "top_produtos": [
    {"produto_id": "<UUID_PRODUTO>", "nome": "Produto X", "total_vendido": 24}
  ],
  "ultimos_pedidos": [
    {
      "pedido_id": "<UUID_PEDIDO>",
      "total": 42.5,
      "data": "2024-07-01T10:00:00+00:00",
      "status": "PAGO"
    }
  ]
}
```

Resposta de `GET /dashboard/prestador/me/resumo` (exemplo):

```json
{
  "prestador_id": "<UUID_PRESTADOR>",
  "total_por_status": {
    "PENDENTE": 3,
    "CONFIRMADO": 5
  },
  "proximos_agendamentos": [
    {
      "agendamento_id": "<UUID_AGENDAMENTO>",
      "cliente_id": "<UUID_CLIENTE>",
      "servico_id": "<UUID_SERVICO>",
      "data_hora": "2024-07-05T09:30:00+00:00",
      "status": "CONFIRMADO"
    }
  ]
}
```

> Utilize o Swagger UI (`/docs`) para gerar exemplos adicionais e testar parâmetros dinamicamente.
