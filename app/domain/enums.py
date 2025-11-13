from enum import Enum


class UserRole(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    CLIENTE = "CLIENTE"
    MERCHANT = "MERCHANT"
    PRESTADOR = "PRESTADOR"


class PedidoStatus(str, Enum):
    CRIADO = "CRIADO"
    PENDENTE_PAGAMENTO = "PENDENTE_PAGAMENTO"
    PAGO = "PAGO"
    CANCELADO = "CANCELADO"


class AgendamentoStatus(str, Enum):
    PENDENTE = "PENDENTE"
    CONFIRMADO = "CONFIRMADO"
    CANCELADO = "CANCELADO"
    CONCLUIDO = "CONCLUIDO"
