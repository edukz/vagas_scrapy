"""
Sistema de Logs Estruturado

Este módulo implementa um sistema robusto de logging estruturado em JSON
para facilitar monitoramento, debugging e análise de performance.

Funcionalidades:
- Logs em formato JSON estruturado
- Níveis de severidade (DEBUG, INFO, WARN, ERROR, CRITICAL)
- Rotação automática de arquivos
- Correlação de operações com trace IDs
- Context management para dados específicos
- Performance tracking integrado
"""

import json
import logging
import logging.handlers
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager
import threading
from pathlib import Path


class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Component(Enum):
    """Componentes do sistema"""
    SCRAPER = "scraper"
    RETRY_SYSTEM = "retry_system"
    FALLBACK_SELECTOR = "fallback_selector"
    DATA_VALIDATOR = "data_validator"
    CACHE = "cache"
    RATE_LIMITER = "rate_limiter"
    NAVIGATOR = "navigator"
    MAIN = "main"
    SYSTEM = "system"


@dataclass
class LogEntry:
    """Estrutura de uma entrada de log"""
    timestamp: str
    level: str
    component: str
    message: str
    operation: Optional[str] = None
    trace_id: Optional[str] = None
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class StructuredFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON"""
    
    def format(self, record):
        """Formata o record em JSON estruturado"""
        # Extrair dados estruturados do record
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'component': getattr(record, 'component', 'unknown'),
            'message': record.getMessage(),
        }
        
        # Adicionar campos opcionais se existirem
        optional_fields = [
            'operation', 'trace_id', 'duration_ms', 'success', 
            'error', 'context', 'metadata', 'url', 'attempt',
            'retry_reason', 'validation_score', 'anomaly_type'
        ]
        
        for field in optional_fields:
            if hasattr(record, field) and getattr(record, field) is not None:
                log_data[field] = getattr(record, field)
        
        # Adicionar informações de exceção se houver
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))


class TraceContext:
    """Context manager para correlação de operações"""
    
    def __init__(self):
        self._local = threading.local()
    
    def get_trace_id(self) -> Optional[str]:
        """Obtém o trace ID atual"""
        return getattr(self._local, 'trace_id', None)
    
    def set_trace_id(self, trace_id: str):
        """Define o trace ID atual"""
        self._local.trace_id = trace_id
    
    def clear_trace_id(self):
        """Limpa o trace ID atual"""
        if hasattr(self._local, 'trace_id'):
            delattr(self._local, 'trace_id')
    
    @contextmanager
    def trace(self, operation: str = None):
        """Context manager para criar um novo trace"""
        trace_id = str(uuid.uuid4())[:8]
        old_trace_id = self.get_trace_id()
        
        try:
            self.set_trace_id(trace_id)
            yield trace_id
        finally:
            if old_trace_id:
                self.set_trace_id(old_trace_id)
            else:
                self.clear_trace_id()


class PerformanceTracker:
    """Tracker de performance para operações"""
    
    def __init__(self, logger: 'StructuredLogger', component: Component, operation: str):
        self.logger = logger
        self.component = component
        self.operation = operation
        self.start_time = None
        self.context = {}
    
    def start(self, **context):
        """Inicia o tracking de performance"""
        self.start_time = time.time()
        self.context.update(context)
        
        self.logger.debug(
            f"Started operation: {self.operation}",
            component=self.component,
            operation=self.operation,
            context=self.context
        )
        
        return self
    
    def finish(self, success: bool = True, **additional_context):
        """Finaliza o tracking de performance"""
        if self.start_time is None:
            return
        
        duration_ms = (time.time() - self.start_time) * 1000
        final_context = {**self.context, **additional_context}
        
        level = LogLevel.INFO if success else LogLevel.WARN
        message = f"Completed operation: {self.operation}"
        
        self.logger.log(
            level,
            message,
            component=self.component,
            operation=self.operation,
            duration_ms=round(duration_ms, 2),
            success=success,
            context=final_context
        )
        
        return duration_ms
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        error_info = {}
        
        if exc_type:
            error_info['error'] = str(exc_val)
            error_info['error_type'] = exc_type.__name__
        
        self.finish(success=success, **error_info)


class StructuredLogger:
    """Logger principal com funcionalidades estruturadas"""
    
    def __init__(self, name: str = "scraper", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.trace_context = TraceContext()
        self._setup_logger()
    
    def _setup_logger(self):
        """Configura o logger com handlers apropriados"""
        # Criar diretório de logs
        self.log_dir.mkdir(exist_ok=True)
        
        # Configurar logger principal
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Limpar handlers existentes
        self.logger.handlers.clear()
        
        # Handler para arquivo principal (INFO+)
        main_file = self.log_dir / "scraper.log"
        main_handler = logging.handlers.RotatingFileHandler(
            main_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.INFO)
        main_handler.setFormatter(StructuredFormatter())
        
        # Handler para arquivo de debug (DEBUG+)
        debug_file = self.log_dir / "scraper_debug.log"
        debug_handler = logging.handlers.RotatingFileHandler(
            debug_file,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=3,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(StructuredFormatter())
        
        # Handler para arquivo de erros (ERROR+)
        error_file = self.log_dir / "scraper_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        
        # Handler para console (INFO+ em modo normal)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Apenas warnings+ no console
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(component)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Adicionar handlers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # Evitar propagação para o logger root
        self.logger.propagate = False
    
    def _create_log_record(self, level: LogLevel, message: str, **kwargs):
        """Cria um record de log com dados estruturados"""
        # Obter trace ID atual
        trace_id = self.trace_context.get_trace_id()
        
        # Criar record
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=getattr(logging, level.value),
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # Adicionar trace ID se disponível
        if trace_id:
            record.trace_id = trace_id
        
        # Adicionar campos customizados
        for key, value in kwargs.items():
            setattr(record, key, value)
        
        return record
    
    def log(self, level: LogLevel, message: str, component: Component = Component.SYSTEM, **kwargs):
        """Log genérico com nível especificado"""
        record = self._create_log_record(level, message, component=component.value, **kwargs)
        self.logger.handle(record)
    
    def debug(self, message: str, component: Component = Component.SYSTEM, **kwargs):
        """Log de debug"""
        self.log(LogLevel.DEBUG, message, component, **kwargs)
    
    def info(self, message: str, component: Component = Component.SYSTEM, **kwargs):
        """Log de informação"""
        self.log(LogLevel.INFO, message, component, **kwargs)
    
    def warn(self, message: str, component: Component = Component.SYSTEM, **kwargs):
        """Log de warning"""
        self.log(LogLevel.WARN, message, component, **kwargs)
    
    def error(self, message: str, component: Component = Component.SYSTEM, **kwargs):
        """Log de erro"""
        self.log(LogLevel.ERROR, message, component, **kwargs)
    
    def critical(self, message: str, component: Component = Component.SYSTEM, **kwargs):
        """Log crítico"""
        self.log(LogLevel.CRITICAL, message, component, **kwargs)
    
    def exception(self, message: str, component: Component = Component.SYSTEM, **kwargs):
        """Log de exceção com stack trace"""
        record = self._create_log_record(LogLevel.ERROR, message, component=component.value, **kwargs)
        record.exc_info = True
        self.logger.handle(record)
    
    # Métodos de conveniência para componentes específicos
    def retry_log(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Log específico do sistema de retry"""
        self.log(level, message, Component.RETRY_SYSTEM, **kwargs)
    
    def fallback_log(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Log específico do sistema de fallback"""
        self.log(level, message, Component.FALLBACK_SELECTOR, **kwargs)
    
    def validation_log(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Log específico do sistema de validação"""
        self.log(level, message, Component.DATA_VALIDATOR, **kwargs)
    
    def scraper_log(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Log específico do scraper"""
        self.log(level, message, Component.SCRAPER, **kwargs)
    
    def cache_log(self, message: str, level: LogLevel = LogLevel.INFO, **kwargs):
        """Log específico do cache"""
        self.log(level, message, Component.CACHE, **kwargs)
    
    # Context managers
    @contextmanager
    def trace_operation(self, operation: str, component: Component = Component.SYSTEM):
        """Context manager para traced operations"""
        with self.trace_context.trace(operation) as trace_id:
            self.debug(
                f"Starting traced operation: {operation}",
                component=component,
                operation=operation,
                trace_id=trace_id
            )
            try:
                yield trace_id
            except Exception as e:
                self.error(
                    f"Traced operation failed: {operation}",
                    component=component,
                    operation=operation,
                    error=str(e),
                    trace_id=trace_id
                )
                raise
            finally:
                self.debug(
                    f"Finished traced operation: {operation}",
                    component=component,
                    operation=operation,
                    trace_id=trace_id
                )
    
    def track_performance(self, component: Component, operation: str):
        """Cria um performance tracker"""
        return PerformanceTracker(self, component, operation)
    
    # Métodos utilitários
    def set_console_level(self, level: LogLevel):
        """Altera o nível de log do console"""
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(getattr(logging, level.value))
    
    def log_system_info(self):
        """Log informações do sistema"""
        import platform
        import sys
        
        self.info(
            "System information logged",
            component=Component.SYSTEM,
            metadata={
                'python_version': sys.version,
                'platform': platform.platform(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'log_directory': str(self.log_dir.absolute())
            }
        )
    
    def log_scraping_session_start(self, config: Dict[str, Any]):
        """Log início de sessão de scraping"""
        with self.trace_context.trace("scraping_session") as trace_id:
            self.info(
                "Scraping session started",
                component=Component.MAIN,
                operation="scraping_session",
                context=config,
                trace_id=trace_id
            )
            return trace_id
    
    def log_scraping_session_end(self, stats: Dict[str, Any]):
        """Log fim de sessão de scraping"""
        self.info(
            "Scraping session completed",
            component=Component.MAIN,
            operation="scraping_session",
            context=stats
        )
    
    def get_log_files(self):
        """Retorna lista de arquivos de log"""
        return {
            'main': self.log_dir / "scraper.log",
            'debug': self.log_dir / "scraper_debug.log",
            'errors': self.log_dir / "scraper_errors.log"
        }
    
    def get_log_stats(self):
        """Retorna estatísticas dos logs"""
        stats = {}
        
        for log_type, log_file in self.get_log_files().items():
            if log_file.exists():
                stats[log_type] = {
                    'size_mb': round(log_file.stat().st_size / (1024*1024), 2),
                    'lines': sum(1 for _ in open(log_file, 'r', encoding='utf-8')),
                    'last_modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                }
            else:
                stats[log_type] = {'exists': False}
        
        return stats


# Instância global do logger
structured_logger = StructuredLogger()


# Decorador para logging automático de funções
def log_function_call(component: Component = Component.SYSTEM, level: LogLevel = LogLevel.DEBUG):
    """Decorador para logging automático de chamadas de função"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            operation = f"{func.__module__}.{func.__name__}"
            
            with structured_logger.track_performance(component, operation) as tracker:
                structured_logger.log(
                    level,
                    f"Calling function: {func.__name__}",
                    component=component,
                    operation=operation,
                    context={'args_count': len(args), 'kwargs_count': len(kwargs)}
                )
                
                try:
                    result = func(*args, **kwargs)
                    structured_logger.log(
                        level,
                        f"Function completed: {func.__name__}",
                        component=component,
                        operation=operation,
                        success=True
                    )
                    return result
                except Exception as e:
                    structured_logger.error(
                        f"Function failed: {func.__name__}",
                        component=component,
                        operation=operation,
                        error=str(e),
                        success=False
                    )
                    raise
        
        return wrapper
    return decorator