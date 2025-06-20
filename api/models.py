"""
Modelos Pydantic para a API

Define todos os schemas de request/response da API
com validação automática e documentação
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class ScrapingStatusEnum(str, Enum):
    """Status possíveis de um processo de scraping"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    """Roles de usuário"""
    USER = "user"
    ADMIN = "admin"


# ==================== MODELOS DE AUTENTICAÇÃO ====================

class UserLogin(BaseModel):
    """Request para login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    
    class Config:
        schema_extra = {
            "example": {
                "username": "usuario_teste",
                "password": "senha_segura123"
            }
        }


class TokenResponse(BaseModel):
    """Response com token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Tempo de expiração em segundos")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class User(BaseModel):
    """Modelo de usuário"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


# ==================== MODELOS DE SCRAPING ====================

class ScrapingFilters(BaseModel):
    """Filtros para aplicar durante o scraping"""
    technologies: Optional[List[str]] = Field(None, description="Tecnologias desejadas")
    min_salary: Optional[int] = Field(None, ge=0, description="Salário mínimo")
    max_salary: Optional[int] = Field(None, ge=0, description="Salário máximo")
    experience_levels: Optional[List[str]] = Field(None, description="Níveis de experiência")
    company_types: Optional[List[str]] = Field(None, description="Tipos de empresa")
    keywords: Optional[List[str]] = Field(None, description="Palavras-chave")
    exclude_keywords: Optional[List[str]] = Field(None, description="Palavras para excluir")
    
    @validator('max_salary')
    def validate_salary_range(cls, v, values):
        if v and 'min_salary' in values and values['min_salary']:
            if v < values['min_salary']:
                raise ValueError('max_salary deve ser maior que min_salary')
        return v


class ScrapingRequest(BaseModel):
    """Request para iniciar scraping"""
    max_pages: int = Field(5, ge=1, le=20, description="Número máximo de páginas")
    max_concurrent_jobs: int = Field(3, ge=1, le=5, description="Jobs simultâneos")
    incremental: bool = Field(True, description="Processar apenas dados novos")
    enable_deduplication: bool = Field(True, description="Remover duplicatas")
    use_pool: bool = Field(True, description="Usar pool de conexões")
    filters: Optional[ScrapingFilters] = Field(None, description="Filtros opcionais")
    
    class Config:
        schema_extra = {
            "example": {
                "max_pages": 5,
                "max_concurrent_jobs": 3,
                "incremental": True,
                "enable_deduplication": True,
                "use_pool": True,
                "filters": {
                    "technologies": ["Python", "Django"],
                    "min_salary": 5000,
                    "experience_levels": ["Pleno", "Senior"]
                }
            }
        }


class ScrapingResponse(BaseModel):
    """Response ao iniciar scraping"""
    task_id: str = Field(..., description="ID único da task")
    status: str = Field(..., description="Status inicial")
    message: str = Field(..., description="Mensagem de confirmação")
    started_at: datetime
    config: Dict[str, Any] = Field(..., description="Configuração utilizada")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "started",
                "message": "Scraping iniciado com ID 550e8400-e29b-41d4-a716-446655440000",
                "started_at": "2024-01-15T10:30:00",
                "config": {
                    "max_pages": 5,
                    "incremental": True
                }
            }
        }


class ScrapingProgress(BaseModel):
    """Progresso do scraping"""
    current_page: int = Field(0, ge=0)
    total_pages: int = Field(0, ge=0)
    jobs_found: int = Field(0, ge=0)
    jobs_processed: int = Field(0, ge=0)
    duplicates_removed: int = Field(0, ge=0)
    errors_count: int = Field(0, ge=0)
    elapsed_time_seconds: float = Field(0, ge=0)
    estimated_time_remaining: Optional[float] = None


class ScrapingStatus(BaseModel):
    """Status detalhado do scraping"""
    task_id: str
    status: ScrapingStatusEnum
    progress: ScrapingProgress
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "progress": {
                    "current_page": 3,
                    "total_pages": 5,
                    "jobs_found": 45,
                    "jobs_processed": 42,
                    "duplicates_removed": 3,
                    "errors_count": 0,
                    "elapsed_time_seconds": 120.5
                },
                "started_at": "2024-01-15T10:30:00",
                "completed_at": None,
                "error_message": None
            }
        }


# ==================== MODELOS DE DADOS/BUSCA ====================

class JobModel(BaseModel):
    """Modelo de uma vaga"""
    titulo: str
    empresa: str
    localizacao: str = "Remoto"
    link: str
    salario: Optional[str] = None
    regime: Optional[str] = None
    nivel: Optional[str] = None
    nivel_categorizado: Optional[str] = None
    descricao: Optional[str] = None
    tecnologias_detectadas: List[str] = Field(default_factory=list)
    tipo_empresa: Optional[str] = None
    beneficios: List[str] = Field(default_factory=list)
    data_publicacao: Optional[str] = None
    data_coleta: str
    score_qualidade: Optional[float] = Field(None, ge=0, le=100)
    
    class Config:
        schema_extra = {
            "example": {
                "titulo": "Desenvolvedor Python Senior",
                "empresa": "TechCorp",
                "localizacao": "São Paulo, SP",
                "link": "https://catho.com.br/vagas/123",
                "salario": "R$ 8.000 - R$ 12.000",
                "regime": "CLT",
                "nivel": "Senior",
                "tecnologias_detectadas": ["Python", "Django", "PostgreSQL"],
                "data_coleta": "2024-01-15 10:30:00",
                "score_qualidade": 92.5
            }
        }


class SearchRequest(BaseModel):
    """Request para busca de vagas"""
    query: Optional[str] = Field(None, description="Busca por texto livre")
    companies: Optional[List[str]] = Field(None, description="Filtrar por empresas")
    technologies: Optional[List[str]] = Field(None, description="Filtrar por tecnologias")
    locations: Optional[List[str]] = Field(None, description="Filtrar por localizações")
    levels: Optional[List[str]] = Field(None, description="Filtrar por níveis")
    salary_min: Optional[int] = Field(None, ge=0, description="Salário mínimo")
    salary_max: Optional[int] = Field(None, ge=0, description="Salário máximo")
    date_from: Optional[datetime] = Field(None, description="Data inicial")
    date_to: Optional[datetime] = Field(None, description="Data final")
    limit: int = Field(20, ge=1, le=100, description="Limite de resultados")
    offset: int = Field(0, ge=0, description="Offset para paginação")
    sort_by: Optional[str] = Field("date", description="Campo para ordenação")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")
    
    class Config:
        schema_extra = {
            "example": {
                "technologies": ["Python", "Django"],
                "locations": ["São Paulo", "Remoto"],
                "salary_min": 5000,
                "limit": 20,
                "offset": 0
            }
        }


class SearchResponse(BaseModel):
    """Response da busca de vagas"""
    total: int = Field(..., description="Total de resultados encontrados")
    limit: int = Field(..., description="Limite aplicado")
    offset: int = Field(..., description="Offset aplicado")
    jobs: List[JobModel] = Field(..., description="Lista de vagas")
    query_time_ms: int = Field(..., description="Tempo de busca em ms")
    
    class Config:
        schema_extra = {
            "example": {
                "total": 150,
                "limit": 20,
                "offset": 0,
                "jobs": [{"titulo": "Dev Python", "empresa": "TechCorp"}],
                "query_time_ms": 45
            }
        }


# ==================== MODELOS DE CACHE ====================

class CacheStatsResponse(BaseModel):
    """Response com estatísticas do cache"""
    total_entries: int = Field(..., description="Total de entradas no cache")
    total_jobs: int = Field(..., description="Total de vagas cacheadas")
    cache_size_mb: float = Field(..., description="Tamanho do cache em MB")
    compression_ratio: float = Field(..., description="Taxa de compressão")
    oldest_entry: Optional[str] = Field(None, description="Data da entrada mais antiga")
    newest_entry: Optional[str] = Field(None, description="Data da entrada mais recente")
    last_updated: Optional[str] = Field(None, description="Última atualização")
    
    class Config:
        schema_extra = {
            "example": {
                "total_entries": 250,
                "total_jobs": 3500,
                "cache_size_mb": 12.5,
                "compression_ratio": 72.3,
                "oldest_entry": "2024-01-01T00:00:00",
                "newest_entry": "2024-01-15T10:30:00",
                "last_updated": "2024-01-15T10:35:00"
            }
        }


class CacheCleanRequest(BaseModel):
    """Request para limpeza de cache"""
    remove_duplicates: bool = Field(True, description="Remover duplicatas")
    remove_old: bool = Field(False, description="Remover dados antigos")
    max_age_days: int = Field(7, ge=1, le=30, description="Idade máxima em dias")
    
    class Config:
        schema_extra = {
            "example": {
                "remove_duplicates": True,
                "remove_old": True,
                "max_age_days": 7
            }
        }


# ==================== MODELOS DE SISTEMA ====================

class SystemHealthResponse(BaseModel):
    """Response do health check"""
    status: str = Field(..., description="Status geral do sistema")
    timestamp: datetime
    version: str
    uptime_seconds: int = Field(..., ge=0)
    components: Dict[str, str] = Field(..., description="Status de cada componente")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00",
                "version": "1.0.0",
                "uptime_seconds": 3600,
                "components": {
                    "api": "healthy",
                    "cache": "healthy",
                    "scraper": "healthy",
                    "background_tasks": "healthy"
                }
            }
        }


class MetricsResponse(BaseModel):
    """Response com métricas do sistema"""
    requests_per_minute: float = Field(..., ge=0)
    active_scraping_tasks: int = Field(..., ge=0)
    total_jobs_scraped: int = Field(..., ge=0)
    average_response_time_ms: float = Field(..., ge=0)
    cache_hit_rate: float = Field(..., ge=0, le=100)
    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=100)
    memory_usage_mb: Optional[float] = Field(None, ge=0)
    
    class Config:
        schema_extra = {
            "example": {
                "requests_per_minute": 45.2,
                "active_scraping_tasks": 2,
                "total_jobs_scraped": 15420,
                "average_response_time_ms": 125.5,
                "cache_hit_rate": 85.3,
                "cpu_usage_percent": 35.2,
                "memory_usage_mb": 512.8
            }
        }


# ==================== MODELOS DE ERRO ====================

class ErrorResponse(BaseModel):
    """Response padrão para erros"""
    error: str = Field(..., description="Mensagem de erro")
    status_code: int = Field(..., description="Código HTTP")
    timestamp: datetime = Field(default_factory=datetime.now)
    path: str = Field(..., description="Path da requisição")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Task não encontrada",
                "status_code": 404,
                "timestamp": "2024-01-15T10:30:00",
                "path": "/api/v1/scraping/status/invalid-id",
                "details": None
            }
        }


# ==================== MODELOS DE WEBHOOK ====================

class WebhookConfig(BaseModel):
    """Configuração de webhook para notificações"""
    url: str = Field(..., description="URL do webhook")
    events: List[str] = Field(..., description="Eventos para notificar")
    headers: Optional[Dict[str, str]] = Field(None, description="Headers customizados")
    active: bool = Field(True, description="Se o webhook está ativo")
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/webhook",
                "events": ["scraping.completed", "scraping.failed"],
                "headers": {"X-API-Key": "secret"},
                "active": True
            }
        }