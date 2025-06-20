"""
Sistema de Gerenciamento de Tarefas de Scraping

Gerencia tarefas de scraping em background com:
- Controle de estado e progresso
- Armazenamento em memória/Redis
- Histórico de execuções
- Cancelamento de tarefas
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
from enum import Enum
import time
import sys
import os
import traceback

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.scraper_pooled import scrape_catho_jobs_pooled
from src.core.scraper_optimized import scrape_catho_jobs_optimized
from src.systems.compressed_cache import CompressedCache
from src.systems.deduplicator import JobDeduplicator
from src.utils.filters import JobFilter
from api.models import ScrapingRequest, ScrapingStatusEnum, ScrapingProgress


class TaskManager:
    """
    Gerenciador central de tarefas de scraping
    
    Mantém registro de todas as tarefas e seus estados
    """
    
    def __init__(self):
        """Inicializa o gerenciador de tarefas"""
        # Armazena tarefas em memória (em produção, usar Redis/DB)
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self._initialized = False
        self._cleanup_task = None
        
    async def initialize(self):
        """Inicializa o gerenciador e inicia tarefas de manutenção"""
        if self._initialized:
            return
        
        print("📋 Inicializando gerenciador de tarefas...")
        
        # Iniciar tarefa de limpeza periódica
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        self._initialized = True
        print("✅ Gerenciador de tarefas inicializado!")
    
    async def shutdown(self):
        """Desliga o gerenciador gracefully"""
        print("🔌 Desligando gerenciador de tarefas...")
        
        # Cancelar tarefas ativas
        for task_id, task in self.active_tasks.items():
            if not task.done():
                task.cancel()
                print(f"  ❌ Cancelando tarefa {task_id}")
        
        # Aguardar tarefas terminarem
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        
        # Cancelar tarefa de limpeza
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self._initialized = False
        print("✅ Gerenciador de tarefas finalizado!")
    
    def create_task(self, task_id: str, user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria nova tarefa de scraping
        
        Args:
            task_id: ID único da tarefa
            user_id: ID do usuário que criou
            config: Configuração do scraping
            
        Returns:
            Dados da tarefa criada
        """
        task_data = {
            "task_id": task_id,
            "user_id": user_id,
            "status": ScrapingStatusEnum.PENDING,
            "config": config,
            "progress": {
                "current_page": 0,
                "total_pages": config.get("max_pages", 5),
                "jobs_found": 0,
                "jobs_processed": 0,
                "duplicates_removed": 0,
                "errors_count": 0,
                "elapsed_time_seconds": 0,
                "estimated_time_remaining": None
            },
            "started_at": datetime.now(),
            "completed_at": None,
            "error_message": None,
            "result_summary": None,
            "logs": []
        }
        
        self.tasks[task_id] = task_data
        return task_data
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retorna dados de uma tarefa"""
        return self.tasks.get(task_id)
    
    def get_user_history(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Retorna histórico de tarefas do usuário"""
        user_tasks = [
            task for task in self.tasks.values()
            if task["user_id"] == user_id
        ]
        
        # Ordenar por data de criação (mais recente primeiro)
        user_tasks.sort(key=lambda t: t["started_at"], reverse=True)
        
        # Aplicar paginação
        return user_tasks[offset:offset + limit]
    
    def get_active_count(self) -> int:
        """Retorna número de tarefas ativas"""
        return sum(
            1 for task in self.tasks.values()
            if task["status"] in [ScrapingStatusEnum.PENDING, ScrapingStatusEnum.RUNNING]
        )
    
    def is_healthy(self) -> bool:
        """Verifica se o gerenciador está saudável"""
        return self._initialized and self._cleanup_task and not self._cleanup_task.done()
    
    async def run_scraping(self, task_id: str, request: ScrapingRequest):
        """
        Executa tarefa de scraping em background
        
        Args:
            task_id: ID da tarefa
            request: Configuração do scraping
        """
        task_data = self.tasks.get(task_id)
        if not task_data:
            print(f"❌ Tarefa {task_id} não encontrada!")
            return
        
        # Criar asyncio.Task
        async_task = asyncio.create_task(self._execute_scraping(task_id, request))
        self.active_tasks[task_id] = async_task
        
        try:
            await async_task
        finally:
            # Remover da lista de tarefas ativas
            self.active_tasks.pop(task_id, None)
    
    async def _execute_scraping(self, task_id: str, request: ScrapingRequest):
        """Executa o scraping propriamente dito"""
        task_data = self.tasks[task_id]
        start_time = time.time()
        
        try:
            # Atualizar status para RUNNING
            task_data["status"] = ScrapingStatusEnum.RUNNING
            self._log_task(task_id, "Iniciando processo de scraping...")
            
            # Preparar callback para progresso
            def progress_callback(page: int, total: int, jobs: int):
                elapsed = time.time() - start_time
                task_data["progress"].update({
                    "current_page": page,
                    "total_pages": total,
                    "jobs_found": jobs,
                    "elapsed_time_seconds": elapsed
                })
                
                # Estimar tempo restante
                if page > 0:
                    time_per_page = elapsed / page
                    remaining_pages = total - page
                    task_data["progress"]["estimated_time_remaining"] = time_per_page * remaining_pages
                
                self._log_task(task_id, f"Processando página {page}/{total} - {jobs} vagas encontradas")
            
            # Escolher scraper baseado na configuração
            scraper_func = scrape_catho_jobs_pooled if request.use_pool else scrape_catho_jobs_optimized
            
            # Executar scraping
            self._log_task(task_id, f"Usando {'pool de conexões' if request.use_pool else 'scraper otimizado'}")
            
            jobs = await asyncio.to_thread(
                scraper_func,
                max_pages=request.max_pages,
                max_concurrent_jobs=request.max_concurrent_jobs,
                incremental=request.incremental,
                enable_deduplication=request.enable_deduplication,
                progress_callback=progress_callback
            )
            
            # Aplicar filtros se especificados
            if request.filters:
                self._log_task(task_id, "Aplicando filtros...")
                job_filter = JobFilter()
                
                # Configurar filtros
                if request.filters.technologies:
                    job_filter.set_technologies(request.filters.technologies)
                if request.filters.min_salary:
                    job_filter.set_salary_range(request.filters.min_salary, request.filters.max_salary)
                if request.filters.keywords:
                    job_filter.set_keywords(request.filters.keywords)
                if request.filters.exclude_keywords:
                    job_filter.set_exclude_keywords(request.filters.exclude_keywords)
                
                # Aplicar filtros
                original_count = len(jobs)
                jobs = job_filter.filter_jobs(jobs)
                filtered_count = original_count - len(jobs)
                
                self._log_task(task_id, f"Filtros aplicados: {filtered_count} vagas removidas")
            
            # Atualizar progresso final
            task_data["progress"]["jobs_processed"] = len(jobs)
            
            # Criar resumo
            task_data["result_summary"] = {
                "total_jobs_collected": len(jobs),
                "total_pages_processed": request.max_pages,
                "execution_time_seconds": time.time() - start_time,
                "filters_applied": bool(request.filters),
                "deduplication_enabled": request.enable_deduplication,
                "incremental_mode": request.incremental
            }
            
            # Marcar como completo
            task_data["status"] = ScrapingStatusEnum.COMPLETED
            task_data["completed_at"] = datetime.now()
            
            self._log_task(task_id, f"✅ Scraping concluído! {len(jobs)} vagas coletadas")
            
        except asyncio.CancelledError:
            # Tarefa foi cancelada
            task_data["status"] = ScrapingStatusEnum.CANCELLED
            task_data["completed_at"] = datetime.now()
            task_data["error_message"] = "Tarefa cancelada pelo usuário"
            self._log_task(task_id, "❌ Tarefa cancelada")
            raise
            
        except Exception as e:
            # Erro durante execução
            task_data["status"] = ScrapingStatusEnum.FAILED
            task_data["completed_at"] = datetime.now()
            task_data["error_message"] = str(e)
            task_data["error_traceback"] = traceback.format_exc()
            
            self._log_task(task_id, f"❌ Erro: {str(e)}")
            print(f"Erro na tarefa {task_id}:\n{traceback.format_exc()}")
    
    async def stop_task(self, task_id: str) -> bool:
        """
        Para uma tarefa em execução
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se parou com sucesso, False caso contrário
        """
        # Verificar se existe
        if task_id not in self.tasks:
            return False
        
        # Verificar se está ativa
        if task_id in self.active_tasks:
            async_task = self.active_tasks[task_id]
            if not async_task.done():
                async_task.cancel()
                self._log_task(task_id, "Solicitação de cancelamento enviada")
                return True
        
        return False
    
    def _log_task(self, task_id: str, message: str):
        """Adiciona log à tarefa"""
        task_data = self.tasks.get(task_id)
        if task_data:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "message": message
            }
            task_data["logs"].append(log_entry)
            
            # Limitar tamanho dos logs
            if len(task_data["logs"]) > 100:
                task_data["logs"] = task_data["logs"][-100:]
    
    async def _periodic_cleanup(self):
        """Limpa tarefas antigas periodicamente"""
        while True:
            try:
                await asyncio.sleep(3600)  # A cada hora
                
                # Remover tarefas antigas (mais de 24 horas)
                cutoff_time = datetime.now() - timedelta(hours=24)
                old_tasks = [
                    task_id for task_id, task in self.tasks.items()
                    if task["started_at"] < cutoff_time and 
                    task["status"] in [ScrapingStatusEnum.COMPLETED, ScrapingStatusEnum.FAILED]
                ]
                
                for task_id in old_tasks:
                    del self.tasks[task_id]
                
                if old_tasks:
                    print(f"🧹 Limpeza: {len(old_tasks)} tarefas antigas removidas")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Erro na limpeza periódica: {e}")


# Instância global do gerenciador
scraping_task_manager = TaskManager()


# Helper functions para métricas
def get_task_statistics() -> Dict[str, Any]:
    """Retorna estatísticas gerais das tarefas"""
    total_tasks = len(scraping_task_manager.tasks)
    
    status_count = {
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "cancelled": 0
    }
    
    total_jobs_collected = 0
    total_execution_time = 0
    
    for task in scraping_task_manager.tasks.values():
        status_count[task["status"]] += 1
        
        if task["result_summary"]:
            total_jobs_collected += task["result_summary"].get("total_jobs_collected", 0)
            total_execution_time += task["result_summary"].get("execution_time_seconds", 0)
    
    return {
        "total_tasks": total_tasks,
        "status_distribution": status_count,
        "total_jobs_collected": total_jobs_collected,
        "average_execution_time": total_execution_time / max(1, status_count["completed"]),
        "active_tasks": status_count["pending"] + status_count["running"]
    }