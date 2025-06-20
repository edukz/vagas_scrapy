"""
Detector de Duplicatas usando Machine Learning
==============================================

Identifica vagas duplicadas usando:
- Similaridade semântica de texto
- Comparação de características estruturadas
- Machine Learning para classificação de duplicatas
- Algoritmos de clustering para agrupamento
"""

import re
import hashlib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from difflib import SequenceMatcher
import joblib
from pathlib import Path


@dataclass
class DuplicateGroup:
    """Grupo de vagas duplicadas"""
    master_id: str
    duplicate_ids: List[str]
    similarity_scores: List[float]
    confidence: float
    reasons: List[str]
    
    def __str__(self):
        return f"Grupo com {len(self.duplicate_ids)} duplicatas (confiança: {self.confidence:.2%})"


@dataclass
class DuplicateResult:
    """Resultado da detecção de duplicatas"""
    total_jobs: int
    unique_jobs: int
    duplicate_groups: List[DuplicateGroup]
    removed_count: int
    efficiency_gain: float
    
    @property
    def duplicate_rate(self) -> float:
        return self.removed_count / self.total_jobs if self.total_jobs > 0 else 0.0


class DuplicateDetector:
    """
    Detector de duplicatas usando múltiplas técnicas:
    
    1. Hash exato (títulos e empresas idênticos)
    2. Similaridade semântica (TF-IDF + cosine)
    3. Fuzzy matching (títulos similares)
    4. Clustering hierárquico
    5. Detecção de anomalias
    """
    
    def __init__(self):
        # Configurações de similaridade
        self.similarity_thresholds = {
            'exact_match': 1.0,         # Hash exato
            'high_similarity': 0.9,     # Muito similares
            'medium_similarity': 0.75,  # Moderadamente similares
            'low_similarity': 0.6       # Baixa similaridade
        }
        
        # Vetorizador para texto
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            min_df=2,
            stop_words=['de', 'da', 'do', 'para', 'com', 'em', 'na', 'no', 'a', 'o']
        )
        
        # Algoritmo de clustering
        self.clustering = DBSCAN(
            eps=0.3,
            min_samples=2,
            metric='cosine'
        )
        
        # Detector de anomalias
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        
        # Cache para melhorar performance
        self._text_vectors = {}
        self._similarity_cache = {}
    
    def detect_duplicates(self, jobs: List[Dict], 
                         strict_mode: bool = False) -> DuplicateResult:
        """
        Detecta duplicatas em uma lista de vagas
        
        Args:
            jobs: Lista de vagas
            strict_mode: Modo mais restritivo para detecção
            
        Returns:
            Resultado da detecção com grupos de duplicatas
        """
        if not jobs:
            return DuplicateResult(0, 0, [], 0, 0.0)
        
        print(f"🔍 Analisando {len(jobs)} vagas para duplicatas...")
        
        # Preparar dados
        df = pd.DataFrame(jobs)
        df['job_id'] = df.index.astype(str)
        
        # 1. Detecção por hash exato
        exact_duplicates = self._find_exact_duplicates(df)
        
        # 2. Detecção por similaridade semântica
        semantic_duplicates = self._find_semantic_duplicates(df, strict_mode)
        
        # 3. Detecção por fuzzy matching de títulos
        fuzzy_duplicates = self._find_fuzzy_duplicates(df)
        
        # 4. Combinar resultados
        all_groups = self._merge_duplicate_groups(
            exact_duplicates + semantic_duplicates + fuzzy_duplicates
        )
        
        # 5. Filtrar grupos por confiança
        min_confidence = 0.8 if strict_mode else 0.6
        filtered_groups = [g for g in all_groups if g.confidence >= min_confidence]
        
        # 6. Calcular estatísticas
        removed_count = sum(len(g.duplicate_ids) for g in filtered_groups)
        unique_jobs = len(jobs) - removed_count
        efficiency_gain = removed_count / len(jobs) if jobs else 0.0
        
        result = DuplicateResult(
            total_jobs=len(jobs),
            unique_jobs=unique_jobs,
            duplicate_groups=filtered_groups,
            removed_count=removed_count,
            efficiency_gain=efficiency_gain
        )
        
        print(f"✅ Detecção concluída: {removed_count} duplicatas em {len(filtered_groups)} grupos")
        
        return result
    
    def _find_exact_duplicates(self, df: pd.DataFrame) -> List[DuplicateGroup]:
        """Encontra duplicatas exatas por hash"""
        duplicates = []
        
        # Criar hash baseado em título + empresa
        df['hash'] = df.apply(
            lambda row: hashlib.md5(
                f"{row.get('titulo', '').lower().strip()}"
                f"{row.get('empresa', '').lower().strip()}"
                .encode('utf-8')
            ).hexdigest(),
            axis=1
        )
        
        # Agrupar por hash
        hash_groups = df.groupby('hash')
        
        for hash_val, group in hash_groups:
            if len(group) > 1:
                job_ids = group['job_id'].tolist()
                master_id = job_ids[0]
                duplicate_ids = job_ids[1:]
                
                group_obj = DuplicateGroup(
                    master_id=master_id,
                    duplicate_ids=duplicate_ids,
                    similarity_scores=[1.0] * len(duplicate_ids),
                    confidence=1.0,
                    reasons=['Hash exato: título + empresa idênticos']
                )
                
                duplicates.append(group_obj)
        
        return duplicates
    
    def _find_semantic_duplicates(self, df: pd.DataFrame, 
                                strict_mode: bool) -> List[DuplicateGroup]:
        """Encontra duplicatas por similaridade semântica"""
        duplicates = []
        
        # Preparar textos para análise
        texts = []
        for _, row in df.iterrows():
            text = f"{row.get('titulo', '')} {row.get('descricao', '')} {row.get('empresa', '')}"
            texts.append(self._clean_text(text))
        
        # Vetorizar textos
        try:
            text_vectors = self.vectorizer.fit_transform(texts)
        except:
            return duplicates  # Falha na vetorização
        
        # Calcular matriz de similaridade
        similarity_matrix = cosine_similarity(text_vectors)
        
        # Encontrar pares similares
        threshold = self.similarity_thresholds['high_similarity'] if strict_mode else \
                   self.similarity_thresholds['medium_similarity']
        
        processed_ids = set()
        
        for i in range(len(similarity_matrix)):
            if str(i) in processed_ids:
                continue
            
            similar_indices = []
            similarities = []
            
            for j in range(i + 1, len(similarity_matrix)):
                similarity = similarity_matrix[i][j]
                
                if similarity >= threshold:
                    similar_indices.append(j)
                    similarities.append(similarity)
            
            if similar_indices:
                # Criar grupo de duplicatas
                master_id = str(i)
                duplicate_ids = [str(idx) for idx in similar_indices]
                
                # Marcar como processados
                processed_ids.add(master_id)
                processed_ids.update(duplicate_ids)
                
                # Analisar razões da similaridade
                reasons = self._analyze_similarity_reasons(
                    df.iloc[i], [df.iloc[idx] for idx in similar_indices]
                )
                
                group_obj = DuplicateGroup(
                    master_id=master_id,
                    duplicate_ids=duplicate_ids,
                    similarity_scores=similarities,
                    confidence=np.mean(similarities),
                    reasons=reasons
                )
                
                duplicates.append(group_obj)
        
        return duplicates
    
    def _find_fuzzy_duplicates(self, df: pd.DataFrame) -> List[DuplicateGroup]:
        """Encontra duplicatas por fuzzy matching de títulos"""
        duplicates = []
        
        # Extrair títulos únicos
        titles = df['titulo'].fillna('').tolist()
        
        processed_indices = set()
        
        for i, title1 in enumerate(titles):
            if i in processed_indices:
                continue
            
            similar_indices = []
            similarities = []
            
            for j, title2 in enumerate(titles[i+1:], i+1):
                if j in processed_indices:
                    continue
                
                # Calcular similaridade de títulos
                similarity = self._calculate_title_similarity(title1, title2)
                
                if similarity >= 0.85:  # Títulos muito similares
                    # Verificar se são da mesma empresa
                    company1 = df.iloc[i].get('empresa', '').lower()
                    company2 = df.iloc[j].get('empresa', '').lower()
                    
                    if company1 == company2 or not company1 or not company2:
                        similar_indices.append(j)
                        similarities.append(similarity)
            
            if similar_indices:
                master_id = str(i)
                duplicate_ids = [str(idx) for idx in similar_indices]
                
                processed_indices.add(i)
                processed_indices.update(similar_indices)
                
                group_obj = DuplicateGroup(
                    master_id=master_id,
                    duplicate_ids=duplicate_ids,
                    similarity_scores=similarities,
                    confidence=np.mean(similarities),
                    reasons=['Títulos muito similares na mesma empresa']
                )
                
                duplicates.append(group_obj)
        
        return duplicates
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calcula similaridade entre títulos"""
        if not title1 or not title2:
            return 0.0
        
        # Normalizar títulos
        title1 = self._normalize_title(title1)
        title2 = self._normalize_title(title2)
        
        # Usar SequenceMatcher para similaridade
        return SequenceMatcher(None, title1, title2).ratio()
    
    def _normalize_title(self, title: str) -> str:
        """Normaliza título para comparação"""
        # Converter para minúsculas
        title = title.lower()
        
        # Remover números e caracteres especiais
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\d+', '', title)
        
        # Remover palavras comuns
        stop_words = ['vaga', 'para', 'de', 'em', 'na', 'no', 'da', 'do', 'com']
        words = [w for w in title.split() if w not in stop_words and len(w) > 2]
        
        return ' '.join(words)
    
    def _analyze_similarity_reasons(self, master_job: pd.Series, 
                                  similar_jobs: List[pd.Series]) -> List[str]:
        """Analisa razões da similaridade"""
        reasons = []
        
        master_title = master_job.get('titulo', '').lower()
        master_company = master_job.get('empresa', '').lower()
        
        # Verificar títulos similares
        title_similarities = []
        for job in similar_jobs:
            similarity = self._calculate_title_similarity(
                master_title, job.get('titulo', '')
            )
            title_similarities.append(similarity)
        
        avg_title_sim = np.mean(title_similarities)
        if avg_title_sim > 0.8:
            reasons.append(f"Títulos muito similares ({avg_title_sim:.1%})")
        
        # Verificar mesma empresa
        same_company = all(
            job.get('empresa', '').lower() == master_company 
            for job in similar_jobs
        )
        if same_company and master_company:
            reasons.append("Mesma empresa")
        
        # Verificar tecnologias similares
        master_techs = set(master_job.get('tecnologias_detectadas', []))
        if master_techs:
            tech_overlaps = []
            for job in similar_jobs:
                job_techs = set(job.get('tecnologias_detectadas', []))
                if job_techs:
                    overlap = len(master_techs & job_techs) / len(master_techs | job_techs)
                    tech_overlaps.append(overlap)
            
            if tech_overlaps and np.mean(tech_overlaps) > 0.7:
                reasons.append("Tecnologias similares")
        
        return reasons or ["Alta similaridade semântica"]
    
    def _merge_duplicate_groups(self, groups: List[DuplicateGroup]) -> List[DuplicateGroup]:
        """Combina grupos sobrepostos de duplicatas"""
        if not groups:
            return []
        
        # Criar mapeamento de job_id para grupos
        job_to_groups = {}
        for i, group in enumerate(groups):
            all_ids = [group.master_id] + group.duplicate_ids
            for job_id in all_ids:
                if job_id not in job_to_groups:
                    job_to_groups[job_id] = []
                job_to_groups[job_id].append(i)
        
        # Encontrar grupos sobrepostos
        merged_groups = []
        processed_group_indices = set()
        
        for i, group in enumerate(groups):
            if i in processed_group_indices:
                continue
            
            # Encontrar todos os grupos que compartilham jobs
            related_groups = {i}
            to_check = {i}
            
            while to_check:
                current_group_idx = to_check.pop()
                current_group = groups[current_group_idx]
                all_jobs = [current_group.master_id] + current_group.duplicate_ids
                
                for job_id in all_jobs:
                    for group_idx in job_to_groups.get(job_id, []):
                        if group_idx not in related_groups:
                            related_groups.add(group_idx)
                            to_check.add(group_idx)
            
            # Combinar grupos relacionados
            if len(related_groups) > 1:
                combined_group = self._combine_groups([groups[idx] for idx in related_groups])
                merged_groups.append(combined_group)
            else:
                merged_groups.append(group)
            
            processed_group_indices.update(related_groups)
        
        return merged_groups
    
    def _combine_groups(self, groups: List[DuplicateGroup]) -> DuplicateGroup:
        """Combina múltiplos grupos em um só"""
        all_job_ids = set()
        all_similarities = []
        all_reasons = []
        
        for group in groups:
            all_job_ids.add(group.master_id)
            all_job_ids.update(group.duplicate_ids)
            all_similarities.extend(group.similarity_scores)
            all_reasons.extend(group.reasons)
        
        # Escolher master (primeiro por ordem)
        sorted_ids = sorted(all_job_ids)
        master_id = sorted_ids[0]
        duplicate_ids = sorted_ids[1:]
        
        # Calcular confiança combinada
        confidence = np.mean(all_similarities) if all_similarities else 0.5
        
        # Remover razões duplicadas
        unique_reasons = list(set(all_reasons))
        
        return DuplicateGroup(
            master_id=master_id,
            duplicate_ids=duplicate_ids,
            similarity_scores=all_similarities,
            confidence=confidence,
            reasons=unique_reasons
        )
    
    def _clean_text(self, text: str) -> str:
        """Limpa texto para análise"""
        if not text:
            return ""
        
        # Converter para minúsculas
        text = text.lower()
        
        # Remover HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remover caracteres especiais
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remover números
        text = re.sub(r'\d+', ' ', text)
        
        # Remover espaços extras
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def remove_duplicates(self, jobs: List[Dict], 
                         keep_best: bool = True) -> Tuple[List[Dict], DuplicateResult]:
        """
        Remove duplicatas de uma lista de vagas
        
        Args:
            jobs: Lista original de vagas
            keep_best: Se deve manter a melhor vaga de cada grupo
            
        Returns:
            (Lista filtrada, Resultado da detecção)
        """
        result = self.detect_duplicates(jobs)
        
        if not result.duplicate_groups:
            return jobs, result
        
        # IDs a serem removidos
        ids_to_remove = set()
        for group in result.duplicate_groups:
            ids_to_remove.update(group.duplicate_ids)
        
        # Filtrar vagas
        filtered_jobs = []
        for i, job in enumerate(jobs):
            if str(i) not in ids_to_remove:
                filtered_jobs.append(job)
        
        print(f"✅ {len(ids_to_remove)} duplicatas removidas")
        print(f"📊 Dataset reduzido de {len(jobs)} para {len(filtered_jobs)} vagas")
        
        return filtered_jobs, result
    
    def get_duplicate_report(self, result: DuplicateResult) -> str:
        """Gera relatório detalhado de duplicatas"""
        if not result.duplicate_groups:
            return "✅ Nenhuma duplicata encontrada"
        
        report = f"""
🔍 RELATÓRIO DE DETECÇÃO DE DUPLICATAS

📊 Estatísticas Gerais:
   • Total de vagas analisadas: {result.total_jobs:,}
   • Vagas únicas: {result.unique_jobs:,}
   • Duplicatas encontradas: {result.removed_count:,}
   • Taxa de duplicação: {result.duplicate_rate:.1%}
   • Eficiência ganho: {result.efficiency_gain:.1%}

📋 Grupos de Duplicatas: {len(result.duplicate_groups)}

"""
        
        for i, group in enumerate(result.duplicate_groups[:10], 1):  # Top 10
            report += f"""
   {i}. Grupo com {len(group.duplicate_ids)} duplicatas
      • Confiança: {group.confidence:.1%}
      • Razões: {', '.join(group.reasons)}
      • Master: {group.master_id}
      • Duplicatas: {', '.join(group.duplicate_ids[:5])}{'...' if len(group.duplicate_ids) > 5 else ''}
"""
        
        if len(result.duplicate_groups) > 10:
            report += f"\n   ... e mais {len(result.duplicate_groups) - 10} grupos"
        
        return report
    
    def benchmark_performance(self, jobs: List[Dict]) -> Dict:
        """Avalia performance do detector"""
        import time
        
        start_time = time.time()
        result = self.detect_duplicates(jobs)
        end_time = time.time()
        
        processing_time = end_time - start_time
        jobs_per_second = len(jobs) / processing_time if processing_time > 0 else 0
        
        return {
            'processing_time': processing_time,
            'jobs_per_second': jobs_per_second,
            'duplicate_rate': result.duplicate_rate,
            'groups_found': len(result.duplicate_groups),
            'efficiency': result.efficiency_gain
        }


# Exemplo de uso
if __name__ == "__main__":
    detector = DuplicateDetector()
    
    # Dados de exemplo com duplicatas intencionais
    jobs_example = [
        {
            'titulo': 'Desenvolvedor Python Sênior',
            'empresa': 'TechCorp',
            'descricao': 'Vaga para desenvolvedor Python experiente',
            'tecnologias_detectadas': ['Python', 'Django']
        },
        {
            'titulo': 'Desenvolvedor Python Sr',  # Similar ao anterior
            'empresa': 'TechCorp',
            'descricao': 'Buscamos desenvolvedor Python com experiência',
            'tecnologias_detectadas': ['Python', 'Django']
        },
        {
            'titulo': 'Full Stack Developer',
            'empresa': 'StartupXYZ',
            'descricao': 'Desenvolvedor full stack para projeto inovador',
            'tecnologias_detectadas': ['React', 'Node.js']
        },
        {
            'titulo': 'Desenvolvedor Python Sênior',  # Duplicata exata
            'empresa': 'TechCorp',
            'descricao': 'Vaga para desenvolvedor Python experiente',
            'tecnologias_detectadas': ['Python', 'Django']
        }
    ]
    
    # Detectar duplicatas
    result = detector.detect_duplicates(jobs_example)
    
    print(detector.get_duplicate_report(result))
    
    # Remover duplicatas
    clean_jobs, _ = detector.remove_duplicates(jobs_example)
    
    print(f"\n✅ Dataset limpo: {len(clean_jobs)} vagas únicas")