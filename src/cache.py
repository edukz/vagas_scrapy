import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional


class CacheEntry:
    """
    Entrada do cache com metadados
    """
    def __init__(self, data: Dict, timestamp: datetime, url: str, hash_key: str):
        self.data = data
        self.timestamp = timestamp
        self.url = url
        self.hash_key = hash_key
    
    def is_expired(self, max_age_hours: int = 6) -> bool:
        """Verifica se o cache expirou"""
        return datetime.now() - self.timestamp > timedelta(hours=max_age_hours)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário serializável"""
        return {
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'url': self.url,
            'hash_key': self.hash_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """Cria instância a partir de dicionário"""
        return cls(
            data=data['data'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            url=data['url'],
            hash_key=data['hash_key']
        )


class IntelligentCache:
    """
    Sistema de cache inteligente para URLs e dados de vagas
    """
    def __init__(self, cache_dir: str = "data/cache", max_age_hours: int = 6):
        self.cache_dir = cache_dir
        self.max_age_hours = max_age_hours
        self.memory_cache = {}
        
        # Criar diretório de cache
        os.makedirs(cache_dir, exist_ok=True)
        
        # Limpar cache expirado na inicialização (síncronamente)
        self._cleanup_expired_cache_sync()
    
    def _get_cache_key(self, url: str) -> str:
        """Gera chave única para URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Gera caminho do arquivo de cache"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    async def get(self, url: str) -> Optional[Dict]:
        """
        Recupera dados do cache se válidos
        """
        cache_key = self._get_cache_key(url)
        
        # Verificar cache em memória primeiro
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if not entry.is_expired(self.max_age_hours):
                print(f"✓ Cache hit (memória): {url[:50]}...")
                return entry.data
            else:
                del self.memory_cache[cache_key]
        
        # Verificar cache em disco
        cache_file = self._get_cache_file_path(cache_key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                entry = CacheEntry.from_dict(cache_data)
                
                if not entry.is_expired(self.max_age_hours):
                    # Carregar de volta para memória
                    self.memory_cache[cache_key] = entry
                    print(f"✓ Cache hit (disco): {url[:50]}...")
                    return entry.data
                else:
                    # Cache expirado, remover arquivo
                    os.remove(cache_file)
            except Exception as e:
                print(f"⚠ Erro ao ler cache: {e}")
        
        return None
    
    async def set(self, url: str, data: Dict) -> None:
        """
        Armazena dados no cache
        """
        cache_key = self._get_cache_key(url)
        entry = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            url=url,
            hash_key=cache_key
        )
        
        # Armazenar em memória
        self.memory_cache[cache_key] = entry
        
        # Armazenar em disco
        cache_file = self._get_cache_file_path(cache_key)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"✓ Cache salvo: {url[:50]}...")
        except Exception as e:
            print(f"⚠ Erro ao salvar cache: {e}")
    
    async def _cleanup_expired_cache(self) -> None:
        """
        Remove entradas de cache expiradas
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        entry = CacheEntry.from_dict(cache_data)
                        if entry.is_expired(self.max_age_hours):
                            os.remove(cache_file)
                            print(f"🗑️ Cache expirado removido: {filename}")
                    except:
                        # Se houver erro ao ler, remover arquivo corrompido
                        os.remove(cache_file)
        except Exception as e:
            print(f"⚠ Erro na limpeza do cache: {e}")
    
    def _cleanup_expired_cache_sync(self) -> None:
        """
        Remove entradas de cache expiradas (versão síncrona)
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        entry = CacheEntry.from_dict(cache_data)
                        if entry.is_expired(self.max_age_hours):
                            os.remove(cache_file)
                    except:
                        # Se houver erro ao ler, remover arquivo corrompido
                        os.remove(cache_file)
        except Exception as e:
            pass  # Silencioso na inicialização