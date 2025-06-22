"""
LRU Cache com TTL para otimização de performance
===============================================

Cache LRU (Least Recently Used) com Time-To-Live para evitar memory leaks
e garantir que dados não fiquem obsoletos.
"""

import time
import threading
from collections import OrderedDict
from typing import Any, Optional, Dict, Tuple, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """Entrada do cache com metadados"""
    value: Any
    timestamp: float
    access_count: int = 0
    last_access: float = None
    
    def __post_init__(self):
        if self.last_access is None:
            self.last_access = self.timestamp


class LRUCacheWithTTL:
    """
    Cache LRU com TTL (Time-To-Live) thread-safe
    
    Funcionalidades:
    - LRU eviction quando cache está cheio
    - TTL automático para evitar dados obsoletos
    - Thread-safe para uso em ambiente assíncrono
    - Estatísticas detalhadas
    - Limpeza automática em background
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Inicializa cache LRU com TTL
        
        Args:
            max_size: Número máximo de entradas no cache
            ttl_seconds: Tempo de vida das entradas em segundos
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()  # Permite re-entrada
        
        # Estatísticas
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expires': 0,
            'sets': 0,
            'deletes': 0,
            'cleanups': 0,
            'total_access_time': 0.0
        }
        
        # Configurações de limpeza automática
        self._last_cleanup = time.time()
        self._cleanup_interval = min(300, ttl_seconds // 2)  # Limpar a cada 5min ou metade do TTL
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor se encontrado e não expirado, None caso contrário
        """
        start_time = time.time()
        
        with self._lock:
            # Verificar se é hora de fazer limpeza
            self._maybe_cleanup()
            
            if key in self._cache:
                entry = self._cache[key]
                current_time = time.time()
                
                # Verificar se entrada expirou
                if current_time - entry.timestamp > self.ttl_seconds:
                    del self._cache[key]
                    self._stats['expires'] += 1
                    self._stats['misses'] += 1
                    return None
                
                # Mover para o final (mais recente)
                self._cache.move_to_end(key)
                
                # Atualizar metadados
                entry.access_count += 1
                entry.last_access = current_time
                
                # Estatísticas
                self._stats['hits'] += 1
                self._stats['total_access_time'] += time.time() - start_time
                
                return entry.value
            else:
                self._stats['misses'] += 1
                return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Define valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
        """
        with self._lock:
            current_time = time.time()
            
            # Se chave já existe, atualizar
            if key in self._cache:
                entry = self._cache[key]
                entry.value = value
                entry.timestamp = current_time
                entry.last_access = current_time
                self._cache.move_to_end(key)
            else:
                # Nova entrada
                entry = CacheEntry(
                    value=value,
                    timestamp=current_time,
                    last_access=current_time
                )
                self._cache[key] = entry
                
                # Se cache está cheio, remover o mais antigo
                if len(self._cache) > self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._stats['evictions'] += 1
            
            self._stats['sets'] += 1
    
    def delete(self, key: str) -> bool:
        """
        Remove entrada do cache
        
        Args:
            key: Chave a ser removida
            
        Returns:
            True se removida, False se não encontrada
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats['deletes'] += 1
                return True
            return False
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            self._stats['deletes'] += cleared_count
    
    def _maybe_cleanup(self) -> None:
        """
        Executa limpeza se necessário (chamado internamente)
        """
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = current_time
    
    def _cleanup_expired(self) -> None:
        """
        Remove entradas expiradas (assumindo que já tem lock)
        """
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time - entry.timestamp > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['expires'] += 1
        
        if expired_keys:
            self._stats['cleanups'] += 1
    
    def cleanup(self) -> int:
        """
        Força limpeza de entradas expiradas
        
        Returns:
            Número de entradas removidas
        """
        with self._lock:
            initial_size = len(self._cache)
            self._cleanup_expired()
            removed = initial_size - len(self._cache)
            
            if removed > 0:
                self._stats['cleanups'] += 1
            
            return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / max(1, total_requests)) * 100
            avg_access_time = self._stats['total_access_time'] / max(1, self._stats['hits'])
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': round(hit_rate, 2),
                'avg_access_time_ms': round(avg_access_time * 1000, 3),
                'ttl_seconds': self.ttl_seconds,
                'usage_percent': round((len(self._cache) / self.max_size) * 100, 1),
                **self._stats
            }
    
    def print_stats(self) -> None:
        """Imprime estatísticas formatadas"""
        stats = self.get_stats()
        
        print("\n📊 ESTATÍSTICAS DO CACHE LRU")
        print("=" * 40)
        print(f"📦 Tamanho: {stats['size']}/{stats['max_size']} ({stats['usage_percent']}%)")
        print(f"🎯 Taxa de hit: {stats['hit_rate']}%")
        print(f"⏱️ Tempo médio de acesso: {stats['avg_access_time_ms']}ms")
        print(f"⏰ TTL: {stats['ttl_seconds']}s")
        print(f"✅ Hits: {stats['hits']}")
        print(f"❌ Misses: {stats['misses']}")
        print(f"🗑️ Evictions: {stats['evictions']}")
        print(f"⌛ Expires: {stats['expires']}")
        print(f"📝 Sets: {stats['sets']}")
        print(f"🧹 Cleanups: {stats['cleanups']}")
        print("=" * 40)
    
    def __contains__(self, key: str) -> bool:
        """Verifica se chave existe (sem afetar LRU)"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                current_time = time.time()
                
                # Verificar se expirado
                if current_time - entry.timestamp > self.ttl_seconds:
                    del self._cache[key]
                    self._stats['expires'] += 1
                    return False
                
                return True
            return False
    
    def __len__(self) -> int:
        """Retorna tamanho atual do cache"""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> List[str]:
        """Retorna todas as chaves válidas (não expiradas)"""
        with self._lock:
            self._cleanup_expired()
            return list(self._cache.keys())
    
    def get_most_accessed(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Retorna entradas mais acessadas
        
        Args:
            limit: Número máximo de entradas a retornar
            
        Returns:
            Lista de (chave, access_count) ordenada por acesso
        """
        with self._lock:
            entries = [
                (key, entry.access_count) 
                for key, entry in self._cache.items()
            ]
            entries.sort(key=lambda x: x[1], reverse=True)
            return entries[:limit]
    
    def get_memory_usage_estimate(self) -> Dict[str, int]:
        """
        Estima uso de memória do cache
        
        Returns:
            Dicionário com estimativas em bytes
        """
        import sys
        
        with self._lock:
            total_size = 0
            key_size = 0
            value_size = 0
            metadata_size = 0
            
            for key, entry in self._cache.items():
                key_size += sys.getsizeof(key)
                value_size += sys.getsizeof(entry.value)
                metadata_size += sys.getsizeof(entry)
            
            total_size = key_size + value_size + metadata_size
            
            return {
                'total_bytes': total_size,
                'keys_bytes': key_size,
                'values_bytes': value_size,
                'metadata_bytes': metadata_size,
                'total_mb': round(total_size / (1024 * 1024), 2)
            }


class CVJobMatcherCache:
    """
    Cache especializado para o CV Job Matcher
    """
    
    def __init__(self):
        # Cache para CVs processados (TTL maior - 1 hora)
        self.cv_cache = LRUCacheWithTTL(max_size=100, ttl_seconds=3600)
        
        # Cache para jobs processados (TTL menor - 30 min)
        self.job_cache = LRUCacheWithTTL(max_size=1000, ttl_seconds=1800)
        
        # Cache para resultados de matching (TTL médio - 15 min)
        self.match_cache = LRUCacheWithTTL(max_size=500, ttl_seconds=900)
    
    def get_cv(self, cv_id: str) -> Optional[Any]:
        """Obtém CV processado do cache"""
        return self.cv_cache.get(cv_id)
    
    def set_cv(self, cv_id: str, processed_cv: Any) -> None:
        """Armazena CV processado no cache"""
        self.cv_cache.set(cv_id, processed_cv)
    
    def get_job(self, job_id: str) -> Optional[Any]:
        """Obtém job processado do cache"""
        return self.job_cache.get(job_id)
    
    def set_job(self, job_id: str, processed_job: Any) -> None:
        """Armazena job processado no cache"""
        self.job_cache.set(job_id, processed_job)
    
    def get_match(self, match_key: str) -> Optional[Any]:
        """Obtém resultado de matching do cache"""
        return self.match_cache.get(match_key)
    
    def set_match(self, match_key: str, match_result: Any) -> None:
        """Armazena resultado de matching no cache"""
        self.match_cache.set(match_key, match_result)
    
    def clear_all(self) -> None:
        """Limpa todos os caches"""
        self.cv_cache.clear()
        self.job_cache.clear()
        self.match_cache.clear()
    
    def cleanup_all(self) -> Dict[str, int]:
        """Executa limpeza em todos os caches"""
        return {
            'cv_removed': self.cv_cache.cleanup(),
            'job_removed': self.job_cache.cleanup(),
            'match_removed': self.match_cache.cleanup()
        }
    
    def get_combined_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas combinadas de todos os caches"""
        cv_stats = self.cv_cache.get_stats()
        job_stats = self.job_cache.get_stats()
        match_stats = self.match_cache.get_stats()
        
        return {
            'cv_cache': cv_stats,
            'job_cache': job_stats,
            'match_cache': match_stats,
            'total_size': cv_stats['size'] + job_stats['size'] + match_stats['size'],
            'total_hits': cv_stats['hits'] + job_stats['hits'] + match_stats['hits'],
            'total_misses': cv_stats['misses'] + job_stats['misses'] + match_stats['misses'],
            'overall_hit_rate': round(
                ((cv_stats['hits'] + job_stats['hits'] + match_stats['hits']) / 
                 max(1, cv_stats['hits'] + job_stats['hits'] + match_stats['hits'] + 
                     cv_stats['misses'] + job_stats['misses'] + match_stats['misses'])) * 100, 2
            )
        }
    
    def print_combined_stats(self) -> None:
        """Imprime estatísticas combinadas formatadas"""
        stats = self.get_combined_stats()
        
        print("\n📊 ESTATÍSTICAS COMBINADAS DOS CACHES")
        print("=" * 50)
        print(f"📦 Total de entradas: {stats['total_size']}")
        print(f"🎯 Taxa de hit geral: {stats['overall_hit_rate']}%")
        print(f"✅ Total de hits: {stats['total_hits']}")
        print(f"❌ Total de misses: {stats['total_misses']}")
        print()
        
        print("📋 CV Cache:")
        print(f"   Tamanho: {stats['cv_cache']['size']}/{stats['cv_cache']['max_size']}")
        print(f"   Hit rate: {stats['cv_cache']['hit_rate']}%")
        
        print("💼 Job Cache:")
        print(f"   Tamanho: {stats['job_cache']['size']}/{stats['job_cache']['max_size']}")
        print(f"   Hit rate: {stats['job_cache']['hit_rate']}%")
        
        print("🔍 Match Cache:")
        print(f"   Tamanho: {stats['match_cache']['size']}/{stats['match_cache']['max_size']}")
        print(f"   Hit rate: {stats['match_cache']['hit_rate']}%")
        print("=" * 50)