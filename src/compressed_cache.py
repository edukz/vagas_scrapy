"""
Sistema de Cache Comprimido

Este módulo estende o cache inteligente adicionando compressão gzip
para reduzir o uso de disco em 60-80%.

Benefícios:
- 💾 Economia significativa de espaço
- 🚀 Leitura mais rápida para arquivos grandes
- 🔒 Compatibilidade total com o cache existente
"""

import json
import os
import gzip
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path

from .cache import CacheEntry, IntelligentCache
from .cache_index import CacheIndex


class CompressedCache(IntelligentCache):
    """
    Sistema de cache com compressão automática
    
    Reduz o tamanho dos arquivos de cache em 60-80% usando gzip,
    mantendo compatibilidade total com a interface existente.
    """
    
    def __init__(self, cache_dir: str = "data/cache", max_age_hours: int = 6, compression_level: int = 6):
        """
        Inicializa cache comprimido
        
        Args:
            cache_dir: Diretório para armazenar cache
            max_age_hours: Tempo de vida do cache em horas
            compression_level: Nível de compressão gzip (1-9, default 6)
        """
        self.compression_level = compression_level
        super().__init__(cache_dir, max_age_hours)
        
        # Sistema de índices para busca rápida
        self.index = CacheIndex(cache_dir)
        
        # Estatísticas de compressão
        self.compression_stats = {
            'total_saved_bytes': 0,
            'total_files_compressed': 0,
            'average_compression_ratio': 0.0
        }
        
        # Migrar cache existente para formato comprimido
        self._migrate_existing_cache()
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Gera caminho do arquivo de cache comprimido"""
        return os.path.join(self.cache_dir, f"{cache_key}.json.gz")
    
    def _get_legacy_cache_path(self, cache_key: str) -> str:
        """Gera caminho do arquivo de cache antigo (sem compressão)"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    async def get(self, url: str) -> Optional[Dict]:
        """
        Recupera dados do cache se válidos
        
        Tenta primeiro o formato comprimido, depois o formato legado
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
        
        # Verificar cache comprimido em disco
        cache_file = self._get_cache_file_path(cache_key)
        if os.path.exists(cache_file):
            try:
                # Ler e descomprimir
                with gzip.open(cache_file, 'rt', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                entry = CacheEntry.from_dict(cache_data)
                
                if not entry.is_expired(self.max_age_hours):
                    # Carregar de volta para memória
                    self.memory_cache[cache_key] = entry
                    print(f"✓ Cache hit (disco comprimido): {url[:50]}...")
                    return entry.data
                else:
                    # Cache expirado, remover arquivo
                    os.remove(cache_file)
            except Exception as e:
                print(f"⚠ Erro ao ler cache comprimido: {e}")
        
        # Verificar cache legado (não comprimido)
        legacy_file = self._get_legacy_cache_path(cache_key)
        if os.path.exists(legacy_file):
            try:
                with open(legacy_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                entry = CacheEntry.from_dict(cache_data)
                
                if not entry.is_expired(self.max_age_hours):
                    # Migrar para formato comprimido
                    await self.set(url, entry.data)
                    
                    # Remover arquivo legado
                    os.remove(legacy_file)
                    
                    print(f"✓ Cache hit (disco legado, migrado): {url[:50]}...")
                    return entry.data
                else:
                    # Cache expirado, remover arquivo
                    os.remove(legacy_file)
            except Exception as e:
                print(f"⚠ Erro ao ler cache legado: {e}")
        
        return None
    
    async def set(self, url: str, data: Dict) -> None:
        """
        Armazena dados no cache com compressão e indexação automática
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
        
        # Armazenar em disco com compressão
        cache_file = self._get_cache_file_path(cache_key)
        try:
            # Serializar para JSON
            json_str = json.dumps(entry.to_dict(), ensure_ascii=False, indent=2)
            json_bytes = json_str.encode('utf-8')
            
            # Comprimir e salvar
            with gzip.open(cache_file, 'wt', encoding='utf-8', compresslevel=self.compression_level) as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
            
            # Calcular estatísticas
            compressed_size = os.path.getsize(cache_file)
            original_size = len(json_bytes)
            saved_bytes = original_size - compressed_size
            compression_ratio = (saved_bytes / original_size) * 100
            
            # Atualizar estatísticas
            self.compression_stats['total_saved_bytes'] += saved_bytes
            self.compression_stats['total_files_compressed'] += 1
            self.compression_stats['average_compression_ratio'] = (
                (self.compression_stats['average_compression_ratio'] * 
                 (self.compression_stats['total_files_compressed'] - 1) + 
                 compression_ratio) / self.compression_stats['total_files_compressed']
            )
            
            # Indexar automaticamente se dados contêm jobs
            if 'jobs' in data and isinstance(data['jobs'], list):
                self.index.add_entry(
                    cache_key=cache_key,
                    file_path=cache_file,
                    url=url,
                    jobs_data=data['jobs'],
                    original_size=original_size,
                    compressed_size=compressed_size
                )
                print(f"✓ Cache salvo e indexado (comprimido {compression_ratio:.1f}%): {url[:50]}...")
            else:
                print(f"✓ Cache salvo (comprimido {compression_ratio:.1f}%): {url[:50]}...")
            
        except Exception as e:
            print(f"⚠ Erro ao salvar cache comprimido: {e}")
    
    def _migrate_existing_cache(self) -> None:
        """
        Migra arquivos de cache existentes para formato comprimido
        """
        migrated = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json') and not filename.endswith('.json.gz'):
                    legacy_file = os.path.join(self.cache_dir, filename)
                    
                    try:
                        # Ler arquivo antigo
                        with open(legacy_file, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        entry = CacheEntry.from_dict(cache_data)
                        
                        # Se não expirado, comprimir
                        if not entry.is_expired(self.max_age_hours):
                            cache_key = filename.replace('.json', '')
                            compressed_file = self._get_cache_file_path(cache_key)
                            
                            # Salvar comprimido
                            with gzip.open(compressed_file, 'wt', encoding='utf-8', 
                                         compresslevel=self.compression_level) as f:
                                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                            
                            migrated += 1
                        
                        # Remover arquivo antigo
                        os.remove(legacy_file)
                        
                    except Exception as e:
                        print(f"⚠ Erro ao migrar {filename}: {e}")
            
            if migrated > 0:
                print(f"✅ {migrated} arquivos de cache migrados para formato comprimido")
                
        except Exception as e:
            print(f"⚠ Erro na migração do cache: {e}")
    
    async def _cleanup_expired_cache(self) -> None:
        """
        Remove entradas de cache expiradas (comprimidas e legadas)
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json.gz') or (filename.endswith('.json') and not filename.endswith('.json.gz')):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        # Determinar se é comprimido ou não
                        if filename.endswith('.json.gz'):
                            with gzip.open(cache_file, 'rt', encoding='utf-8') as f:
                                cache_data = json.load(f)
                        else:
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
    
    def get_compression_stats(self) -> Dict:
        """
        Retorna estatísticas de compressão
        """
        stats = self.compression_stats.copy()
        
        # Adicionar estatísticas do diretório
        total_size = 0
        compressed_files = 0
        legacy_files = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if filename.endswith('.json.gz'):
                    compressed_files += 1
                    total_size += os.path.getsize(file_path)
                elif filename.endswith('.json'):
                    legacy_files += 1
                    total_size += os.path.getsize(file_path)
        except:
            pass
        
        stats.update({
            'total_cache_size_mb': total_size / (1024 * 1024),
            'compressed_files': compressed_files,
            'legacy_files': legacy_files,
            'estimated_savings_mb': stats['total_saved_bytes'] / (1024 * 1024)
        })
        
        return stats
    
    def search_cache(self, criteria: Dict) -> List:
        """
        Busca entries no cache usando critérios
        
        Args:
            criteria: Critérios de busca (ver CacheIndex.search)
            
        Returns:
            Lista de CacheIndexEntry que atendem aos critérios
        """
        return self.index.search(criteria)
    
    def get_cache_stats(self) -> Dict:
        """
        Retorna estatísticas combinadas do cache e índices
        """
        compression_stats = self.get_compression_stats()
        index_stats = self.index.get_stats()
        
        return {
            'compression': compression_stats,
            'index': index_stats
        }
    
    def get_top_companies(self, limit: int = 10) -> List:
        """
        Retorna empresas com mais vagas no cache
        """
        return self.index.get_top_companies(limit)
    
    def get_top_technologies(self, limit: int = 10) -> List:
        """
        Retorna tecnologias mais demandadas no cache
        """
        return self.index.get_top_technologies(limit)
    
    def get_recent_entries(self, days: int = 7) -> List:
        """
        Retorna entries dos últimos N dias
        """
        return self.index.get_entries_by_date_range(days)
    
    def rebuild_index(self) -> int:
        """
        Reconstrói o índice completo do cache
        """
        return self.index.rebuild_index(self.cache_dir)
    
    def print_compression_report(self) -> None:
        """
        Exibe relatório completo de compressão e índices
        """
        compression_stats = self.get_compression_stats()
        index_stats = self.index.get_stats()
        
        print("\n📊 RELATÓRIO DO CACHE COMPRIMIDO + ÍNDICES")
        print("=" * 60)
        
        # Estatísticas de compressão
        print("🗜️ COMPRESSÃO:")
        print(f"  📁 Arquivos comprimidos: {compression_stats['compressed_files']}")
        print(f"  📄 Arquivos legados: {compression_stats['legacy_files']}")
        print(f"  💾 Tamanho total: {compression_stats['total_cache_size_mb']:.2f} MB")
        print(f"  📈 Taxa média de compressão: {compression_stats['average_compression_ratio']:.1f}%")
        print(f"  💰 Economia: {compression_stats['estimated_savings_mb']:.2f} MB")
        
        # Estatísticas do índice
        print(f"\n🔍 ÍNDICES:")
        print(f"  📋 Entradas indexadas: {index_stats['total_entries']}")
        print(f"  💼 Total de vagas: {index_stats['total_jobs']}")
        print(f"  📅 Última atualização: {index_stats.get('last_updated', 'N/A')[:19]}")
        
        # Top empresas e tecnologias
        top_companies = self.get_top_companies(3)
        if top_companies:
            print(f"\n🏢 TOP EMPRESAS:")
            for company, count in top_companies:
                print(f"  • {company}: {count} vagas")
        
        top_techs = self.get_top_technologies(3)
        if top_techs:
            print(f"\n💻 TOP TECNOLOGIAS:")
            for tech, count in top_techs:
                print(f"  • {tech}: {count} vagas")
        
        print("=" * 60)