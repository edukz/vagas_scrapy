"""
Sistema de Pool de Conexões Reutilizáveis

Este módulo implementa um pool de páginas do browser para reutilização,
reduzindo o overhead de criação/destruição de conexões e melhorando
significativamente a performance.

Benefícios:
- ⚡ Reduz 100-500ms por requisição
- 🔄 Reutiliza conexões HTTP/browser
- 🧹 Limpeza automática de recursos
- 📊 Métricas detalhadas de performance
"""

import asyncio
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from playwright.async_api import Page, Browser
from collections import deque
import threading


@dataclass
class PooledPage:
    """
    Representa uma página no pool com metadados
    """
    page: Page
    created_at: datetime
    last_used: datetime
    usage_count: int = 0
    is_busy: bool = False
    errors_count: int = 0
    max_errors: int = 3
    
    def mark_used(self) -> None:
        """Marca página como usada"""
        self.last_used = datetime.now()
        self.usage_count += 1
        self.is_busy = True
    
    def mark_available(self) -> None:
        """Marca página como disponível"""
        self.is_busy = False
    
    def mark_error(self) -> None:
        """Registra erro na página"""
        self.errors_count += 1
    
    def should_recreate(self, max_age_minutes: int = 30) -> bool:
        """Verifica se página deve ser recriada"""
        age = datetime.now() - self.created_at
        return (
            self.errors_count >= self.max_errors or
            age > timedelta(minutes=max_age_minutes) or
            self.usage_count > 100  # Evitar memory leaks
        )
    
    async def reset(self) -> bool:
        """
        Reseta página para estado limpo - versão robusta
        
        Returns:
            True se sucesso, False se deve ser descartada
        """
        try:
            # Tentar limpar storage apenas se possível
            try:
                # Verificar se podemos acessar localStorage primeiro
                await self.page.evaluate("typeof(Storage) !== 'undefined' && localStorage")
                await self.page.evaluate("localStorage.clear()")
            except Exception:
                # Ignore localStorage errors - muitas vezes o site bloqueia acesso
                pass
            
            try:
                # Tentar limpar sessionStorage
                await self.page.evaluate("typeof(Storage) !== 'undefined' && sessionStorage")
                await self.page.evaluate("sessionStorage.clear()")
            except Exception:
                # Ignore sessionStorage errors também
                pass
            
            # Limpar cookies (isso geralmente funciona)
            try:
                context = self.page.context
                await context.clear_cookies()
            except Exception:
                # Se nem cookies conseguimos limpar, a página pode estar com problemas
                pass
            
            # Navegar para página limpa
            try:
                await self.page.goto("about:blank", timeout=5000)
            except Exception:
                # Se não conseguir navegar, a página provavelmente tem problemas sérios
                self.mark_error()
                return False
            
            return True
            
        except Exception as e:
            self.mark_error()
            # Log apenas em casos realmente críticos, não para erros de localStorage
            if "localStorage" not in str(e) and "sessionStorage" not in str(e):
                print(f"⚠️ Erro crítico ao resetar página: {e}")
            return False


class ConnectionPool:
    """
    Pool de conexões/páginas reutilizáveis para otimização de performance
    
    Gerencia um pool de páginas do browser que podem ser reutilizadas
    ao invés de criar novas a cada requisição, reduzindo significativamente
    o overhead de setup/teardown.
    """
    
    def __init__(self, 
                 min_size: int = 2,
                 max_size: int = 10,
                 max_age_minutes: int = 30,
                 cleanup_interval_seconds: int = 60):
        """
        Inicializa pool de conexões
        
        Args:
            min_size: Número mínimo de páginas no pool
            max_size: Número máximo de páginas no pool
            max_age_minutes: Idade máxima de uma página antes de recriar
            cleanup_interval_seconds: Intervalo de limpeza automática
        """
        self.min_size = min_size
        self.max_size = max_size
        self.max_age_minutes = max_age_minutes
        self.cleanup_interval = cleanup_interval_seconds
        
        # Pool de páginas
        self.available_pages: deque[PooledPage] = deque()
        self.busy_pages: List[PooledPage] = []
        self.browser: Optional[Browser] = None
        
        # Controle de estado
        self.is_initialized = False
        self.is_shutdown = False
        self._lock = asyncio.Lock()
        
        # Estatísticas
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'pages_created': 0,
            'pages_destroyed': 0,
            'average_wait_time': 0.0,
            'total_wait_time': 0.0,
            'errors': 0,
            'cleanup_runs': 0
        }
        
        # Task de limpeza
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self, browser: Browser) -> None:
        """
        Inicializa o pool com um browser
        """
        if self.is_initialized:
            return
        
        self.browser = browser
        
        # Criar páginas iniciais
        for _ in range(self.min_size):
            new_page = await self._create_new_page()
            if new_page:
                self.available_pages.append(new_page)
        
        # Iniciar task de limpeza
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.is_initialized = True
        print(f"✅ Pool de conexões inicializado: {len(self.available_pages)} páginas prontas")
    
    async def _create_new_page(self) -> Optional[PooledPage]:
        """
        Cria nova página no pool
        """
        if not self.browser or self.is_shutdown:
            return None
        
        try:
            page = await self.browser.new_page()
            
            # Configurar página para performance
            await page.set_extra_http_headers({
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=300'
            })
            
            # Desabilitar recursos desnecessários para performance
            await page.route("**/*.{png,jpg,jpeg,gif,css,woff,woff2}", lambda route: route.abort())
            
            pooled_page = PooledPage(
                page=page,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            
            self.stats['pages_created'] += 1
            return pooled_page
            
        except Exception as e:
            print(f"❌ Erro ao criar página no pool: {e}")
            self.stats['errors'] += 1
            return None
    
    async def get_page(self, timeout_seconds: float = 10.0) -> Optional[Page]:
        """
        Obtém página do pool ou cria nova se necessário - VERSÃO CORRIGIDA
        
        Args:
            timeout_seconds: Tempo máximo para aguardar página
            
        Returns:
            Página disponível ou None se timeout
        """
        if not self.is_initialized:
            print("❌ Pool não inicializado")
            return None
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        pooled_page = None
        
        # Manter lock durante toda operação para evitar race conditions
        async with self._lock:
            # Tentar pegar página disponível
            while self.available_pages:
                candidate = self.available_pages.popleft()
                
                # Verificar se página ainda é válida
                if candidate.should_recreate(self.max_age_minutes):
                    await self._destroy_page(candidate)
                    continue
                
                # Tentar resetar página
                if await candidate.reset():
                    candidate.mark_used()
                    self.busy_pages.append(candidate)
                    pooled_page = candidate
                    
                    # Estatísticas
                    wait_time = time.time() - start_time
                    self.stats['cache_hits'] += 1
                    self.stats['total_wait_time'] += wait_time
                    self.stats['average_wait_time'] = self.stats['total_wait_time'] / self.stats['total_requests']
                    
                    print(f"🔄 Página reutilizada do pool (uso #{candidate.usage_count})")
                    break
                else:
                    await self._destroy_page(candidate)
            
            # Se não achou página disponível, tentar criar nova
            if not pooled_page and len(self.busy_pages) + len(self.available_pages) < self.max_size:
                new_page = await self._create_new_page()
                if new_page:
                    new_page.mark_used()
                    self.busy_pages.append(new_page)
                    pooled_page = new_page
                    
                    # Estatísticas
                    wait_time = time.time() - start_time
                    self.stats['cache_misses'] += 1
                    self.stats['total_wait_time'] += wait_time
                    self.stats['average_wait_time'] = self.stats['total_wait_time'] / self.stats['total_requests']
                    
                    print(f"🆕 Nova página criada no pool")
        
        # Se conseguiu página, retornar
        if pooled_page:
            return pooled_page.page
        
        # Aguardar página ficar disponível (com timeout)
        deadline = time.time() + timeout_seconds
        wait_interval = 0.05  # 50ms entre verificações
        
        while time.time() < deadline:
            async with self._lock:
                if self.available_pages:
                    # Tentar recursivamente mas com timeout reduzido
                    remaining_time = deadline - time.time()
                    if remaining_time > 0:
                        return await self.get_page(remaining_time)
                    break
            
            await asyncio.sleep(wait_interval)
        
        print(f"⏰ Timeout ao aguardar página do pool após {timeout_seconds}s")
        self.stats['errors'] += 1
        return None
    
    async def return_page(self, page: Page, had_error: bool = False) -> None:
        """
        Retorna página para o pool - VERSÃO CORRIGIDA
        
        Args:
            page: Página a ser retornada
            had_error: Se houve erro ao usar a página
        """
        # Toda operação dentro do lock para evitar race conditions
        async with self._lock:
            # Encontrar página nos busy_pages
            pooled_page = None
            for i, p in enumerate(self.busy_pages):
                if p.page == page:
                    pooled_page = self.busy_pages.pop(i)
                    break
            
            if not pooled_page:
                print("⚠️ Página não encontrada no pool")
                return
            
            # Marcar erro se houve
            if had_error:
                pooled_page.mark_error()
            
            # Verificar se deve descartar página
            if pooled_page.should_recreate(self.max_age_minutes):
                await self._destroy_page(pooled_page)
                
                # Criar nova página se pool ficou muito pequeno
                # Fazer isso dentro do mesmo lock para garantir consistência
                if len(self.available_pages) + len(self.busy_pages) < self.min_size:
                    new_page = await self._create_new_page()
                    if new_page:
                        self.available_pages.append(new_page)
                        print(f"🔄 Nova página criada para manter pool mínimo")
            else:
                # Retornar página para pool
                pooled_page.mark_available()
                self.available_pages.append(pooled_page)
                print(f"↩️ Página retornada ao pool (total disponível: {len(self.available_pages)})")
    
    async def _destroy_page(self, pooled_page: PooledPage) -> None:
        """
        Destroi uma página do pool
        """
        try:
            await pooled_page.page.close()
            self.stats['pages_destroyed'] += 1
            print(f"🗑️ Página removida do pool (errors: {pooled_page.errors_count}, age: {datetime.now() - pooled_page.created_at})")
        except Exception as e:
            print(f"⚠️ Erro ao fechar página: {e}")
    
    async def _cleanup_loop(self) -> None:
        """
        Loop de limpeza automática do pool
        """
        while not self.is_shutdown:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_pages()
                self.stats['cleanup_runs'] += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Erro na limpeza do pool: {e}")
    
    async def _cleanup_old_pages(self) -> None:
        """
        Remove páginas antigas ou com muitos erros
        """
        async with self._lock:
            pages_to_remove = []
            
            # Verificar páginas disponíveis
            for pooled_page in list(self.available_pages):
                if pooled_page.should_recreate(self.max_age_minutes):
                    pages_to_remove.append(pooled_page)
                    self.available_pages.remove(pooled_page)
            
            # Remover páginas identificadas
            for pooled_page in pages_to_remove:
                await self._destroy_page(pooled_page)
            
            # Criar novas páginas se necessário
            while len(self.available_pages) < self.min_size and not self.is_shutdown:
                new_page = await self._create_new_page()
                if new_page:
                    self.available_pages.append(new_page)
                else:
                    break
            
            if pages_to_remove:
                print(f"🧹 Limpeza: {len(pages_to_remove)} páginas antigas removidas")
    
    async def shutdown(self) -> None:
        """
        Finaliza pool e limpa recursos
        """
        if self.is_shutdown:
            return
        
        self.is_shutdown = True
        
        # Cancelar task de limpeza
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Fechar todas as páginas
        async with self._lock:
            all_pages = list(self.available_pages) + self.busy_pages
            
            for pooled_page in all_pages:
                await self._destroy_page(pooled_page)
            
            self.available_pages.clear()
            self.busy_pages.clear()
        
        print(f"🔌 Pool de conexões finalizado")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do pool
        """
        return {
            **self.stats,
            'pool_size': len(self.available_pages) + len(self.busy_pages),
            'available_pages': len(self.available_pages),
            'busy_pages': len(self.busy_pages),
            'cache_hit_rate': (self.stats['cache_hits'] / max(1, self.stats['total_requests'])) * 100,
            'is_initialized': self.is_initialized,
            'is_shutdown': self.is_shutdown
        }
    
    def print_stats(self) -> None:
        """
        Exibe estatísticas do pool
        """
        stats = self.get_stats()
        
        print("\n📊 ESTATÍSTICAS DO POOL DE CONEXÕES")
        print("=" * 50)
        print(f"🔄 Páginas no pool: {stats['pool_size']}")
        print(f"   • Disponíveis: {stats['available_pages']}")
        print(f"   • Em uso: {stats['busy_pages']}")
        print(f"📈 Requisições totais: {stats['total_requests']}")
        print(f"🎯 Taxa de cache hit: {stats['cache_hit_rate']:.1f}%")
        print(f"⏱️ Tempo médio de espera: {stats['average_wait_time']:.3f}s")
        print(f"🆕 Páginas criadas: {stats['pages_created']}")
        print(f"🗑️ Páginas destruídas: {stats['pages_destroyed']}")
        print(f"❌ Erros: {stats['errors']}")
        print(f"🧹 Limpezas executadas: {stats['cleanup_runs']}")
        print("=" * 50)


# Instância global do pool
connection_pool = ConnectionPool()


async def get_pooled_page(timeout_seconds: float = 10.0) -> Optional[Page]:
    """
    Função utilitária para obter página do pool global
    """
    return await connection_pool.get_page(timeout_seconds)


async def return_pooled_page(page: Page, had_error: bool = False) -> None:
    """
    Função utilitária para retornar página ao pool global
    """
    await connection_pool.return_page(page, had_error)