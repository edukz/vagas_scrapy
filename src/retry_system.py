"""
Sistema de Retry Inteligente para Web Scraping

Este módulo implementa um sistema robusto de retry com:
- Retry exponencial com jitter
- Detecção inteligente de tipos de erro
- Métricas de tentativas
- Logs detalhados
"""

import asyncio
import random
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum


class RetryReason(Enum):
    """Razões para retry"""
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMITED = "rate_limited"
    SERVER_ERROR = "server_error"
    ELEMENT_NOT_FOUND = "element_not_found"
    BROWSER_ERROR = "browser_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryAttempt:
    """Informações sobre uma tentativa de retry"""
    attempt: int
    exception: Exception
    reason: RetryReason
    delay: float
    timestamp: float


@dataclass
class RetryResult:
    """Resultado de uma operação com retry"""
    success: bool
    result: Any = None
    attempts: List[RetryAttempt] = None
    total_time: float = 0.0
    final_exception: Optional[Exception] = None


class RetryStrategy:
    """
    Estratégia de retry configurável
    """
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_backoff: bool = True,
        jitter: bool = True,
        jitter_factor: float = 0.1
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff
        self.jitter = jitter
        self.jitter_factor = jitter_factor
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcula o delay para uma tentativa específica"""
        if self.exponential_backoff:
            delay = self.base_delay * (2 ** (attempt - 1))
        else:
            delay = self.base_delay
        
        # Aplicar limite máximo
        delay = min(delay, self.max_delay)
        
        # Adicionar jitter para evitar thundering herd
        if self.jitter:
            jitter_amount = delay * self.jitter_factor
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


class RetryableException:
    """
    Classificador de exceções para determinar se devem ser retryadas
    """
    
    # Mapeamento de exceções para razões de retry
    EXCEPTION_MAPPING = {
        # Erros de rede
        'ConnectionError': RetryReason.NETWORK_ERROR,
        'TimeoutError': RetryReason.TIMEOUT_ERROR,
        'asyncio.TimeoutError': RetryReason.TIMEOUT_ERROR,
        'aiohttp.ClientTimeout': RetryReason.TIMEOUT_ERROR,
        
        # Erros do Playwright
        'playwright._impl._errors.TimeoutError': RetryReason.TIMEOUT_ERROR,
        'playwright._impl._errors.Error': RetryReason.BROWSER_ERROR,
        
        # Erros HTTP
        'aiohttp.ClientResponseError': RetryReason.SERVER_ERROR,
        'requests.exceptions.RequestException': RetryReason.NETWORK_ERROR,
        
        # Erros específicos do scraping
        'ElementNotFoundError': RetryReason.ELEMENT_NOT_FOUND,
    }
    
    # Códigos HTTP que devem ser retryados
    RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}
    
    @classmethod
    def should_retry(cls, exception: Exception) -> bool:
        """Determina se uma exceção deve ser retryada"""
        exception_name = exception.__class__.__name__
        full_exception_name = f"{exception.__class__.__module__}.{exception_name}"
        
        # Verificar mapeamento direto
        if exception_name in cls.EXCEPTION_MAPPING:
            return True
        if full_exception_name in cls.EXCEPTION_MAPPING:
            return True
        
        # Verificar códigos HTTP específicos
        if hasattr(exception, 'status') and exception.status in cls.RETRYABLE_HTTP_CODES:
            return True
        
        # Verificar mensagens específicas
        error_message = str(exception).lower()
        retryable_messages = [
            'timeout', 'connection', 'network', 'temporary',
            'rate limit', 'too many requests', 'server error'
        ]
        
        return any(msg in error_message for msg in retryable_messages)
    
    @classmethod
    def get_retry_reason(cls, exception: Exception) -> RetryReason:
        """Determina a razão do retry baseada na exceção"""
        exception_name = exception.__class__.__name__
        full_exception_name = f"{exception.__class__.__module__}.{exception_name}"
        
        # Verificar mapeamento direto
        if exception_name in cls.EXCEPTION_MAPPING:
            return cls.EXCEPTION_MAPPING[exception_name]
        if full_exception_name in cls.EXCEPTION_MAPPING:
            return cls.EXCEPTION_MAPPING[full_exception_name]
        
        # Verificar códigos HTTP
        if hasattr(exception, 'status'):
            if exception.status == 429:
                return RetryReason.RATE_LIMITED
            elif exception.status >= 500:
                return RetryReason.SERVER_ERROR
        
        # Análise por mensagem
        error_message = str(exception).lower()
        if 'timeout' in error_message:
            return RetryReason.TIMEOUT_ERROR
        elif 'connection' in error_message or 'network' in error_message:
            return RetryReason.NETWORK_ERROR
        elif 'rate limit' in error_message or 'too many requests' in error_message:
            return RetryReason.RATE_LIMITED
        
        return RetryReason.UNKNOWN_ERROR


class RetrySystem:
    """
    Sistema principal de retry
    """
    
    def __init__(self, default_strategy: Optional[RetryStrategy] = None):
        self.default_strategy = default_strategy or RetryStrategy()
        self.metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_retries': 0,
            'retry_reasons': {}
        }
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        strategy: Optional[RetryStrategy] = None,
        operation_name: str = "unknown_operation",
        **kwargs
    ) -> RetryResult:
        """
        Executa uma operação com retry automático
        """
        strategy = strategy or self.default_strategy
        attempts = []
        start_time = time.time()
        
        self.metrics['total_operations'] += 1
        
        for attempt in range(1, strategy.max_attempts + 1):
            try:
                print(f"🔄 [{operation_name}] Tentativa {attempt}/{strategy.max_attempts}")
                
                # Executar a operação
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                # Sucesso!
                total_time = time.time() - start_time
                self.metrics['successful_operations'] += 1
                
                if attempts:  # Houve retries anteriores
                    self.metrics['total_retries'] += len(attempts)
                    print(f"✅ [{operation_name}] Sucesso após {attempt} tentativas em {total_time:.2f}s")
                else:
                    print(f"✅ [{operation_name}] Sucesso na primeira tentativa")
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_time=total_time
                )
                
            except Exception as e:
                # Verificar se deve fazer retry
                should_retry = RetryableException.should_retry(e)
                retry_reason = RetryableException.get_retry_reason(e)
                
                # Atualizar métricas de razões
                reason_key = retry_reason.value
                self.metrics['retry_reasons'][reason_key] = self.metrics['retry_reasons'].get(reason_key, 0) + 1
                
                if not should_retry or attempt >= strategy.max_attempts:
                    # Não deve retry ou esgotou tentativas
                    total_time = time.time() - start_time
                    self.metrics['failed_operations'] += 1
                    self.metrics['total_retries'] += len(attempts)
                    
                    print(f"❌ [{operation_name}] Falha final após {attempt} tentativas: {e}")
                    
                    return RetryResult(
                        success=False,
                        attempts=attempts,
                        total_time=total_time,
                        final_exception=e
                    )
                
                # Calcular delay e registrar tentativa
                delay = strategy.calculate_delay(attempt)
                
                attempt_info = RetryAttempt(
                    attempt=attempt,
                    exception=e,
                    reason=retry_reason,
                    delay=delay,
                    timestamp=time.time()
                )
                attempts.append(attempt_info)
                
                print(f"⚠️ [{operation_name}] Tentativa {attempt} falhou ({retry_reason.value}): {e}")
                
                if attempt < strategy.max_attempts:
                    print(f"⏳ Aguardando {delay:.2f}s antes da próxima tentativa...")
                    await asyncio.sleep(delay)
    
    def get_metrics(self) -> Dict:
        """Retorna métricas do sistema de retry"""
        if self.metrics['total_operations'] > 0:
            success_rate = (self.metrics['successful_operations'] / self.metrics['total_operations']) * 100
            avg_retries = self.metrics['total_retries'] / self.metrics['total_operations']
        else:
            success_rate = 0
            avg_retries = 0
        
        return {
            **self.metrics,
            'success_rate': f"{success_rate:.1f}%",
            'average_retries_per_operation': f"{avg_retries:.2f}"
        }
    
    def print_metrics(self):
        """Imprime métricas formatadas"""
        metrics = self.get_metrics()
        
        print(f"\n📊 MÉTRICAS DO SISTEMA DE RETRY:")
        print(f"   📈 Operações totais: {metrics['total_operations']}")
        print(f"   ✅ Operações bem-sucedidas: {metrics['successful_operations']}")
        print(f"   ❌ Operações falharam: {metrics['failed_operations']}")
        print(f"   🔄 Total de retries: {metrics['total_retries']}")
        print(f"   📊 Taxa de sucesso: {metrics['success_rate']}")
        print(f"   📊 Média de retries: {metrics['average_retries_per_operation']}")
        
        if metrics['retry_reasons']:
            print(f"   📋 Razões de retry:")
            for reason, count in metrics['retry_reasons'].items():
                print(f"      - {reason}: {count}")


# Estratégias pré-configuradas
STRATEGIES = {
    'conservative': RetryStrategy(max_attempts=2, base_delay=2.0, max_delay=10.0),
    'standard': RetryStrategy(max_attempts=3, base_delay=1.0, max_delay=30.0),
    'aggressive': RetryStrategy(max_attempts=5, base_delay=0.5, max_delay=60.0),
    'network_heavy': RetryStrategy(max_attempts=4, base_delay=2.0, max_delay=120.0),
}


# Decorador para facilitar uso
def retry_on_failure(
    strategy_name: str = 'standard',
    operation_name: Optional[str] = None
):
    """
    Decorador para aplicar retry automático a funções
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retry_system = RetrySystem()
            strategy = STRATEGIES.get(strategy_name, STRATEGIES['standard'])
            op_name = operation_name or func.__name__
            
            result = await retry_system.execute_with_retry(
                func, *args, strategy=strategy, operation_name=op_name, **kwargs
            )
            
            if result.success:
                return result.result
            else:
                raise result.final_exception
        
        return wrapper
    return decorator