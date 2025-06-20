"""
API REST para Catho Job Scraper

Sistema completo de API com FastAPI incluindo:
- Endpoints para controle de scraping
- Busca e consulta de dados
- Gerenciamento de cache
- Autenticação JWT
- Documentação automática (Swagger/ReDoc)
- Background tasks
- Rate limiting
- Monitoramento
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import asyncio
import time
import os
import sys
from datetime import datetime, timedelta
import uuid

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Importar módulos do scraper
from src.core.scraper_pooled import scrape_catho_jobs_pooled
from src.systems.compressed_cache import CompressedCache
from src.systems.deduplicator import JobDeduplicator
from src.utils.filters import JobFilter

# Importar configurações da API
from api.config import settings
from api.models import (
    ScrapingRequest, ScrapingResponse, ScrapingStatus,
    SearchRequest, SearchResponse, JobModel,
    CacheStatsResponse, SystemHealthResponse,
    TokenResponse, UserLogin
)
from api.auth import (
    authenticate_user, create_access_token, get_current_user,
    get_password_hash, verify_password
)
from api.tasks import scraping_task_manager
from api.rate_limiter import RateLimiter
from api.database import init_db

# Configurar rate limiter
rate_limiter = RateLimiter(requests_per_minute=60)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    # Startup
    print("🚀 Iniciando API REST...")
    await init_db()
    await scraping_task_manager.initialize()
    print("✅ API pronta para receber requisições!")
    
    yield
    
    # Shutdown
    print("🔌 Desligando API...")
    await scraping_task_manager.shutdown()
    print("👋 API finalizada!")

# Criar aplicação FastAPI
app = FastAPI(
    title="Catho Job Scraper API",
    description="""
    API REST completa para o sistema de scraping de vagas do Catho.
    
    ## Funcionalidades
    
    * **Scraping** - Iniciar, parar e monitorar processos de scraping
    * **Busca** - Pesquisar vagas com filtros avançados
    * **Cache** - Gerenciar cache e índices
    * **Estatísticas** - Analytics e métricas do sistema
    * **Autenticação** - Sistema seguro com JWT
    
    ## Autenticação
    
    A maioria dos endpoints requer autenticação via Bearer Token.
    Use `/auth/token` para obter um token JWT.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Aplica rate limiting em todas as requisições"""
    client_ip = request.client.host
    
    if not rate_limiter.check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )
    
    response = await call_next(request)
    return response

# ==================== ENDPOINTS DE AUTENTICAÇÃO ====================

@app.post("/auth/token", response_model=TokenResponse, tags=["Authentication"])
async def login(user_credentials: UserLogin):
    """
    Autenticar usuário e obter token JWT
    
    - **username**: Nome de usuário
    - **password**: Senha do usuário
    
    Retorna um token JWT válido por 30 minutos
    """
    user = authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

# ==================== ENDPOINTS DE SCRAPING ====================

@app.post("/api/v1/scraping/start", 
         response_model=ScrapingResponse,
         tags=["Scraping"],
         summary="Iniciar novo processo de scraping")
async def start_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Inicia um novo processo de scraping em background
    
    Parâmetros:
    - **max_pages**: Número máximo de páginas para processar (1-20)
    - **max_concurrent_jobs**: Jobs simultâneos (1-5)
    - **incremental**: Se deve processar apenas dados novos
    - **enable_deduplication**: Se deve remover duplicatas
    - **filters**: Filtros opcionais (tecnologias, salário, etc)
    
    Retorna:
    - **task_id**: ID único para acompanhar o progresso
    - **status**: Status inicial do processo
    """
    # Validar limites
    if request.max_pages > 20:
        raise HTTPException(status_code=400, detail="Máximo de 20 páginas permitido")
    
    if request.max_concurrent_jobs > 5:
        raise HTTPException(status_code=400, detail="Máximo de 5 jobs simultâneos")
    
    # Criar task ID único
    task_id = str(uuid.uuid4())
    
    # Criar task de scraping
    task = scraping_task_manager.create_task(
        task_id=task_id,
        user_id=current_user["username"],
        config=request.dict()
    )
    
    # Adicionar ao background
    background_tasks.add_task(
        scraping_task_manager.run_scraping,
        task_id,
        request
    )
    
    return ScrapingResponse(
        task_id=task_id,
        status="started",
        message=f"Scraping iniciado com ID {task_id}",
        started_at=datetime.now(),
        config=request.dict()
    )

@app.get("/api/v1/scraping/status/{task_id}",
         response_model=ScrapingStatus,
         tags=["Scraping"],
         summary="Verificar status de scraping")
async def get_scraping_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Verifica o status de um processo de scraping
    
    Retorna informações detalhadas sobre o progresso, incluindo:
    - Status atual (running, completed, failed)
    - Progresso (páginas processadas, vagas encontradas)
    - Mensagens de erro (se houver)
    - Estatísticas de performance
    """
    task = scraping_task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")
    
    # Verificar se usuário tem acesso
    if task["user_id"] != current_user["username"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return task

@app.post("/api/v1/scraping/stop/{task_id}",
          tags=["Scraping"],
          summary="Parar processo de scraping")
async def stop_scraping(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Para um processo de scraping em execução
    
    O processo será interrompido de forma segura, salvando
    todos os dados coletados até o momento.
    """
    success = await scraping_task_manager.stop_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task não encontrada ou já finalizada")
    
    return {"message": f"Scraping {task_id} parado com sucesso"}

@app.get("/api/v1/scraping/history",
         tags=["Scraping"],
         summary="Histórico de scraping")
async def get_scraping_history(
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna histórico de processos de scraping do usuário
    
    - **limit**: Número máximo de registros
    - **offset**: Paginação
    """
    history = scraping_task_manager.get_user_history(
        user_id=current_user["username"],
        limit=limit,
        offset=offset
    )
    
    return {
        "total": len(history),
        "limit": limit,
        "offset": offset,
        "tasks": history
    }

# ==================== ENDPOINTS DE BUSCA ====================

@app.post("/api/v1/data/search",
          response_model=SearchResponse,
          tags=["Data"],
          summary="Buscar vagas")
async def search_jobs(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Busca vagas no cache com filtros avançados
    
    Filtros disponíveis:
    - **companies**: Lista de empresas
    - **technologies**: Lista de tecnologias
    - **locations**: Lista de localizações
    - **salary_min**: Salário mínimo
    - **date_from**: Data inicial
    - **date_to**: Data final
    - **limit**: Máximo de resultados
    - **offset**: Paginação
    """
    cache = CompressedCache()
    
    # Converter filtros para formato do cache
    criteria = {}
    if request.companies:
        criteria['companies'] = request.companies
    if request.technologies:
        criteria['technologies'] = request.technologies
    if request.locations:
        criteria['locations'] = request.locations
    if request.date_from:
        criteria['date_from'] = request.date_from
    if request.date_to:
        criteria['date_to'] = request.date_to
    
    # Buscar no cache
    results = cache.search_cache(criteria)
    
    # Aplicar paginação
    total = len(results)
    start = request.offset
    end = start + request.limit
    paginated_results = results[start:end]
    
    # Converter para modelo de resposta
    jobs = []
    for entry in paginated_results:
        # Ler dados completos do arquivo
        cached_data = await cache.get(entry.url)
        if cached_data and 'jobs' in cached_data:
            for job in cached_data['jobs']:
                jobs.append(JobModel(**job))
    
    return SearchResponse(
        total=total,
        limit=request.limit,
        offset=request.offset,
        jobs=jobs,
        query_time_ms=0  # TODO: Implementar medição
    )

@app.get("/api/v1/data/stats",
         tags=["Data"],
         summary="Estatísticas gerais")
async def get_statistics(current_user: dict = Depends(get_current_user)):
    """
    Retorna estatísticas gerais do sistema
    
    Inclui:
    - Total de vagas no cache
    - Top empresas
    - Top tecnologias
    - Distribuição por localização
    - Tendências temporais
    """
    cache = CompressedCache()
    
    stats = cache.get_cache_stats()
    top_companies = cache.get_top_companies(10)
    top_technologies = cache.get_top_technologies(10)
    
    return {
        "total_jobs": stats['index']['total_jobs'],
        "total_entries": stats['index']['total_entries'],
        "cache_size_mb": stats['compression']['total_cache_size_mb'],
        "compression_ratio": stats['compression']['average_compression_ratio'],
        "top_companies": [
            {"name": company, "count": count} 
            for company, count in top_companies
        ],
        "top_technologies": [
            {"name": tech, "count": count} 
            for tech, count in top_technologies
        ],
        "last_updated": stats['index'].get('last_updated')
    }

# ==================== ENDPOINTS DE CACHE ====================

@app.get("/api/v1/cache/stats",
         response_model=CacheStatsResponse,
         tags=["Cache"],
         summary="Estatísticas do cache")
async def get_cache_stats(current_user: dict = Depends(get_current_user)):
    """
    Retorna estatísticas detalhadas do cache
    
    Inclui informações sobre:
    - Tamanho e compressão
    - Número de entradas
    - Taxa de hit/miss
    - Idade dos dados
    """
    cache = CompressedCache()
    stats = cache.get_cache_stats()
    
    return CacheStatsResponse(
        total_entries=stats['index']['total_entries'],
        total_jobs=stats['index']['total_jobs'],
        cache_size_mb=stats['compression']['total_cache_size_mb'],
        compression_ratio=stats['compression']['average_compression_ratio'],
        oldest_entry=stats['index'].get('oldest_entry'),
        newest_entry=stats['index'].get('newest_entry'),
        last_updated=stats['index'].get('last_updated')
    )

@app.post("/api/v1/cache/clean",
          tags=["Cache"],
          summary="Limpar cache")
async def clean_cache(
    remove_duplicates: bool = True,
    remove_old: bool = False,
    max_age_days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """
    Limpa o cache removendo dados antigos ou duplicados
    
    Parâmetros:
    - **remove_duplicates**: Remove vagas duplicadas
    - **remove_old**: Remove dados antigos
    - **max_age_days**: Idade máxima em dias (se remove_old=true)
    
    ⚠️ Requer privilégios de administrador
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem limpar o cache")
    
    results = {
        "duplicates_removed": 0,
        "old_entries_removed": 0
    }
    
    if remove_duplicates:
        deduplicator = JobDeduplicator()
        results["duplicates_removed"] = deduplicator.clean_existing_files("data")
    
    if remove_old:
        # TODO: Implementar remoção de dados antigos
        pass
    
    return {
        "message": "Cache limpo com sucesso",
        "results": results
    }

@app.post("/api/v1/cache/rebuild-index",
          tags=["Cache"],
          summary="Reconstruir índices")
async def rebuild_cache_index(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Reconstrói os índices do cache para busca rápida
    
    Este processo pode demorar alguns minutos dependendo
    do tamanho do cache. Será executado em background.
    
    ⚠️ Requer privilégios de administrador
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem reconstruir índices")
    
    task_id = str(uuid.uuid4())
    
    # TODO: Adicionar ao background
    background_tasks.add_task(rebuild_index_task, task_id)
    
    return {
        "message": "Reconstrução de índices iniciada",
        "task_id": task_id
    }

# ==================== ENDPOINTS DE SISTEMA ====================

@app.get("/api/v1/health",
         response_model=SystemHealthResponse,
         tags=["System"],
         summary="Health check")
async def health_check():
    """
    Verifica a saúde do sistema
    
    Retorna o status de todos os componentes:
    - API
    - Cache
    - Scraper
    - Background tasks
    """
    cache = CompressedCache()
    
    # Verificar componentes
    components = {
        "api": "healthy",
        "cache": "healthy" if os.path.exists("data/cache") else "unhealthy",
        "scraper": "healthy",  # TODO: Verificar pool de conexões
        "background_tasks": "healthy" if scraping_task_manager.is_healthy() else "unhealthy"
    }
    
    overall_health = "healthy" if all(v == "healthy" for v in components.values()) else "degraded"
    
    return SystemHealthResponse(
        status=overall_health,
        timestamp=datetime.now(),
        version="1.0.0",
        uptime_seconds=int(time.time() - app.state.start_time) if hasattr(app.state, 'start_time') else 0,
        components=components
    )

@app.get("/api/v1/metrics",
         tags=["System"],
         summary="Métricas do sistema")
async def get_metrics(current_user: dict = Depends(get_current_user)):
    """
    Retorna métricas detalhadas do sistema
    
    Inclui:
    - Taxa de requisições
    - Tempo de resposta
    - Uso de recursos
    - Estatísticas de scraping
    
    ⚠️ Requer privilégios de administrador
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem ver métricas")
    
    # TODO: Implementar coleta de métricas reais
    return {
        "requests_per_minute": rate_limiter.get_current_rpm(),
        "active_scraping_tasks": scraping_task_manager.get_active_count(),
        "total_jobs_scraped": 0,  # TODO: Implementar contador
        "average_response_time_ms": 0,  # TODO: Implementar medição
        "cache_hit_rate": 0,  # TODO: Implementar medição
    }

# ==================== ROOT ENDPOINT ====================

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raiz com informações da API
    """
    return {
        "name": "Catho Job Scraper API",
        "version": "1.0.0",
        "documentation": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health",
        "description": "API REST completa para scraping de vagas do Catho"
    }

# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler customizado para erros HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para erros não tratados"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    app.state.start_time = time.time()
    print(f"🚀 API iniciada em: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 Documentação: http://{settings.HOST}:{settings.PORT}/docs")

# ==================== HELPER FUNCTIONS ====================

async def rebuild_index_task(task_id: str):
    """Task para reconstruir índices em background"""
    cache = CompressedCache()
    count = cache.rebuild_index()
    # TODO: Salvar resultado da task
    return count

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )