"""
Configurações da API

Centraliza todas as configurações usando Pydantic Settings
"""

try:
    # Tentar nova versão do pydantic
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    try:
        # Fallback para versão antiga
        from pydantic import BaseSettings, Field
    except ImportError:
        # Fallback manual se pydantic não estiver disponível
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        def Field(**kwargs):
            return kwargs.get('default')
from typing import List, Optional
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # API Configuration
    APP_NAME: str = "Catho Job Scraper API"
    APP_VERSION: str = "1.0.0"
    HOST: str = Field("0.0.0.0", env="API_HOST")
    PORT: int = Field(8000, env="API_PORT")
    DEBUG: bool = Field(False, env="DEBUG")
    
    # Security
    SECRET_KEY: str = Field(
        "your-secret-key-change-this-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="TOKEN_EXPIRE_MINUTES")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(10, env="RATE_LIMIT_BURST")
    
    # Cache Settings
    CACHE_DIR: str = Field("data/cache", env="CACHE_DIR")
    CACHE_MAX_AGE_HOURS: int = Field(6, env="CACHE_MAX_AGE_HOURS")
    
    # Scraping Settings
    MAX_CONCURRENT_SCRAPERS: int = Field(3, env="MAX_CONCURRENT_SCRAPERS")
    DEFAULT_MAX_PAGES: int = Field(5, env="DEFAULT_MAX_PAGES")
    DEFAULT_CONCURRENT_JOBS: int = Field(3, env="DEFAULT_CONCURRENT_JOBS")
    
    # Background Tasks
    TASK_CLEANUP_MINUTES: int = Field(60, env="TASK_CLEANUP_MINUTES")
    MAX_TASK_AGE_HOURS: int = Field(24, env="MAX_TASK_AGE_HOURS")
    
    # Database (optional)
    DATABASE_URL: Optional[str] = Field(None, env="DATABASE_URL")
    
    # Redis (optional)
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    
    # Monitoring
    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(9090, env="METRICS_PORT")
    
    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field("logs/api.log", env="LOG_FILE")
    
    # Email (optional)
    SMTP_HOST: Optional[str] = Field(None, env="SMTP_HOST")
    SMTP_PORT: Optional[int] = Field(587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")
    SMTP_FROM: Optional[str] = Field(None, env="SMTP_FROM")
    
    # Webhook
    WEBHOOK_TIMEOUT: int = Field(30, env="WEBHOOK_TIMEOUT")
    WEBHOOK_MAX_RETRIES: int = Field(3, env="WEBHOOK_MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instância global de configurações
settings = Settings()


# Validações customizadas
def validate_settings():
    """Valida configurações críticas"""
    
    # Verificar SECRET_KEY em produção
    if not settings.DEBUG and settings.SECRET_KEY == "your-secret-key-change-this-in-production":
        raise ValueError("SECRET_KEY deve ser alterada em produção!")
    
    # Criar diretórios necessários
    os.makedirs(settings.CACHE_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    
    # Avisos
    if not settings.DATABASE_URL:
        print("⚠️  Aviso: DATABASE_URL não configurada - usando armazenamento em memória")
    
    if not settings.REDIS_URL:
        print("⚠️  Aviso: REDIS_URL não configurada - background tasks limitadas")
    
    if not settings.SMTP_HOST:
        print("⚠️  Aviso: Email não configurado - notificações por email desabilitadas")


# Executar validações ao importar
validate_settings()


# Helper functions para configurações
def get_database_settings():
    """Retorna configurações do banco de dados"""
    if not settings.DATABASE_URL:
        return None
    
    # Parse DATABASE_URL
    # postgresql://user:password@localhost:5432/dbname
    return {
        "url": settings.DATABASE_URL,
        "echo": settings.DEBUG,
        "pool_size": 10,
        "max_overflow": 20
    }


def get_redis_settings():
    """Retorna configurações do Redis"""
    if not settings.REDIS_URL:
        return None
    
    return {
        "url": settings.REDIS_URL,
        "decode_responses": True,
        "max_connections": 50
    }


def get_smtp_settings():
    """Retorna configurações de email"""
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        return None
    
    return {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "username": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "from_email": settings.SMTP_FROM or settings.SMTP_USER,
        "use_tls": True
    }


# Configurações de ambiente
def is_production():
    """Verifica se está em produção"""
    return not settings.DEBUG


def is_development():
    """Verifica se está em desenvolvimento"""
    return settings.DEBUG


# Export all settings
__all__ = [
    "settings",
    "validate_settings",
    "get_database_settings",
    "get_redis_settings",
    "get_smtp_settings",
    "is_production",
    "is_development"
]