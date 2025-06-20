"""
Sistema de Rate Limiting

Implementa limitação de taxa de requisições por IP
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
import time
import asyncio
from threading import Lock


class RateLimiter:
    """
    Rate limiter simples baseado em sliding window
    """
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        """
        Inicializa rate limiter
        
        Args:
            requests_per_minute: Requisições permitidas por minuto
            burst_size: Tamanho do burst (requisições rápidas)
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.window_size = 60  # segundos
        
        # Armazena timestamps das requisições por IP
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = Lock()
        
        # Estatísticas
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "unique_ips": set()
        }
    
    def check_rate_limit(self, identifier: str) -> bool:
        """
        Verifica se o identificador (IP) pode fazer requisição
        
        Args:
            identifier: Identificador único (geralmente IP)
            
        Returns:
            True se permitido, False se bloqueado
        """
        with self.lock:
            now = time.time()
            self.stats["total_requests"] += 1
            self.stats["unique_ips"].add(identifier)
            
            # Limpar requisições antigas
            self._cleanup_old_requests(identifier, now)
            
            # Verificar limite
            request_times = self.requests[identifier]
            
            # Verificar burst
            if len(request_times) >= self.burst_size:
                # Verificar se o burst mais antigo foi há menos de 1 segundo
                oldest_burst = request_times[-self.burst_size]
                if now - oldest_burst < 1.0:
                    self.stats["blocked_requests"] += 1
                    return False
            
            # Verificar limite por minuto
            if len(request_times) >= self.requests_per_minute:
                self.stats["blocked_requests"] += 1
                return False
            
            # Adicionar requisição atual
            request_times.append(now)
            return True
    
    def _cleanup_old_requests(self, identifier: str, current_time: float):
        """Remove requisições antigas da janela"""
        cutoff_time = current_time - self.window_size
        request_times = self.requests[identifier]
        
        # Remove requisições antigas
        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()
        
        # Remove entrada se não há mais requisições
        if not request_times and identifier in self.requests:
            del self.requests[identifier]
    
    def get_remaining_requests(self, identifier: str) -> Tuple[int, float]:
        """
        Retorna quantas requisições restam e quando resetará
        
        Returns:
            (requisições_restantes, segundos_até_reset)
        """
        with self.lock:
            now = time.time()
            self._cleanup_old_requests(identifier, now)
            
            request_times = self.requests.get(identifier, deque())
            remaining = self.requests_per_minute - len(request_times)
            
            # Calcular reset time
            if request_times:
                oldest_request = request_times[0]
                reset_in = max(0, self.window_size - (now - oldest_request))
            else:
                reset_in = 0
            
            return max(0, remaining), reset_in
    
    def get_current_rpm(self) -> float:
        """Retorna taxa atual de requisições por minuto (global)"""
        with self.lock:
            now = time.time()
            total_recent = 0
            
            for identifier, times in self.requests.items():
                self._cleanup_old_requests(identifier, now)
                total_recent += len(times)
            
            return total_recent
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do rate limiter"""
        with self.lock:
            return {
                "total_requests": self.stats["total_requests"],
                "blocked_requests": self.stats["blocked_requests"],
                "block_rate": (
                    self.stats["blocked_requests"] / max(1, self.stats["total_requests"])
                ) * 100,
                "unique_ips": len(self.stats["unique_ips"]),
                "current_rpm": self.get_current_rpm(),
                "config": {
                    "requests_per_minute": self.requests_per_minute,
                    "burst_size": self.burst_size
                }
            }
    
    def reset_stats(self):
        """Reseta estatísticas"""
        with self.lock:
            self.stats = {
                "total_requests": 0,
                "blocked_requests": 0,
                "unique_ips": set()
            }
    
    def reset_identifier(self, identifier: str):
        """Reseta limite para um identificador específico"""
        with self.lock:
            if identifier in self.requests:
                del self.requests[identifier]


class DistributedRateLimiter:
    """
    Rate limiter distribuído usando Redis (implementação futura)
    """
    
    def __init__(self, redis_client, requests_per_minute: int = 60):
        """
        Inicializa rate limiter distribuído
        
        Args:
            redis_client: Cliente Redis
            requests_per_minute: Requisições por minuto
        """
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.window_size = 60
    
    async def check_rate_limit(self, identifier: str) -> bool:
        """
        Verifica rate limit usando Redis
        
        Implementação usando sliding window com Redis sorted sets
        """
        # TODO: Implementar com Redis
        # key = f"rate_limit:{identifier}"
        # now = time.time()
        # cutoff = now - self.window_size
        
        # # Remove entradas antigas
        # await self.redis.zremrangebyscore(key, 0, cutoff)
        
        # # Conta requisições atuais
        # current_count = await self.redis.zcard(key)
        
        # if current_count >= self.requests_per_minute:
        #     return False
        
        # # Adiciona requisição atual
        # await self.redis.zadd(key, {str(now): now})
        # await self.redis.expire(key, self.window_size)
        
        # return True
        
        raise NotImplementedError("DistributedRateLimiter requer Redis")


# Helper decorators
def rate_limit(requests_per_minute: int = 60):
    """
    Decorator para aplicar rate limiting em funções
    
    Usage:
        @rate_limit(requests_per_minute=30)
        async def my_function():
            pass
    """
    limiter = RateLimiter(requests_per_minute=requests_per_minute)
    
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Tenta extrair identificador dos argumentos
            identifier = kwargs.get('client_ip', 'default')
            
            if not limiter.check_rate_limit(identifier):
                raise Exception(f"Rate limit exceeded for {identifier}")
            
            return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            # Tenta extrair identificador dos argumentos
            identifier = kwargs.get('client_ip', 'default')
            
            if not limiter.check_rate_limit(identifier):
                raise Exception(f"Rate limit exceeded for {identifier}")
            
            return func(*args, **kwargs)
        
        # Retorna wrapper apropriado
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator