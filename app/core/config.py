from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Configurações principais
    app_name: str = "Fahamo Multi Service API"
    environment: str = "local"

    # Base de dados
    database_url: str = "postgresql+psycopg://msb:msb@localhost:5432/msb"

    # Segurança / JWT
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Multi-tenant
    tenant_header: str = "X-Tenant-ID"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


settings = Settings()
