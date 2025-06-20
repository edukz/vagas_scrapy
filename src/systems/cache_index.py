"""
Sistema de Índices do Cache

Este módulo implementa um sistema de indexação para o cache comprimido,
permitindo busca e estatísticas instantâneas sem necessidade de abrir
arquivos individuais.

Funcionalidades:
- 🔍 Busca instantânea por critérios
- 📊 Estatísticas em tempo real
- 🗂️ Índices por data, empresa, tecnologia
- ⚡ Queries sem I/O de disco
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import threading
import hashlib


@dataclass
class CacheIndexEntry:
    """
    Entrada do índice do cache com metadados
    """
    cache_key: str
    file_path: str
    url: str
    timestamp: datetime
    file_size: int
    compressed_size: int
    compression_ratio: float
    
    # Metadados extraídos do conteúdo
    job_count: int = 0
    companies: List[str] = None
    technologies: List[str] = None
    salary_ranges: List[str] = None
    locations: List[str] = None
    levels: List[str] = None
    
    def __post_init__(self):
        if self.companies is None:
            self.companies = []
        if self.technologies is None:
            self.technologies = []
        if self.salary_ranges is None:
            self.salary_ranges = []
        if self.locations is None:
            self.locations = []
        if self.levels is None:
            self.levels = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheIndexEntry':
        """Cria instância a partir de dicionário"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    def matches_criteria(self, criteria: Dict[str, Any]) -> bool:
        """
        Verifica se entrada match com critérios de busca
        """
        # Filtro por data
        if 'date_from' in criteria:
            if self.timestamp < criteria['date_from']:
                return False
        
        if 'date_to' in criteria:
            if self.timestamp > criteria['date_to']:
                return False
        
        # Filtro por empresa
        if 'companies' in criteria:
            companies_filter = set(str(c).lower() for c in criteria['companies'])
            companies_entry = set(str(c).lower() for c in self.companies)
            if not companies_filter.intersection(companies_entry):
                return False
        
        # Filtro por tecnologia
        if 'technologies' in criteria:
            tech_filter = set(str(t).lower() for t in criteria['technologies'])
            tech_entry = set(str(t).lower() for t in self.technologies)
            if not tech_filter.intersection(tech_entry):
                return False
        
        # Filtro por localização
        if 'locations' in criteria:
            loc_filter = set(str(l).lower() for l in criteria['locations'])
            loc_entry = set(str(l).lower() for l in self.locations)
            if not loc_filter.intersection(loc_entry):
                return False
        
        # Filtro por nível
        if 'levels' in criteria:
            level_filter = set(str(l).lower() for l in criteria['levels'])
            level_entry = set(str(l).lower() for l in self.levels)
            if not level_filter.intersection(level_entry):
                return False
        
        # Filtro por número mínimo de vagas
        if 'min_jobs' in criteria:
            if self.job_count < criteria['min_jobs']:
                return False
        
        # Filtro por tamanho do arquivo
        if 'min_size' in criteria:
            if self.file_size < criteria['min_size']:
                return False
        
        return True


class CacheIndex:
    """
    Sistema de indexação do cache para busca e estatísticas rápidas
    
    Mantém um índice em memória e disco de todos os arquivos de cache
    com seus metadados, permitindo busca instantânea sem I/O.
    """
    
    def __init__(self, cache_dir: str = "data/cache", index_file: str = "cache_index.json"):
        """
        Inicializa sistema de índices
        
        Args:
            cache_dir: Diretório do cache
            index_file: Arquivo do índice
        """
        self.cache_dir = Path(cache_dir)
        self.index_file = self.cache_dir / index_file
        
        # Índice em memória
        self.entries: Dict[str, CacheIndexEntry] = {}
        
        # Índices especializados para busca rápida
        self.date_index: Dict[str, List[str]] = defaultdict(list)  # "YYYY-MM-DD" -> [cache_keys]
        self.company_index: Dict[str, List[str]] = defaultdict(list)  # company -> [cache_keys]
        self.tech_index: Dict[str, List[str]] = defaultdict(list)  # tech -> [cache_keys]
        self.location_index: Dict[str, List[str]] = defaultdict(list)  # location -> [cache_keys]
        
        # Estatísticas cache
        self.stats = {
            'total_entries': 0,
            'total_jobs': 0,
            'total_file_size': 0,
            'total_compressed_size': 0,
            'average_compression_ratio': 0.0,
            'oldest_entry': None,
            'newest_entry': None,
            'last_updated': None
        }
        
        # Thread lock para operações thread-safe
        self._lock = threading.RLock()
        
        # Carregar índice existente
        self.load_index()
    
    def _extract_metadata_from_jobs(self, jobs_data: List[Dict]) -> Dict[str, Any]:
        """
        Extrai metadados das vagas para indexação
        """
        metadata = {
            'job_count': len(jobs_data),
            'companies': [],
            'technologies': [],
            'salary_ranges': [],
            'locations': [],
            'levels': []
        }
        
        # Contadores para evitar duplicatas
        companies = set()
        technologies = set()
        salary_ranges = set()
        locations = set()
        levels = set()
        
        for job in jobs_data:
            # Empresa
            if 'empresa' in job and job['empresa']:
                companies.add(str(job['empresa']).strip())
            
            # Tecnologias
            if 'tecnologias_detectadas' in job:
                for tech in job['tecnologias_detectadas']:
                    if tech:
                        technologies.add(str(tech).strip())
            
            # Salário
            if 'salario' in job and job['salario']:
                salary_ranges.add(str(job['salario']).strip())
            
            # Localização
            if 'localizacao' in job and job['localizacao']:
                locations.add(str(job['localizacao']).strip())
            
            # Nível
            if 'nivel' in job and job['nivel']:
                levels.add(str(job['nivel']).strip())
            elif 'nivel_categorizado' in job and job['nivel_categorizado']:
                levels.add(str(job['nivel_categorizado']).strip())
        
        # Converter para listas ordenadas
        metadata['companies'] = sorted(list(companies))
        metadata['technologies'] = sorted(list(technologies))
        metadata['salary_ranges'] = sorted(list(salary_ranges))
        metadata['locations'] = sorted(list(locations))
        metadata['levels'] = sorted(list(levels))
        
        return metadata
    
    def add_entry(self, cache_key: str, file_path: str, url: str, 
                  jobs_data: List[Dict], original_size: int, compressed_size: int) -> None:
        """
        Adiciona entrada ao índice
        """
        with self._lock:
            # Extrair metadados
            metadata = self._extract_metadata_from_jobs(jobs_data)
            
            # Calcular compressão
            compression_ratio = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
            
            # Criar entrada
            entry = CacheIndexEntry(
                cache_key=cache_key,
                file_path=file_path,
                url=url,
                timestamp=datetime.now(),
                file_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                **metadata
            )
            
            # Adicionar aos índices
            self.entries[cache_key] = entry
            self._add_to_specialized_indexes(entry)
            
            # Atualizar estatísticas
            self._update_stats()
            
            # Salvar índice
            self.save_index()
    
    def _add_to_specialized_indexes(self, entry: CacheIndexEntry) -> None:
        """
        Adiciona entrada aos índices especializados
        """
        cache_key = entry.cache_key
        
        # Índice por data
        date_str = entry.timestamp.strftime('%Y-%m-%d')
        self.date_index[date_str].append(cache_key)
        
        # Índice por empresa
        for company in entry.companies:
            company_lower = company.lower()
            self.company_index[company_lower].append(cache_key)
        
        # Índice por tecnologia
        for tech in entry.technologies:
            tech_lower = tech.lower()
            self.tech_index[tech_lower].append(cache_key)
        
        # Índice por localização
        for location in entry.locations:
            location_lower = location.lower()
            self.location_index[location_lower].append(cache_key)
    
    def remove_entry(self, cache_key: str) -> bool:
        """
        Remove entrada do índice
        """
        with self._lock:
            if cache_key not in self.entries:
                return False
            
            entry = self.entries[cache_key]
            
            # Remover dos índices especializados
            self._remove_from_specialized_indexes(entry)
            
            # Remover entrada principal
            del self.entries[cache_key]
            
            # Atualizar estatísticas
            self._update_stats()
            
            # Salvar índice
            self.save_index()
            
            return True
    
    def _remove_from_specialized_indexes(self, entry: CacheIndexEntry) -> None:
        """
        Remove entrada dos índices especializados
        """
        cache_key = entry.cache_key
        
        # Remover do índice por data
        date_str = entry.timestamp.strftime('%Y-%m-%d')
        if cache_key in self.date_index[date_str]:
            self.date_index[date_str].remove(cache_key)
            if not self.date_index[date_str]:
                del self.date_index[date_str]
        
        # Remover dos demais índices
        for company in entry.companies:
            company_lower = company.lower()
            if cache_key in self.company_index[company_lower]:
                self.company_index[company_lower].remove(cache_key)
                if not self.company_index[company_lower]:
                    del self.company_index[company_lower]
        
        for tech in entry.technologies:
            tech_lower = tech.lower()
            if cache_key in self.tech_index[tech_lower]:
                self.tech_index[tech_lower].remove(cache_key)
                if not self.tech_index[tech_lower]:
                    del self.tech_index[tech_lower]
        
        for location in entry.locations:
            location_lower = location.lower()
            if cache_key in self.location_index[location_lower]:
                self.location_index[location_lower].remove(cache_key)
                if not self.location_index[location_lower]:
                    del self.location_index[location_lower]
    
    def search(self, criteria: Dict[str, Any]) -> List[CacheIndexEntry]:
        """
        Busca entradas que atendem aos critérios
        
        Args:
            criteria: Dicionário com critérios de busca
                - date_from: datetime
                - date_to: datetime
                - companies: List[str]
                - technologies: List[str]
                - locations: List[str]
                - levels: List[str]
                - min_jobs: int
                - min_size: int
        
        Returns:
            Lista de entradas que atendem aos critérios
        """
        with self._lock:
            # Se não há critérios, retornar tudo
            if not criteria:
                return list(self.entries.values())
            
            # Usar índices especializados quando possível
            candidate_keys = None
            
            # Filtro por tecnologia (mais específico primeiro)
            if 'technologies' in criteria:
                tech_keys = set()
                for tech in criteria['technologies']:
                    tech_lower = str(tech).lower()
                    tech_keys.update(self.tech_index.get(tech_lower, []))
                
                candidate_keys = tech_keys if candidate_keys is None else candidate_keys.intersection(tech_keys)
                
                if not candidate_keys:
                    return []
            
            # Filtro por empresa
            if 'companies' in criteria:
                company_keys = set()
                for company in criteria['companies']:
                    company_lower = str(company).lower()
                    company_keys.update(self.company_index.get(company_lower, []))
                
                candidate_keys = company_keys if candidate_keys is None else candidate_keys.intersection(company_keys)
                
                if not candidate_keys:
                    return []
            
            # Filtro por localização
            if 'locations' in criteria:
                location_keys = set()
                for location in criteria['locations']:
                    location_lower = str(location).lower()
                    location_keys.update(self.location_index.get(location_lower, []))
                
                candidate_keys = location_keys if candidate_keys is None else candidate_keys.intersection(location_keys)
                
                if not candidate_keys:
                    return []
            
            # Se não usou índices especializados, usar todas as chaves
            if candidate_keys is None:
                candidate_keys = set(self.entries.keys())
            
            # Aplicar filtros restantes
            results = []
            for cache_key in candidate_keys:
                if cache_key in self.entries:
                    entry = self.entries[cache_key]
                    if entry.matches_criteria(criteria):
                        results.append(entry)
            
            # Ordenar por timestamp (mais recente primeiro)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            
            return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache
        """
        with self._lock:
            return self.stats.copy()
    
    def get_top_companies(self, limit: int = 10) -> List[tuple]:
        """
        Retorna empresas com mais vagas
        """
        with self._lock:
            company_counts = Counter()
            
            for entry in self.entries.values():
                for company in entry.companies:
                    company_counts[company] += entry.job_count
            
            return company_counts.most_common(limit)
    
    def get_top_technologies(self, limit: int = 10) -> List[tuple]:
        """
        Retorna tecnologias mais demandadas
        """
        with self._lock:
            tech_counts = Counter()
            
            for entry in self.entries.values():
                for tech in entry.technologies:
                    tech_counts[tech] += entry.job_count
            
            return tech_counts.most_common(limit)
    
    def get_entries_by_date_range(self, days: int = 7) -> List[CacheIndexEntry]:
        """
        Retorna entradas dos últimos N dias
        """
        date_from = datetime.now() - timedelta(days=days)
        return self.search({'date_from': date_from})
    
    def _update_stats(self) -> None:
        """
        Atualiza estatísticas
        """
        if not self.entries:
            self.stats = {
                'total_entries': 0,
                'total_jobs': 0,
                'total_file_size': 0,
                'total_compressed_size': 0,
                'average_compression_ratio': 0.0,
                'oldest_entry': None,
                'newest_entry': None,
                'last_updated': datetime.now().isoformat()
            }
            return
        
        entries = list(self.entries.values())
        
        self.stats = {
            'total_entries': len(entries),
            'total_jobs': sum(e.job_count for e in entries),
            'total_file_size': sum(e.file_size for e in entries),
            'total_compressed_size': sum(e.compressed_size for e in entries),
            'average_compression_ratio': sum(e.compression_ratio for e in entries) / len(entries),
            'oldest_entry': min(e.timestamp for e in entries).isoformat(),
            'newest_entry': max(e.timestamp for e in entries).isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def save_index(self) -> bool:
        """
        Salva índice no disco
        """
        try:
            # Preparar dados para serialização
            index_data = {
                'entries': {k: v.to_dict() for k, v in self.entries.items()},
                'date_index': dict(self.date_index),
                'company_index': dict(self.company_index),
                'tech_index': dict(self.tech_index),
                'location_index': dict(self.location_index),
                'stats': self.stats,
                'version': '1.0',
                'created_at': datetime.now().isoformat()
            }
            
            # Criar diretório se necessário
            self.index_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Salvar com backup
            temp_file = self.index_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            # Substituir arquivo original
            temp_file.replace(self.index_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar índice: {e}")
            return False
    
    def load_index(self) -> bool:
        """
        Carrega índice do disco
        """
        if not self.index_file.exists():
            return True  # Índice vazio é válido
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Carregar entradas
            self.entries = {}
            for k, v in index_data.get('entries', {}).items():
                self.entries[k] = CacheIndexEntry.from_dict(v)
            
            # Carregar índices especializados
            self.date_index = defaultdict(list, index_data.get('date_index', {}))
            self.company_index = defaultdict(list, index_data.get('company_index', {}))
            self.tech_index = defaultdict(list, index_data.get('tech_index', {}))
            self.location_index = defaultdict(list, index_data.get('location_index', {}))
            
            # Carregar estatísticas
            self.stats = index_data.get('stats', {})
            
            print(f"✅ Índice do cache carregado: {len(self.entries)} entradas")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar índice: {e}")
            return False
    
    def rebuild_index(self, cache_dir: Optional[str] = None) -> int:
        """
        Reconstrói índice escaneando diretório de cache
        
        Returns:
            Número de arquivos indexados
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        
        print("🔄 Reconstruindo índice do cache...")
        
        with self._lock:
            # Limpar índices
            self.entries.clear()
            self.date_index.clear()
            self.company_index.clear()
            self.tech_index.clear()
            self.location_index.clear()
            
            indexed_count = 0
            
            # Escanear arquivos de cache
            if self.cache_dir.exists():
                for cache_file in self.cache_dir.glob("*.json.gz"):
                    try:
                        # Ler arquivo comprimido
                        import gzip
                        with gzip.open(cache_file, 'rt', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        # Extrair dados
                        if 'data' in cache_data and 'jobs' in cache_data['data']:
                            jobs_data = cache_data['data']['jobs']
                            url = cache_data.get('url', str(cache_file))
                            
                            # Calcular tamanhos
                            compressed_size = cache_file.stat().st_size
                            original_size = len(json.dumps(cache_data).encode('utf-8'))
                            
                            # Extrair cache_key do nome do arquivo
                            cache_key = cache_file.stem.replace('.json', '')
                            
                            # Adicionar ao índice
                            self.add_entry(
                                cache_key=cache_key,
                                file_path=str(cache_file),
                                url=url,
                                jobs_data=jobs_data,
                                original_size=original_size,
                                compressed_size=compressed_size
                            )
                            
                            indexed_count += 1
                            
                    except Exception as e:
                        print(f"⚠️ Erro ao indexar {cache_file}: {e}")
            
            print(f"✅ Índice reconstruído: {indexed_count} arquivos indexados")
            return indexed_count
    
    def print_summary(self) -> None:
        """
        Exibe resumo do índice
        """
        stats = self.get_stats()
        
        print("\n📊 RESUMO DO ÍNDICE DO CACHE")
        print("=" * 50)
        print(f"📁 Total de entradas: {stats['total_entries']}")
        print(f"💼 Total de vagas: {stats['total_jobs']}")
        print(f"💾 Tamanho original: {stats['total_file_size'] / 1024:.2f} KB")
        print(f"🗜️ Tamanho comprimido: {stats['total_compressed_size'] / 1024:.2f} KB")
        print(f"📈 Taxa média de compressão: {stats['average_compression_ratio']:.1f}%")
        
        if stats['oldest_entry']:
            print(f"📅 Entrada mais antiga: {stats['oldest_entry'][:10]}")
        if stats['newest_entry']:
            print(f"📅 Entrada mais recente: {stats['newest_entry'][:10]}")
        
        # Top empresas e tecnologias
        top_companies = self.get_top_companies(5)
        if top_companies:
            print(f"\n🏢 Top 5 Empresas:")
            for company, count in top_companies:
                print(f"   • {company}: {count} vagas")
        
        top_technologies = self.get_top_technologies(5)
        if top_technologies:
            print(f"\n💻 Top 5 Tecnologias:")
            for tech, count in top_technologies:
                print(f"   • {tech}: {count} vagas")
        
        print("=" * 50)