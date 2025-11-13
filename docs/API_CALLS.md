# Exemplos de Chamadas HTTP

Substituir `{{TOKEN}}`, `{{TENANT_UUID}}` e `{{TENANT_SLUG}}` pelos valores reais.

```bash
# 1. Criar tenant (SUPERADMIN)
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Authorization: Bearer {{SUPERADMIN_TOKEN}}" \
  -H "Content-Type: application/json" \
  -d '{"nome":"Lisboa Hub","slug":"lisboa","ativo":true}'

# 2. Registar cliente
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"cliente@acme.com","password":"Teste123","nome":"Cliente","telefone":"+351910000000","tenant_slug":"lisboa"}'

# 3. Login (recebe JWT)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"cliente@acme.com","password":"Teste123"}'

# 4. Listar merchants do tenant (via slug ou UUID)
curl http://localhost:8000/api/v1/merchants?destaque=true \
  -H "X-Tenant-ID: lisboa"

# 5. Checkout
token=$(...) # token cliente
curl -X POST http://localhost:8000/api/v1/checkout \
  -H "Authorization: Bearer ${token}" \
  -H "X-Tenant-ID: {{TENANT_UUID}}" \
  -H "Content-Type: application/json" \
  -d '{"itens":[{"tipo":"produto","ref_id":"<UUID_DO_PRODUTO>","quantidade":2}]}'

# 6. Criar agendamento
curl -X POST http://localhost:8000/api/v1/agendamentos \
  -H "Authorization: Bearer ${token}" \
  -H "X-Tenant-ID: {{TENANT_UUID}}" \
  -H "Content-Type: application/json" \
  -d '{"prestador_id":"<UUID_PRESTADOR>","servico_id":"<UUID_SERVICO>","data_hora":"2024-07-01T10:00:00Z","nome":"Cliente","contacto":"+351910000000"}'

# 7. Dashboard Merchant
curl http://localhost:8000/api/v1/dashboard/merchant/me/resumo \
  -H "Authorization: Bearer {{MERCHANT_TOKEN}}" \
  -H "X-Tenant-ID: {{TENANT_UUID}}"
```

> Use Swagger UI (`/docs`) para experimentar e gerar exemplos de payload dinamicamente.
