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
    ACEITE = "ACEITE"
    EM_PREPARACAO = "EM_PREPARACAO"
    ENVIADO = "ENVIADO"
    CONCLUIDO = "CONCLUIDO"


class AgendamentoStatus(str, Enum):
    PENDENTE = "PENDENTE"
    CONFIRMADO = "CONFIRMADO"
    CANCELADO = "CANCELADO"
    CONCLUIDO = "CONCLUIDO"


class PedidoOrigem(str, Enum):
    WEB = "WEB"
    MOBILE = "MOBILE"
    BACKOFFICE = "BACKOFFICE"


class ServicoTipoAtendimento(str, Enum):
    PRESENCIAL = "PRESENCIAL"
    ONLINE = "ONLINE"
    DOMICILIO = "DOMICILIO"
    MISTO = "MISTO"
