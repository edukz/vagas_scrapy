"""
Sistema de Recomendação de Vagas
================================

Recomenda vagas baseado em:
- Perfil do usuário (skills, experiência, preferências)
- Histórico de aplicações e visualizações
- Similaridade com outros usuários
- Machine Learning colaborativo e baseado em conteúdo
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from collections import defaultdict
import json


@dataclass
class UserProfile:
    """Perfil do usuário para recomendações"""
    user_id: str
    skills: List[str]
    experience_years: int
    seniority_level: str
    preferred_locations: List[str]
    preferred_salary_min: float
    preferred_salary_max: float
    preferred_companies: List[str]
    avoided_companies: List[str]
    work_mode_preference: str  # remoto, presencial, hibrido
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'skills': self.skills,
            'experience_years': self.experience_years,
            'seniority_level': self.seniority_level,
            'preferred_locations': self.preferred_locations,
            'preferred_salary_min': self.preferred_salary_min,
            'preferred_salary_max': self.preferred_salary_max,
            'preferred_companies': self.preferred_companies,
            'avoided_companies': self.avoided_companies,
            'work_mode_preference': self.work_mode_preference
        }


@dataclass
class Recommendation:
    """Recomendação de vaga"""
    job_id: str
    job_title: str
    company: str
    score: float
    reasons: List[str]
    match_percentage: float
    job_data: Dict
    
    def __str__(self):
        return f"{self.job_title} @ {self.company} ({self.match_percentage:.1%} match)"


class JobRecommender:
    """
    Sistema de recomendação híbrido que combina:
    - Filtragem colaborativa (usuários similares)
    - Filtragem baseada em conteúdo (similaridade de vagas)
    - Regras de negócio (preferências explícitas)
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        self.svd = TruncatedSVD(n_components=50, random_state=42)
        
        # Pesos para diferentes fatores de recomendação
        self.weights = {
            'content_similarity': 0.3,    # Similaridade de conteúdo
            'skill_match': 0.25,          # Match de skills
            'seniority_match': 0.15,      # Match de senioridade
            'location_preference': 0.1,   # Preferência de localização
            'salary_match': 0.1,          # Faixa salarial
            'company_preference': 0.1     # Preferência de empresa
        }
        
        # Cache para melhorar performance
        self._job_vectors = {}
        self._similarity_matrix = None
        self._user_interactions = defaultdict(dict)
    
    def fit(self, jobs: List[Dict], user_interactions: List[Dict] = None):
        """
        Treina o sistema de recomendação
        
        Args:
            jobs: Lista de vagas com suas características
            user_interactions: Histórico de interações usuário-vaga
        """
        self.jobs_df = pd.DataFrame(jobs)
        
        # Preparar textos para vetorização
        job_texts = []
        for job in jobs:
            text = f"{job.get('titulo', '')} {job.get('descricao', '')} {' '.join(job.get('tecnologias_detectadas', []))}"
            job_texts.append(text)
        
        # Vetorizar conteúdo das vagas
        job_features = self.vectorizer.fit_transform(job_texts)
        
        # Reduzir dimensionalidade
        self.job_features_reduced = self.svd.fit_transform(job_features.toarray())
        
        # Calcular matriz de similaridade entre vagas
        self._similarity_matrix = cosine_similarity(self.job_features_reduced)
        
        # Processar interações de usuários se fornecidas
        if user_interactions:
            self._process_user_interactions(user_interactions)
        
        print(f"✅ Sistema treinado com {len(jobs)} vagas")
    
    def _process_user_interactions(self, interactions: List[Dict]):
        """Processa histórico de interações usuário-vaga"""
        for interaction in interactions:
            user_id = interaction.get('user_id')
            job_id = interaction.get('job_id')
            action = interaction.get('action')  # view, apply, like, dislike
            
            if user_id and job_id:
                # Converter ações em scores
                action_scores = {
                    'view': 1,
                    'like': 3,
                    'apply': 5,
                    'dislike': -2,
                    'reject': -1
                }
                
                score = action_scores.get(action, 0)
                self._user_interactions[user_id][job_id] = score
    
    def recommend(self, user_profile: UserProfile, 
                  n_recommendations: int = 10,
                  exclude_applied: List[str] = None) -> List[Recommendation]:
        """
        Gera recomendações para um usuário
        
        Args:
            user_profile: Perfil do usuário
            n_recommendations: Número de recomendações
            exclude_applied: IDs de vagas já aplicadas
            
        Returns:
            Lista de recomendações ordenadas por score
        """
        if self.jobs_df.empty:
            return []
        
        exclude_applied = exclude_applied or []
        recommendations = []
        
        for idx, job in self.jobs_df.iterrows():
            job_id = job.get('id', str(idx))
            
            # Pular vagas já aplicadas
            if job_id in exclude_applied:
                continue
            
            # Calcular score da recomendação
            score, reasons = self._calculate_job_score(user_profile, job, idx)
            
            # Calcular percentual de match
            match_percentage = min(score / 10.0, 1.0)  # Normalizar para 0-1
            
            recommendation = Recommendation(
                job_id=job_id,
                job_title=job.get('titulo', 'N/A'),
                company=job.get('empresa', 'N/A'),
                score=score,
                reasons=reasons,
                match_percentage=match_percentage,
                job_data=job.to_dict()
            )
            
            recommendations.append(recommendation)
        
        # Ordenar por score e retornar top N
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:n_recommendations]
    
    def _calculate_job_score(self, user_profile: UserProfile, 
                           job: pd.Series, job_idx: int) -> Tuple[float, List[str]]:
        """Calcula score de compatibilidade usuário-vaga"""
        score = 0.0
        reasons = []
        
        # 1. Match de skills/tecnologias
        job_skills = job.get('tecnologias_detectadas', [])
        if job_skills and user_profile.skills:
            skill_overlap = set(user_profile.skills) & set(job_skills)
            skill_score = len(skill_overlap) / len(set(user_profile.skills) | set(job_skills))
            score += skill_score * self.weights['skill_match'] * 10
            
            if skill_overlap:
                reasons.append(f"Match de skills: {', '.join(list(skill_overlap)[:3])}")
        
        # 2. Match de senioridade
        job_seniority = self._extract_seniority(job)
        seniority_score = self._calculate_seniority_match(
            user_profile.seniority_level, job_seniority
        )
        score += seniority_score * self.weights['seniority_match'] * 10
        
        if seniority_score > 0.7:
            reasons.append(f"Nível compatível: {job_seniority}")
        
        # 3. Preferência de localização
        job_location = job.get('localizacao', '').lower()
        location_score = self._calculate_location_match(
            user_profile.preferred_locations, job_location
        )
        score += location_score * self.weights['location_preference'] * 10
        
        if location_score > 0.5:
            reasons.append("Localização preferida")
        
        # 4. Match salarial (se disponível)
        if hasattr(job, 'predicted_salary') and job.predicted_salary:
            salary_score = self._calculate_salary_match(
                user_profile.preferred_salary_min,
                user_profile.preferred_salary_max,
                job.predicted_salary
            )
            score += salary_score * self.weights['salary_match'] * 10
            
            if salary_score > 0.7:
                reasons.append("Faixa salarial compatível")
        
        # 5. Preferência/aversão a empresas
        company = job.get('empresa', '').lower()
        if company in [c.lower() for c in user_profile.preferred_companies]:
            score += 2.0
            reasons.append("Empresa preferida")
        elif company in [c.lower() for c in user_profile.avoided_companies]:
            score -= 3.0
            reasons.append("Empresa evitada")
        
        # 6. Modalidade de trabalho
        work_mode_score = self._calculate_work_mode_match(
            user_profile.work_mode_preference, job_location
        )
        score += work_mode_score * 0.5
        
        if work_mode_score > 0.7:
            reasons.append(f"Modalidade {user_profile.work_mode_preference}")
        
        # 7. Similaridade com vagas que o usuário gostou (se disponível)
        if user_profile.user_id in self._user_interactions:
            collaborative_score = self._calculate_collaborative_score(
                user_profile.user_id, job_idx
            )
            score += collaborative_score * self.weights['content_similarity'] * 10
            
            if collaborative_score > 0.3:
                reasons.append("Similar a vagas que você gostou")
        
        # 8. Análise de sentimento (se disponível)
        if hasattr(job, 'sentiment_analysis'):
            sentiment_score = job.sentiment_analysis.get('overall_score', 5) / 10
            score += sentiment_score * 0.5
            
            if sentiment_score > 0.7:
                reasons.append("Ambiente de trabalho positivo")
        
        # Normalizar score
        score = max(0, min(10, score))
        
        return score, reasons
    
    def _extract_seniority(self, job: pd.Series) -> str:
        """Extrai nível de senioridade da vaga"""
        if hasattr(job, 'ml_seniority'):
            return job.ml_seniority.get('level', 'pleno')
        
        # Fallback: análise simples do título/descrição
        title = job.get('titulo', '').lower()
        description = job.get('descricao', '').lower()
        text = f"{title} {description}"
        
        if any(word in text for word in ['júnior', 'junior', 'jr']):
            return 'junior'
        elif any(word in text for word in ['sênior', 'senior', 'sr']):
            return 'senior'
        elif any(word in text for word in ['especialista', 'arquiteto', 'tech lead']):
            return 'especialista'
        else:
            return 'pleno'
    
    def _calculate_seniority_match(self, user_seniority: str, job_seniority: str) -> float:
        """Calcula compatibilidade de senioridade"""
        seniority_levels = {
            'estagiario': 0,
            'junior': 1,
            'pleno': 2,
            'senior': 3,
            'especialista': 4
        }
        
        user_level = seniority_levels.get(user_seniority.lower(), 2)
        job_level = seniority_levels.get(job_seniority.lower(), 2)
        
        # Match perfeito = 1.0, diferença de 1 nível = 0.7, etc.
        level_diff = abs(user_level - job_level)
        
        if level_diff == 0:
            return 1.0
        elif level_diff == 1:
            return 0.7
        elif level_diff == 2:
            return 0.4
        else:
            return 0.1
    
    def _calculate_location_match(self, preferred_locations: List[str], 
                                job_location: str) -> float:
        """Calcula match de localização"""
        if not preferred_locations:
            return 0.5  # Neutro se não há preferência
        
        job_location = job_location.lower()
        
        for pref_loc in preferred_locations:
            pref_loc = pref_loc.lower()
            
            # Match exato
            if pref_loc in job_location or job_location in pref_loc:
                return 1.0
            
            # Match parcial para estados/cidades
            if any(keyword in job_location for keyword in pref_loc.split()):
                return 0.7
        
        # Verificar se aceita remoto
        if 'remoto' in preferred_locations and ('remoto' in job_location or 'home office' in job_location):
            return 1.0
        
        return 0.2  # Localização não compatível
    
    def _calculate_salary_match(self, min_preferred: float, max_preferred: float,
                              job_salary: Dict) -> float:
        """Calcula match salarial"""
        if not job_salary:
            return 0.5  # Neutro se salário não disponível
        
        job_min = job_salary.get('min', 0)
        job_max = job_salary.get('max', 0)
        
        if job_min == 0 and job_max == 0:
            return 0.5
        
        # Verificar sobreposição de faixas
        overlap_start = max(min_preferred, job_min)
        overlap_end = min(max_preferred, job_max)
        
        if overlap_start <= overlap_end:
            # Há sobreposição
            overlap_size = overlap_end - overlap_start
            user_range = max_preferred - min_preferred
            job_range = job_max - job_min
            
            # Score baseado no tamanho da sobreposição
            score = overlap_size / max(user_range, job_range)
            return min(1.0, score)
        else:
            # Sem sobreposição - calcular distância
            if job_max < min_preferred:
                # Vaga paga menos que o mínimo desejado
                distance = min_preferred - job_max
                return max(0, 1 - distance / min_preferred)
            else:
                # Vaga paga mais que o máximo desejado (ainda é positivo!)
                return 0.8
    
    def _calculate_work_mode_match(self, preferred_mode: str, job_location: str) -> float:
        """Calcula match de modalidade de trabalho"""
        job_location = job_location.lower()
        preferred_mode = preferred_mode.lower()
        
        if preferred_mode == 'remoto':
            if 'remoto' in job_location or 'home office' in job_location:
                return 1.0
            elif 'híbrido' in job_location or 'flexível' in job_location:
                return 0.7
            else:
                return 0.2
        
        elif preferred_mode == 'hibrido':
            if 'híbrido' in job_location or 'flexível' in job_location:
                return 1.0
            elif 'remoto' in job_location or 'presencial' in job_location:
                return 0.6
            else:
                return 0.5
        
        elif preferred_mode == 'presencial':
            if 'remoto' in job_location or 'home office' in job_location:
                return 0.3
            elif 'híbrido' in job_location:
                return 0.7
            else:
                return 1.0
        
        return 0.5  # Default
    
    def _calculate_collaborative_score(self, user_id: str, job_idx: int) -> float:
        """Calcula score baseado em filtragem colaborativa"""
        if user_id not in self._user_interactions:
            return 0.0
        
        user_interactions = self._user_interactions[user_id]
        
        if not user_interactions:
            return 0.0
        
        # Encontrar vagas similares que o usuário gostou
        similar_scores = []
        
        for liked_job_id, interaction_score in user_interactions.items():
            if interaction_score > 2:  # Usuário gostou da vaga
                try:
                    liked_job_idx = int(liked_job_id)
                    if 0 <= liked_job_idx < len(self._similarity_matrix):
                        similarity = self._similarity_matrix[job_idx][liked_job_idx]
                        similar_scores.append(similarity * interaction_score / 5.0)
                except (ValueError, IndexError):
                    continue
        
        return np.mean(similar_scores) if similar_scores else 0.0
    
    def get_similar_jobs(self, job_id: str, n_similar: int = 5) -> List[Tuple[str, float]]:
        """Encontra vagas similares a uma vaga específica"""
        try:
            job_idx = int(job_id)
            if 0 <= job_idx < len(self._similarity_matrix):
                similarities = self._similarity_matrix[job_idx]
                
                # Ordenar por similaridade (excluindo a própria vaga)
                similar_indices = np.argsort(similarities)[::-1][1:n_similar+1]
                
                similar_jobs = []
                for idx in similar_indices:
                    similarity_score = similarities[idx]
                    job = self.jobs_df.iloc[idx]
                    similar_jobs.append((
                        f"{job.get('titulo', 'N/A')} @ {job.get('empresa', 'N/A')}",
                        similarity_score
                    ))
                
                return similar_jobs
        except (ValueError, IndexError):
            pass
        
        return []
    
    def update_user_interaction(self, user_id: str, job_id: str, action: str):
        """Atualiza interação do usuário com uma vaga"""
        action_scores = {
            'view': 1,
            'like': 3,
            'apply': 5,
            'dislike': -2,
            'reject': -1
        }
        
        score = action_scores.get(action, 0)
        self._user_interactions[user_id][job_id] = score
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Retorna estatísticas do usuário"""
        if user_id not in self._user_interactions:
            return {'error': 'Usuário não encontrado'}
        
        interactions = self._user_interactions[user_id]
        
        return {
            'total_interactions': len(interactions),
            'positive_interactions': len([s for s in interactions.values() if s > 0]),
            'negative_interactions': len([s for s in interactions.values() if s < 0]),
            'avg_interaction_score': np.mean(list(interactions.values())),
            'most_liked_jobs': [
                job_id for job_id, score in interactions.items() 
                if score >= 4
            ]
        }


# Exemplo de uso
if __name__ == "__main__":
    # Criar recomendador
    recommender = JobRecommender()
    
    # Dados de exemplo
    jobs_example = [
        {
            'id': '1',
            'titulo': 'Desenvolvedor Python Sênior',
            'empresa': 'TechCorp',
            'descricao': 'Vaga para desenvolvedor Python com Django e AWS',
            'tecnologias_detectadas': ['Python', 'Django', 'AWS'],
            'localizacao': 'São Paulo - SP (Remoto)',
            'predicted_salary': {'min': 8000, 'max': 12000}
        },
        {
            'id': '2', 
            'titulo': 'Full Stack Developer Pleno',
            'empresa': 'StartupXYZ',
            'descricao': 'React, Node.js, MongoDB para aplicação web',
            'tecnologias_detectadas': ['React', 'Node.js', 'MongoDB'],
            'localizacao': 'Rio de Janeiro - RJ',
            'predicted_salary': {'min': 6000, 'max': 9000}
        }
    ]
    
    # Perfil do usuário
    user = UserProfile(
        user_id='user123',
        skills=['Python', 'Django', 'PostgreSQL'],
        experience_years=5,
        seniority_level='senior',
        preferred_locations=['São Paulo', 'remoto'],
        preferred_salary_min=8000,
        preferred_salary_max=15000,
        preferred_companies=['TechCorp'],
        avoided_companies=[],
        work_mode_preference='remoto'
    )
    
    # Treinar sistema
    recommender.fit(jobs_example)
    
    # Gerar recomendações
    recommendations = recommender.recommend(user, n_recommendations=5)
    
    print("=== Recomendações ===")
    for rec in recommendations:
        print(f"{rec}")
        print(f"  Score: {rec.score:.2f}")
        print(f"  Razões: {', '.join(rec.reasons)}")
        print()