"""
Sistema Circuit Breaker para Web Scraping

Este módulo implementa o padrão Circuit Breaker para prevenir
sobrecarga do sistema e permitir recuperação automática.

Funcionalidades:
- Estados: CLOSED, OPEN, HALF_OPEN
- Detecção automática de falhas
- Tempo de recuperação configurável
- Métricas detalhadas
- Integração com sistema de logs
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

try:
    from .structured_logger import structured_logger, Component, LogLevel
    from .metrics_tracker import metrics_tracker
except ImportError:
    # Fallback se os módulos não estiverem disponíveis
    structured_logger = None
    Component = None
    LogLevel = None
    metrics_tracker = None

# Import para alertas (import tardio para evitar circular)
alert_system = None


class CircuitState(Enum):
    """Estados do Circuit Breaker"""
    CLOSED = "closed"      # Normal - permite todas as operações
    OPEN = "open"          # Falhou muito - bloqueia operações
    HALF_OPEN = "half_open"  # Testando recuperação


@dataclass
class CircuitBreakerConfig:
    """Configuração do Circuit Breaker"""
    failure_threshold: int = 5              # Número de falhas para abrir
    recovery_timeout: float = 60.0          # Tempo para tentar half-open (segundos)
    success_threshold: int = 3              # Sucessos em half-open para fechar
    request_volume_threshold: int = 10      # Mínimo de requests para avaliar
    error_percentage_threshold: float = 50.0  # % de erro para abrir
    sliding_window_size: int = 100          # Tamanho da janela deslizante
    
    # Timeouts específicos
    operation_timeout: float = 30.0         # Timeout por operação
    health_check_interval: float = 10.0     # Intervalo de health check


@dataclass
class OperationResult:
    """Resultado de uma operação"""
    success: bool
    timestamp: float
    duration: float
    error: Optional[Exception] = None
    operation_name: str = "unknown"


class CircuitBreakerError(Exception):
    """Exceção lançada quando circuit breaker está OPEN"""
    def __init__(self, message: str, state: CircuitState, failure_count: int):
        super().__init__(message)
        self.state = state
        self.failure_count = failure_count


class CircuitBreaker:
    """
    Implementação do padrão Circuit Breaker
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # Estado interno
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        
        # Janela deslizante de resultados
        self.results_window = deque(maxlen=self.config.sliding_window_size)
        
        # Métricas
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'circuit_opens': 0,
            'circuit_closes': 0,
            'rejected_requests': 0,
            'recovery_attempts': 0,
            'average_response_time': 0.0,
            'last_failure_time': None,
            'last_success_time': None,
            'state_transitions': []
        }
        
        # Lock para thread safety
        self._lock = asyncio.Lock()
    
    async def call(self, operation: Callable, *args, operation_name: str = None, **kwargs) -> Any:
        """
        Executa uma operação através do circuit breaker
        """
        async with self._lock:
            operation_name = operation_name or operation.__name__
            
            # Verificar estado atual
            await self._update_state()
            
            if self.state == CircuitState.OPEN:
                # Circuit aberto - rejeitar requisição
                self.metrics['rejected_requests'] += 1
                
                # Registrar métricas globais
                if metrics_tracker:
                    metrics_tracker.increment_counter("circuit_breaker.rejections")
                
                if structured_logger:
                    structured_logger.error(
                        f"Circuit breaker OPEN - rejecting operation: {operation_name}",
                        component=Component.RETRY_SYSTEM,
                        operation=operation_name,
                        context={
                            'circuit_name': self.name,
                            'state': self.state.value,
                            'failure_count': self.failure_count,
                            'time_until_retry': self._time_until_retry()
                        }
                    )
                
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Too many failures ({self.failure_count}). "
                    f"Retry in {self._time_until_retry():.1f}s",
                    self.state,
                    self.failure_count
                )
            
            # Executar operação
            start_time = time.time()
            
            try:
                self.metrics['total_requests'] += 1
                
                # Log tentativa
                if structured_logger:
                    structured_logger.info(
                        f"Executing operation through circuit breaker: {operation_name}",
                        component=Component.RETRY_SYSTEM,
                        operation=operation_name,
                        context={
                            'circuit_name': self.name,
                            'state': self.state.value,
                            'attempt_number': self.metrics['total_requests']
                        }
                    )
                
                # Aplicar timeout
                if asyncio.iscoroutinefunction(operation):
                    result = await asyncio.wait_for(
                        operation(*args, **kwargs),
                        timeout=self.config.operation_timeout
                    )
                else:
                    result = operation(*args, **kwargs)
                
                # Sucesso!
                duration = time.time() - start_time
                await self._on_success(operation_name, duration)
                
                return result
                
            except Exception as e:
                # Falha
                duration = time.time() - start_time
                await self._on_failure(operation_name, duration, e)
                raise
    
    async def _update_state(self):
        """Atualiza o estado do circuit breaker"""
        now = time.time()
        
        if self.state == CircuitState.OPEN:
            # Verificar se pode tentar half-open
            if now - self.last_failure_time >= self.config.recovery_timeout:
                await self._transition_to_half_open()
        
        elif self.state == CircuitState.HALF_OPEN:
            # Em half-open, avaliar se deve fechar baseado em sucessos
            if self.success_count >= self.config.success_threshold:
                await self._transition_to_closed()
    
    async def _on_success(self, operation_name: str, duration: float):
        """Processa um sucesso"""
        self.metrics['successful_requests'] += 1
        self.metrics['last_success_time'] = time.time()
        
        # Adicionar à janela de resultados
        result = OperationResult(
            success=True,
            timestamp=time.time(),
            duration=duration,
            operation_name=operation_name
        )
        self.results_window.append(result)
        
        # Atualizar média de tempo de resposta
        self._update_average_response_time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            if structured_logger:
                structured_logger.info(
                    f"Success in HALF_OPEN state: {operation_name}",
                    component=Component.RETRY_SYSTEM,
                    operation=operation_name,
                    context={
                        'circuit_name': self.name,
                        'success_count': self.success_count,
                        'threshold': self.config.success_threshold,
                        'duration_ms': duration * 1000
                    }
                )
                
            # Verificar se deve fechar
            if self.success_count >= self.config.success_threshold:
                await self._transition_to_closed()
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count em caso de sucesso
            self.failure_count = 0
    
    async def _on_failure(self, operation_name: str, duration: float, error: Exception):
        """Processa uma falha"""
        self.metrics['failed_requests'] += 1
        self.metrics['last_failure_time'] = time.time()
        self.last_failure_time = time.time()
        
        # Adicionar à janela de resultados
        result = OperationResult(
            success=False,
            timestamp=time.time(),
            duration=duration,
            error=error,
            operation_name=operation_name
        )
        self.results_window.append(result)
        
        # Atualizar média de tempo de resposta
        self._update_average_response_time()
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            
            # Verificar se deve abrir
            if await self._should_open_circuit():
                await self._transition_to_open()
        
        elif self.state == CircuitState.HALF_OPEN:
            # Qualquer falha em half-open volta para open
            await self._transition_to_open()
        
        # Log da falha
        if structured_logger:
            structured_logger.error(
                f"Operation failed in circuit breaker: {operation_name}",
                component=Component.RETRY_SYSTEM,
                operation=operation_name,
                error=str(error),
                context={
                    'circuit_name': self.name,
                    'state': self.state.value,
                    'failure_count': self.failure_count,
                    'duration_ms': duration * 1000
                }
            )
    
    async def _should_open_circuit(self) -> bool:
        """Determina se o circuit deve ser aberto"""
        # Critério 1: Número absoluto de falhas
        if self.failure_count >= self.config.failure_threshold:
            return True
        
        # Critério 2: Porcentagem de falhas na janela deslizante
        if len(self.results_window) >= self.config.request_volume_threshold:
            failed_results = [r for r in self.results_window if not r.success]
            error_rate = (len(failed_results) / len(self.results_window)) * 100
            
            if error_rate >= self.config.error_percentage_threshold:
                return True
        
        return False
    
    async def _transition_to_open(self):
        """Transição para estado OPEN"""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.metrics['circuit_opens'] += 1
        
        # Registrar métricas globais
        if metrics_tracker:
            metrics_tracker.increment_counter("circuit_breaker.opens")
            metrics_tracker.set_gauge("circuit_breaker.current_state", 1.0)  # OPEN = 1
        self.metrics['state_transitions'].append({
            'from': old_state.value,
            'to': self.state.value,
            'timestamp': time.time(),
            'failure_count': self.failure_count
        })
        
        if structured_logger:
            structured_logger.warn(
                f"Circuit breaker '{self.name}' opened due to failures",
                component=Component.RETRY_SYSTEM,
                context={
                    'circuit_name': self.name,
                    'failure_count': self.failure_count,
                    'recovery_timeout': self.config.recovery_timeout,
                    'error_rate': self._get_current_error_rate()
                }
            )
        
        print(f"🔴 Circuit Breaker '{self.name}' ABERTO - {self.failure_count} falhas detectadas")
        
        # Disparar alerta de circuit breaker aberto
        global alert_system
        if alert_system is None:
            try:
                from .alert_system import alert_system
            except ImportError:
                pass
        
        if alert_system:
            import asyncio
            asyncio.create_task(
                alert_system.trigger_alert(
                    rule_name="circuit_breaker_open",
                    title=f"Circuit Breaker '{self.name}' aberto",
                    description=f"Sistema sobrecarregado - {self.failure_count} falhas detectadas",
                    context={
                        'circuit_name': self.name,
                        'failure_count': self.failure_count,
                        'error_rate': self._get_current_error_rate(),
                        'config': {
                            'failure_threshold': self.config.failure_threshold,
                            'recovery_timeout': self.config.recovery_timeout
                        }
                    }
                )
            )
    
    async def _transition_to_half_open(self):
        """Transição para estado HALF_OPEN"""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.metrics['recovery_attempts'] += 1
        self.metrics['state_transitions'].append({
            'from': old_state.value,
            'to': self.state.value,
            'timestamp': time.time()
        })
        
        if structured_logger:
            structured_logger.info(
                f"Circuit breaker '{self.name}' transitioning to HALF_OPEN",
                component=Component.RETRY_SYSTEM,
                context={
                    'circuit_name': self.name,
                    'recovery_attempt': self.metrics['recovery_attempts']
                }
            )
        
        print(f"🟡 Circuit Breaker '{self.name}' MEIO-ABERTO - testando recuperação")
    
    async def _transition_to_closed(self):
        """Transição para estado CLOSED"""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.metrics['circuit_closes'] += 1
        
        # Registrar métricas globais
        if metrics_tracker:
            metrics_tracker.increment_counter("circuit_breaker.closes")
            metrics_tracker.set_gauge("circuit_breaker.current_state", 0.0)  # CLOSED = 0
        self.metrics['state_transitions'].append({
            'from': old_state.value,
            'to': self.state.value,
            'timestamp': time.time()
        })
        
        if structured_logger:
            structured_logger.info(
                f"Circuit breaker '{self.name}' closed - system recovered",
                component=Component.RETRY_SYSTEM,
                context={
                    'circuit_name': self.name,
                    'recovery_successful': True
                }
            )
        
        print(f"🟢 Circuit Breaker '{self.name}' FECHADO - sistema recuperado")
    
    def _time_until_retry(self) -> float:
        """Calcula tempo até próxima tentativa"""
        if self.state != CircuitState.OPEN:
            return 0.0
        
        elapsed = time.time() - self.last_failure_time
        return max(0, self.config.recovery_timeout - elapsed)
    
    def _get_current_error_rate(self) -> float:
        """Calcula taxa de erro atual"""
        if not self.results_window:
            return 0.0
        
        failed = sum(1 for r in self.results_window if not r.success)
        return (failed / len(self.results_window)) * 100
    
    def _update_average_response_time(self):
        """Atualiza tempo médio de resposta"""
        if not self.results_window:
            return
        
        durations = [r.duration for r in self.results_window]
        self.metrics['average_response_time'] = statistics.mean(durations)
    
    def get_metrics(self) -> Dict:
        """Retorna métricas do circuit breaker"""
        current_metrics = self.metrics.copy()
        current_metrics.update({
            'name': self.name,
            'current_state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'time_until_retry': self._time_until_retry(),
            'current_error_rate': f"{self._get_current_error_rate():.1f}%",
            'window_size': len(self.results_window),
            'config': {
                'failure_threshold': self.config.failure_threshold,
                'recovery_timeout': self.config.recovery_timeout,
                'success_threshold': self.config.success_threshold,
                'error_percentage_threshold': self.config.error_percentage_threshold
            }
        })
        
        return current_metrics
    
    def print_status(self):
        """Imprime status atual do circuit breaker"""
        metrics = self.get_metrics()
        
        state_icons = {
            'closed': '🟢',
            'open': '🔴',
            'half_open': '🟡'
        }
        
        icon = state_icons.get(self.state.value, '⚪')
        
        print(f"\n{icon} CIRCUIT BREAKER: {self.name}")
        print(f"   Estado: {self.state.value.upper()}")
        print(f"   Requisições: {metrics['total_requests']} (✅{metrics['successful_requests']} ❌{metrics['failed_requests']})")
        print(f"   Taxa de erro: {metrics['current_error_rate']}")
        print(f"   Tempo médio: {metrics['average_response_time']:.3f}s")
        
        if self.state == CircuitState.OPEN:
            print(f"   ⏳ Tentativa em: {metrics['time_until_retry']:.1f}s")
        elif self.state == CircuitState.HALF_OPEN:
            print(f"   🔄 Sucessos para fechar: {self.success_count}/{self.config.success_threshold}")
        
        if metrics['circuit_opens'] > 0:
            print(f"   📊 Aberturas: {metrics['circuit_opens']} | Fechamentos: {metrics['circuit_closes']}")


class CircuitBreakerManager:
    """Gerenciador de múltiplos Circuit Breakers"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.default_config = CircuitBreakerConfig()
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Obtém ou cria um circuit breaker"""
        if name not in self.circuit_breakers:
            circuit_config = config or self.default_config
            self.circuit_breakers[name] = CircuitBreaker(name, circuit_config)
        
        return self.circuit_breakers[name]
    
    async def execute_with_circuit_breaker(
        self,
        circuit_name: str,
        operation: Callable,
        *args,
        config: Optional[CircuitBreakerConfig] = None,
        operation_name: str = None,
        **kwargs
    ) -> Any:
        """Executa operação através de um circuit breaker específico"""
        circuit = self.get_circuit_breaker(circuit_name, config)
        return await circuit.call(operation, *args, operation_name=operation_name, **kwargs)
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """Retorna métricas de todos os circuit breakers"""
        return {name: cb.get_metrics() for name, cb in self.circuit_breakers.items()}
    
    def print_all_status(self):
        """Imprime status de todos os circuit breakers"""
        if not self.circuit_breakers:
            print("\n📋 Nenhum Circuit Breaker ativo")
            return
        
        print(f"\n📋 STATUS DOS CIRCUIT BREAKERS ({len(self.circuit_breakers)} ativos)")
        print("=" * 60)
        
        for cb in self.circuit_breakers.values():
            cb.print_status()
    
    async def health_check(self):
        """Executa health check em todos os circuit breakers"""
        if structured_logger:
            structured_logger.info(
                f"Running health check on {len(self.circuit_breakers)} circuit breakers",
                component=Component.RETRY_SYSTEM,
                context={'circuit_count': len(self.circuit_breakers)}
            )
        
        for name, cb in self.circuit_breakers.items():
            await cb._update_state()


# Instância global
circuit_breaker_manager = CircuitBreakerManager()


# Configurações predefinidas
CIRCUIT_CONFIGS = {
    'scraping': CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        success_threshold=2,
        error_percentage_threshold=60.0,
        operation_timeout=30.0
    ),
    'network': CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        success_threshold=3,
        error_percentage_threshold=50.0,
        operation_timeout=15.0
    ),
    'database': CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout=120.0,
        success_threshold=5,
        error_percentage_threshold=40.0,
        operation_timeout=10.0
    )
}


# Decorador para facilitar uso
def with_circuit_breaker(
    circuit_name: str,
    config_name: str = 'scraping',
    operation_name: Optional[str] = None
):
    """
    Decorador para aplicar circuit breaker a funções
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            config = CIRCUIT_CONFIGS.get(config_name, CIRCUIT_CONFIGS['scraping'])
            op_name = operation_name or func.__name__
            
            return await circuit_breaker_manager.execute_with_circuit_breaker(
                circuit_name, func, *args,
                config=config,
                operation_name=op_name,
                **kwargs
            )
        
        return wrapper
    return decorator