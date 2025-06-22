"""
Sistema de Deduplicação Avançado

Este módulo implementa deduplicação robusta para evitar dados repetidos
em todos os níveis: intra-página, inter-páginas, sessões e arquivos.

Funcionalidades:
- 🔍 Detecção inteligente de duplicatas
- 🎯 Múltiplos critérios de comparação
- 📊 Estatísticas de deduplicação
- 🧹 Limpeza de arquivos existentes
- ⚡ Performance otimizada com hashing
"""

import hashlib
import json
import os
from typing import Dict, List, Set, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import re


class JobDeduplicator:
    """
    Sistema avançado de deduplicação de vagas
    
    Usa múltiplos critérios para identificar duplicatas:
    - URL exata
    - Título + empresa
    - Conteúdo similar (fuzzy matching)
    """
    
    def __init__(self, 
                 similarity_threshold: float = 0.95,
                 enable_fuzzy_matching: bool = True,
                 stats_file: str = "data/deduplication_stats.json"):
        """
        Inicializa sistema de deduplicação
        
        Args:
            similarity_threshold: Limiar para considerar textos similares (0-1)
            enable_fuzzy_matching: Se deve usar matching aproximado
            stats_file: Arquivo para salvar estatísticas
        """
        self.similarity_threshold = similarity_threshold
        self.enable_fuzzy_matching = enable_fuzzy_matching
        self.stats_file = stats_file
        
        # Conjuntos de tracking para sessão atual
        self.seen_urls: Set[str] = set()
        self.seen_hashes: Set[str] = set()
        self.seen_title_company: Set[str] = set()
        
        # Estatísticas
        self.stats = {
            'total_processed': 0,
            'duplicates_removed': 0,
            'duplicates_by_url': 0,
            'duplicates_by_hash': 0,
            'duplicates_by_title_company': 0,
            'duplicates_by_similarity': 0,
            'session_start': datetime.now().isoformat()
        }
        
        # Carregar dados existentes para evitar duplicatas entre sessões
        self._load_global_data()
    
    def _load_global_data(self) -> None:
        """Carrega dados de sessões anteriores"""
        try:
            # Carregar URLs conhecidas de arquivos existentes
            self._load_existing_urls()
            print(f"🔍 Deduplicação: {len(self.seen_urls)} URLs conhecidas carregadas")
        except Exception as e:
            print(f"⚠️ Erro ao carregar dados globais: {e}")
    
    def _load_existing_urls(self) -> None:
        """Carrega URLs de arquivos de resultados existentes"""
        results_dir = Path("data")
        if not results_dir.exists():
            return
        
        # Procurar arquivos JSON de resultados
        for json_file in results_dir.glob("**/*.json"):
            try:
                if json_file.name.startswith(('results_', 'vagas_')):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extrair URLs de diferentes formatos
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'link' in item:
                                self._add_to_global_sets(item)
                    elif isinstance(data, dict) and 'vagas' in data:
                        for item in data['vagas']:
                            self._add_to_global_sets(item)
            except Exception as e:
                continue  # Arquivo corrompido, ignorar
    
    def _add_to_global_sets(self, job: Dict[str, Any]) -> None:
        """Adiciona job aos conjuntos globais de tracking"""
        # URL
        if 'link' in job and job['link']:
            self.seen_urls.add(self._normalize_url(job['link']))
        
        # Hash do conteúdo
        content_hash = self._calculate_content_hash(job)
        self.seen_hashes.add(content_hash)
        
        # Título + empresa
        title_company_key = self._get_title_company_key(job)
        if title_company_key:
            self.seen_title_company.add(title_company_key)
    
    def _normalize_url(self, url: str) -> str:
        """Normaliza URL para comparação"""
        if not url:
            return ""
        
        # Remover parâmetros de tracking comuns
        url = re.sub(r'[?&](utm_|ref=|source=|campaign=)[^&]*', '', url)
        
        # Remover fragmentos
        url = url.split('#')[0]
        
        # Normalizar protocolo
        url = url.replace('http://', 'https://')
        
        # Remover trailing slash
        url = url.rstrip('/')
        
        return url.lower()
    
    def _calculate_content_hash(self, job: Dict[str, Any]) -> str:
        """Calcula hash do conteúdo principal da vaga"""
        # Campos principais para hash
        key_fields = ['titulo', 'empresa', 'localizacao', 'salario']
        
        content_parts = []
        for field in key_fields:
            if field in job and job[field]:
                # Normalizar texto
                text = str(job[field]).lower().strip()
                # Remover espaços extras
                text = re.sub(r'\s+', ' ', text)
                content_parts.append(text)
        
        # Adicionar tecnologias se disponível
        if 'tecnologias_detectadas' in job and job['tecnologias_detectadas']:
            techs = sorted([str(t).lower() for t in job['tecnologias_detectadas']])
            content_parts.extend(techs)
        
        # Gerar hash
        content_str = '|'.join(content_parts)
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()
    
    def _get_title_company_key(self, job: Dict[str, Any]) -> Optional[str]:
        """Gera chave título + empresa para comparação"""
        title = job.get('titulo', '').strip()
        company = job.get('empresa', '').strip()
        
        if not title or not company:
            return None
        
        # Normalizar
        title = re.sub(r'\s+', ' ', title.lower())
        company = re.sub(r'\s+', ' ', company.lower())
        
        return f"{title}|{company}"
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre dois textos (Jaccard similarity)"""
        if not text1 or not text2:
            return 0.0
        
        # Tokenizar em palavras
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Similaridade de Jaccard
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def is_duplicate(self, job: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verifica se job é duplicata
        
        Returns:
            (is_duplicate: bool, reason: str)
        """
        self.stats['total_processed'] += 1
        
        # 1. Verificar URL exata
        if 'link' in job and job['link']:
            normalized_url = self._normalize_url(job['link'])
            if normalized_url in self.seen_urls:
                self.stats['duplicates_by_url'] += 1
                return True, f"URL duplicada: {normalized_url[:60]}..."
        
        # 2. Verificar hash do conteúdo
        content_hash = self._calculate_content_hash(job)
        if content_hash in self.seen_hashes:
            self.stats['duplicates_by_hash'] += 1
            return True, f"Conteúdo duplicado (hash: {content_hash[:8]})"
        
        # 3. Verificar título + empresa
        title_company_key = self._get_title_company_key(job)
        if title_company_key and title_company_key in self.seen_title_company:
            self.stats['duplicates_by_title_company'] += 1
            return True, f"Título + empresa duplicados: {title_company_key[:60]}..."
        
        # 4. Verificar similaridade (se habilitado)
        if self.enable_fuzzy_matching and 'titulo' in job:
            current_title = job['titulo']
            for seen_key in self.seen_title_company:
                seen_title = seen_key.split('|')[0]
                similarity = self._calculate_text_similarity(current_title, seen_title)
                
                if similarity >= self.similarity_threshold:
                    self.stats['duplicates_by_similarity'] += 1
                    return True, f"Título similar ({similarity:.2f}): {seen_title[:60]}..."
        
        return False, ""
    
    def add_job(self, job: Dict[str, Any]) -> None:
        """Adiciona job aos conjuntos de tracking"""
        # URL
        if 'link' in job and job['link']:
            self.seen_urls.add(self._normalize_url(job['link']))
        
        # Hash
        content_hash = self._calculate_content_hash(job)
        self.seen_hashes.add(content_hash)
        
        # Título + empresa
        title_company_key = self._get_title_company_key(job)
        if title_company_key:
            self.seen_title_company.add(title_company_key)
    
    def deduplicate_jobs(self, jobs: List[Dict[str, Any]], verbose: bool = True) -> List[Dict[str, Any]]:
        """
        Remove duplicatas de uma lista de jobs
        
        Args:
            jobs: Lista de jobs para deduplica
            verbose: Se deve mostrar logs detalhados
            
        Returns:
            Lista de jobs sem duplicatas
        """
        if not jobs:
            return jobs
        
        original_count = len(jobs)
        deduplicated = []
        duplicates_found = []
        
        for i, job in enumerate(jobs):
            is_dup, reason = self.is_duplicate(job)
            
            if is_dup:
                duplicates_found.append((i, reason))
                if verbose:
                    print(f"🔍 Duplicata {len(duplicates_found):3d}: {reason}")
            else:
                # Não é duplicata, adicionar à lista e tracking
                deduplicated.append(job)
                self.add_job(job)
        
        # Atualizar estatísticas
        removed_count = original_count - len(deduplicated)
        self.stats['duplicates_removed'] += removed_count
        
        if verbose and removed_count > 0:
            print(f"\n🧹 DEDUPLICAÇÃO CONCLUÍDA:")
            print(f"   📊 Total processados: {original_count}")
            print(f"   ❌ Duplicatas removidas: {removed_count}")
            print(f"   ✅ Jobs únicos: {len(deduplicated)}")
            print(f"   📈 Eficiência: {(len(deduplicated)/original_count)*100:.1f}%")
        
        return deduplicated
    
    def clean_existing_files(self, directory: str = "data") -> int:
        """
        Limpa duplicatas em arquivos existentes
        
        Returns:
            Número de duplicatas removidas
        """
        print(f"🧹 Iniciando limpeza de duplicatas em {directory}...")
        
        total_removed = 0
        files_processed = 0
        
        data_dir = Path(directory)
        if not data_dir.exists():
            print(f"❌ Diretório {directory} não encontrado")
            return 0
        
        # Resetar tracking para limpeza global
        original_seen = {
            'urls': self.seen_urls.copy(),
            'hashes': self.seen_hashes.copy(),
            'title_company': self.seen_title_company.copy()
        }
        
        self.seen_urls.clear()
        self.seen_hashes.clear()
        self.seen_title_company.clear()
        
        # Processar arquivos JSON
        for json_file in data_dir.glob("**/*.json"):
            if json_file.name.startswith(('results_', 'vagas_')):
                try:
                    files_processed += 1
                    
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    original_data = data.copy()
                    
                    # Processar diferentes formatos
                    if isinstance(data, list):
                        cleaned_jobs = self.deduplicate_jobs(data, verbose=False)
                        removed = len(data) - len(cleaned_jobs)
                        if removed > 0:
                            # Fazer backup e salvar versão limpa
                            backup_file = json_file.with_suffix('.bak')
                            json_file.rename(backup_file)
                            
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump(cleaned_jobs, f, ensure_ascii=False, indent=2)
                            
                            total_removed += removed
                            print(f"✅ {json_file.name}: {removed} duplicatas removidas")
                    
                    elif isinstance(data, dict) and 'vagas' in data:
                        cleaned_jobs = self.deduplicate_jobs(data['vagas'], verbose=False)
                        removed = len(data['vagas']) - len(cleaned_jobs)
                        if removed > 0:
                            # Fazer backup e salvar versão limpa
                            backup_file = json_file.with_suffix('.bak')
                            json_file.rename(backup_file)
                            
                            data['vagas'] = cleaned_jobs
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            
                            total_removed += removed
                            print(f"✅ {json_file.name}: {removed} duplicatas removidas")
                
                except Exception as e:
                    print(f"❌ Erro ao processar {json_file.name}: {e}")
        
        # Restaurar tracking original
        self.seen_urls = original_seen['urls']
        self.seen_hashes = original_seen['hashes']
        self.seen_title_company = original_seen['title_company']
        
        print(f"\n🎯 LIMPEZA CONCLUÍDA:")
        print(f"   📁 Arquivos processados: {files_processed}")
        print(f"   🧹 Total de duplicatas removidas: {total_removed}")
        
        return total_removed
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de deduplicação"""
        stats = self.stats.copy()
        stats.update({
            'unique_urls': len(self.seen_urls),
            'unique_hashes': len(self.seen_hashes),
            'unique_title_company': len(self.seen_title_company),
            'deduplication_rate': (
                self.stats['duplicates_removed'] / max(1, self.stats['total_processed'])
            ) * 100
        })
        return stats
    
    def print_stats(self) -> None:
        """Exibe estatísticas detalhadas"""
        stats = self.get_stats()
        
        print("\n📊 ESTATÍSTICAS DE DEDUPLICAÇÃO")
        print("=" * 50)
        print(f"📋 Total processado: {stats['total_processed']}")
        print(f"❌ Duplicatas removidas: {stats['duplicates_removed']}")
        print(f"📈 Taxa de deduplicação: {stats['deduplication_rate']:.1f}%")
        print(f"\n🔍 DETALHES POR TIPO:")
        print(f"   🔗 Por URL: {stats['duplicates_by_url']}")
        print(f"   🏷️  Por hash: {stats['duplicates_by_hash']}")
        print(f"   📝 Por título+empresa: {stats['duplicates_by_title_company']}")
        print(f"   🔤 Por similaridade: {stats['duplicates_by_similarity']}")
        print(f"\n💾 DADOS ÚNICOS CONHECIDOS:")
        print(f"   🔗 URLs únicas: {stats['unique_urls']}")
        print(f"   🏷️  Hashes únicos: {stats['unique_hashes']}")
        print(f"   📝 Título+empresa únicos: {stats['unique_title_company']}")
        print("=" * 50)
    
    def save_stats(self) -> None:
        """Salva estatísticas em arquivo"""
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            
            stats = self.get_stats()
            stats['last_updated'] = datetime.now().isoformat()
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ Erro ao salvar estatísticas: {e}")


def deduplicate_file(file_path: str, 
                    output_path: Optional[str] = None,
                    backup: bool = True) -> int:
    """
    Função utilitária para deduplica um arquivo específico
    
    Args:
        file_path: Caminho do arquivo a ser processado
        output_path: Caminho de saída (None = sobrescrever original)
        backup: Se deve fazer backup do arquivo original
        
    Returns:
        Número de duplicatas removidas
    """
    deduplicator = JobDeduplicator()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_count = 0
        cleaned_data = None
        
        if isinstance(data, list):
            original_count = len(data)
            cleaned_data = deduplicator.deduplicate_jobs(data)
        elif isinstance(data, dict) and 'vagas' in data:
            original_count = len(data['vagas'])
            data['vagas'] = deduplicator.deduplicate_jobs(data['vagas'])
            cleaned_data = data
        else:
            print(f"❌ Formato não suportado em {file_path}")
            return 0
        
        removed_count = original_count - (
            len(cleaned_data) if isinstance(cleaned_data, list) 
            else len(cleaned_data['vagas'])
        )
        
        if removed_count > 0:
            # Fazer backup se solicitado
            if backup and not output_path:
                backup_path = file_path + '.bak'
                import shutil
                shutil.copy2(file_path, backup_path)
                print(f"📋 Backup criado: {backup_path}")
            
            # Salvar arquivo limpo
            output_file = output_path or file_path
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ {file_path}: {removed_count} duplicatas removidas")
        else:
            print(f"ℹ️ {file_path}: Nenhuma duplicata encontrada")
        
        return removed_count
        
    except Exception as e:
        print(f"❌ Erro ao processar {file_path}: {e}")
        return 0


if __name__ == "__main__":
    """Utilitário de linha de comando para deduplicação"""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python deduplicator.py <comando> [opções]")
        print("Comandos:")
        print("  clean [diretório]  - Limpa duplicatas em arquivos existentes")
        print("  file <arquivo>     - Deduplica arquivo específico")
        print("  stats              - Mostra estatísticas")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "clean":
        directory = sys.argv[2] if len(sys.argv) > 2 else "data"
        deduplicator = JobDeduplicator()
        removed = deduplicator.clean_existing_files(directory)
        deduplicator.print_stats()
        
    elif command == "file":
        if len(sys.argv) < 3:
            print("❌ Especifique o arquivo: python deduplicator.py file <arquivo>")
            sys.exit(1)
        
        file_path = sys.argv[2]
        removed = deduplicate_file(file_path)
        print(f"✅ Total de duplicatas removidas: {removed}")
        
    elif command == "stats":
        deduplicator = JobDeduplicator()
        deduplicator.print_stats()
        
    else:
        print(f"❌ Comando desconhecido: {command}")
        sys.exit(1)