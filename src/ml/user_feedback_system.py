"""
Sistema de Feedback e Aprendizado do Usuário
===========================================

Sistema que aprende com as interações do usuário para melhorar
as recomendações de vagas ao longo do tempo.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics
from dataclasses import dataclass, asdict


@dataclass
class UserInteraction:
    """Representa uma interação do usuário com uma vaga"""
    user_id: str
    job_id: str
    job_title: str
    interaction_type: str  # view, like, dislike, apply, interview, hired, rejected
    timestamp: str
    match_score: float
    skills_overlap: List[str]
    metadata: Dict


@dataclass
class UserPreferenceLearning:
    """Aprendizado das preferências do usuário"""
    user_id: str
    preferred_skills: Dict[str, float]  # skill -> preference score
    preferred_companies: Dict[str, float]
    preferred_locations: Dict[str, float] 
    preferred_salary_range: Dict[str, float]
    preferred_seniority: str
    interaction_patterns: Dict[str, float]
    learning_confidence: float


class UserFeedbackSystem:
    """
    Sistema que aprende com feedback do usuário
    
    Funcionalidades:
    - Rastreamento de interações detalhadas
    - Aprendizado de preferências implícitas
    - Ajuste automático de pesos de matching
    - Detecção de padrões de comportamento
    - Melhoria contínua das recomendações
    """
    
    def __init__(self, data_file: str = "data/ml/user_feedback.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Criar diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Carregar dados históricos
        self.feedback_data = self._load_feedback_data()
        
        # Tipos de interação e seus pesos para learning
        self.interaction_weights = {
            'view': 0.1,
            'like': 0.3,
            'dislike': -0.2,
            'apply': 0.7,
            'interview': 0.9,
            'hired': 1.0,
            'rejected': -0.1
        }
        
        # Cache de preferências aprendidas
        self.user_preferences_cache = {}
    
    def _load_feedback_data(self) -> Dict:
        """Carrega dados históricos de feedback"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "interactions": [],
            "user_preferences": {},
            "learning_stats": {},
            "model_adjustments": [],
            "last_update": None
        }
    
    def _save_feedback_data(self):
        """Salva dados de feedback"""
        try:
            self.feedback_data["last_update"] = datetime.now().isoformat()
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados de feedback: {e}")
    
    def record_interaction(self, user_id: str, job_data: Dict, 
                          interaction_type: str, match_score: float,
                          skills_overlap: List[str] = None, 
                          metadata: Dict = None) -> UserInteraction:
        """
        Registra uma interação do usuário
        
        Args:
            user_id: ID do usuário
            job_data: Dados da vaga
            interaction_type: Tipo de interação
            match_score: Score de matching original
            skills_overlap: Skills em comum
            metadata: Metadados adicionais
            
        Returns:
            Objeto de interação criado
        """
        interaction = UserInteraction(
            user_id=user_id,
            job_id=job_data.get('job_id', str(hash(str(job_data)))),
            job_title=job_data.get('title', job_data.get('titulo', '')),
            interaction_type=interaction_type,
            timestamp=datetime.now().isoformat(),
            match_score=match_score,
            skills_overlap=skills_overlap or [],
            metadata={
                'company': job_data.get('company', job_data.get('empresa', '')),
                'location': job_data.get('location', job_data.get('localizacao', '')),
                'seniority': job_data.get('seniority', ''),
                'salary_info': job_data.get('salary_info', {}),
                'job_skills': job_data.get('skills', []),
                **(metadata or {})
            }
        )
        
        # Adicionar aos dados de feedback
        self.feedback_data["interactions"].append(asdict(interaction))
        
        # Atualizar preferências do usuário
        self._update_user_preferences(interaction)
        
        # Salvar dados
        self._save_feedback_data()
        
        return interaction
    
    def _update_user_preferences(self, interaction: UserInteraction):
        """Atualiza preferências do usuário baseado na interação"""
        user_id = interaction.user_id
        
        if user_id not in self.feedback_data["user_preferences"]:
            self.feedback_data["user_preferences"][user_id] = {
                'preferred_skills': {},
                'preferred_companies': {},
                'preferred_locations': {},
                'preferred_salary_ranges': {},
                'interaction_patterns': {},
                'total_interactions': 0,
                'learning_confidence': 0.0
            }
        
        prefs = self.feedback_data["user_preferences"][user_id]
        weight = self.interaction_weights.get(interaction.interaction_type, 0.1)
        
        # Atualizar preferências de skills
        for skill in interaction.skills_overlap:
            current_score = prefs['preferred_skills'].get(skill, 0.0)
            prefs['preferred_skills'][skill] = current_score + weight
        
        # Atualizar preferências de empresa
        company = interaction.metadata.get('company', '')
        if company:
            current_score = prefs['preferred_companies'].get(company, 0.0)
            prefs['preferred_companies'][company] = current_score + weight
        
        # Atualizar preferências de localização
        location = interaction.metadata.get('location', '')
        if location:
            current_score = prefs['preferred_locations'].get(location, 0.0)
            prefs['preferred_locations'][location] = current_score + weight
        
        # Atualizar padrões de interação
        prefs['interaction_patterns'][interaction.interaction_type] = \
            prefs['interaction_patterns'].get(interaction.interaction_type, 0) + 1
        
        prefs['total_interactions'] += 1
        
        # Calcular confiança do aprendizado
        prefs['learning_confidence'] = min(1.0, prefs['total_interactions'] / 20.0)
        
        # Limpar cache
        if user_id in self.user_preferences_cache:
            del self.user_preferences_cache[user_id]
    
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferenceLearning]:
        """
        Obtém preferências aprendidas do usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Preferências aprendidas ou None se não há dados suficientes
        """
        if user_id in self.user_preferences_cache:
            return self.user_preferences_cache[user_id]
        
        if user_id not in self.feedback_data["user_preferences"]:
            return None
        
        prefs_data = self.feedback_data["user_preferences"][user_id]
        
        # Só retornar se há confiança mínima
        if prefs_data['learning_confidence'] < 0.1:
            return None
        
        # Normalizar scores de skills
        skills_scores = prefs_data['preferred_skills']
        if skills_scores:
            max_score = max(skills_scores.values())
            if max_score > 0:
                skills_scores = {
                    skill: score / max_score 
                    for skill, score in skills_scores.items()
                }
        
        # Criar objeto de preferências
        preferences = UserPreferenceLearning(
            user_id=user_id,
            preferred_skills=skills_scores,
            preferred_companies=prefs_data['preferred_companies'],
            preferred_locations=prefs_data['preferred_locations'],
            preferred_salary_range=prefs_data.get('preferred_salary_ranges', {}),
            preferred_seniority=self._infer_preferred_seniority(user_id),
            interaction_patterns=prefs_data['interaction_patterns'],
            learning_confidence=prefs_data['learning_confidence']
        )
        
        # Cache para performance
        self.user_preferences_cache[user_id] = preferences
        return preferences
    
    def _infer_preferred_seniority(self, user_id: str) -> str:
        """Infere senioridade preferida baseada em interações positivas"""
        positive_interactions = [
            interaction for interaction in self.feedback_data["interactions"]
            if (interaction['user_id'] == user_id and 
                interaction['interaction_type'] in ['like', 'apply', 'interview', 'hired'])
        ]
        
        if not positive_interactions:
            return 'pleno'  # Default
        
        # Contar senioridades das interações positivas
        seniority_counts = Counter(
            interaction['metadata'].get('seniority', 'pleno')
            for interaction in positive_interactions
        )
        
        return seniority_counts.most_common(1)[0][0] if seniority_counts else 'pleno'
    
    def adjust_matching_weights(self, user_id: str, base_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Ajusta pesos de matching baseado nas preferências do usuário
        
        Args:
            user_id: ID do usuário
            base_weights: Pesos base do algoritmo
            
        Returns:
            Pesos ajustados para o usuário
        """
        preferences = self.get_user_preferences(user_id)
        
        if not preferences or preferences.learning_confidence < 0.3:
            return base_weights.copy()
        
        adjusted_weights = base_weights.copy()
        confidence_factor = preferences.learning_confidence
        
        # Analisar padrões de interação para ajustar pesos
        interaction_patterns = preferences.interaction_patterns
        total_interactions = sum(interaction_patterns.values())
        
        if total_interactions == 0:
            return adjusted_weights
        
        # Se usuário demonstra alta importância para skills (muitas curtidas/aplicações)
        positive_rate = (
            interaction_patterns.get('like', 0) + 
            interaction_patterns.get('apply', 0)
        ) / total_interactions
        
        if positive_rate > 0.6:  # Usuário é seletivo
            # Aumentar peso de skills exatas
            adjusted_weights['skills_exact'] *= (1 + confidence_factor * 0.3)
            adjusted_weights['skills_semantic'] *= (1 + confidence_factor * 0.2)
        
        # Se usuário rejeita muitas vagas, aumentar peso de preferências
        dislike_rate = interaction_patterns.get('dislike', 0) / total_interactions
        if dislike_rate > 0.3:
            # Aumentar peso de compatibilidades específicas
            adjusted_weights['company_type'] *= (1 + confidence_factor * 0.4)
            adjusted_weights['location'] *= (1 + confidence_factor * 0.3)
        
        # Normalizar pesos para manter soma
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {
                key: value / total_weight 
                for key, value in adjusted_weights.items()
            }
        
        return adjusted_weights
    
    def get_personalized_skill_boost(self, user_id: str, job_skills: List[str]) -> float:
        """
        Calcula boost personalizado baseado nas skills preferidas do usuário
        
        Args:
            user_id: ID do usuário
            job_skills: Skills da vaga
            
        Returns:
            Fator de boost (0.0 a 1.0)
        """
        preferences = self.get_user_preferences(user_id)
        
        if not preferences or not preferences.preferred_skills:
            return 0.0
        
        # Calcular boost baseado em skills preferidas
        boost_score = 0.0
        preferred_skills = preferences.preferred_skills
        
        for skill in job_skills:
            skill_lower = skill.lower()
            if skill_lower in preferred_skills:
                boost_score += preferred_skills[skill_lower]
        
        # Normalizar pelo número de skills
        if job_skills:
            boost_score = boost_score / len(job_skills)
        
        # Aplicar confiança do aprendizado
        boost_score *= preferences.learning_confidence
        
        return min(1.0, boost_score)
    
    def analyze_user_behavior(self, user_id: str) -> Dict:
        """
        Analisa comportamento do usuário para insights
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Análise comportamental
        """
        user_interactions = [
            interaction for interaction in self.feedback_data["interactions"]
            if interaction['user_id'] == user_id
        ]
        
        if not user_interactions:
            return {'status': 'insufficient_data'}
        
        # Análise temporal
        timestamps = [
            datetime.fromisoformat(interaction['timestamp'].replace('Z', '+00:00'))
            for interaction in user_interactions
        ]
        
        # Padrões de interação
        interaction_types = Counter(
            interaction['interaction_type'] 
            for interaction in user_interactions
        )
        
        # Evolução do score de matching
        scores = [interaction['match_score'] for interaction in user_interactions]
        avg_score = statistics.mean(scores) if scores else 0
        
        # Skills mais interagidas
        all_skills = []
        for interaction in user_interactions:
            all_skills.extend(interaction.get('skills_overlap', []))
        
        popular_skills = Counter(all_skills).most_common(10)
        
        # Análise de conversão
        total_views = interaction_types.get('view', 0)
        total_applies = interaction_types.get('apply', 0)
        conversion_rate = (total_applies / total_views) if total_views > 0 else 0
        
        return {
            'status': 'analyzed',
            'total_interactions': len(user_interactions),
            'interaction_breakdown': dict(interaction_types),
            'avg_match_score': avg_score,
            'conversion_rate': conversion_rate,
            'popular_skills': popular_skills,
            'activity_period': {
                'first_interaction': min(timestamps).isoformat(),
                'last_interaction': max(timestamps).isoformat(),
                'days_active': (max(timestamps) - min(timestamps)).days
            },
            'user_preferences_confidence': self.get_user_preferences(user_id).learning_confidence if self.get_user_preferences(user_id) else 0
        }
    
    def get_recommendation_explanation(self, user_id: str, job_data: Dict, 
                                     base_score: float, adjusted_score: float) -> str:
        """
        Gera explicação personalizada da recomendação
        
        Args:
            user_id: ID do usuário
            job_data: Dados da vaga
            base_score: Score base
            adjusted_score: Score ajustado
            
        Returns:
            Explicação personalizada
        """
        preferences = self.get_user_preferences(user_id)
        
        if not preferences:
            return "Recomendação baseada em compatibilidade geral"
        
        explanations = []
        
        # Verificar skills preferidas
        job_skills = job_data.get('skills', [])
        preferred_skills = preferences.preferred_skills
        
        matching_preferred_skills = [
            skill for skill in job_skills
            if skill.lower() in preferred_skills
        ]
        
        if matching_preferred_skills:
            explanations.append(
                f"Contém suas skills preferidas: {', '.join(matching_preferred_skills[:3])}"
            )
        
        # Verificar empresa preferida
        company = job_data.get('company', '')
        if company and company in preferences.preferred_companies:
            explanations.append(f"Empresa do seu interesse: {company}")
        
        # Verificar localização
        location = job_data.get('location', '')
        if location and location in preferences.preferred_locations:
            explanations.append(f"Localização preferida: {location}")
        
        # Score improvement
        if adjusted_score > base_score:
            improvement = ((adjusted_score - base_score) / base_score) * 100
            explanations.append(f"Personalizado para você (+{improvement:.0f}%)")
        
        if explanations:
            return "Recomendado porque: " + "; ".join(explanations)
        else:
            return "Boa compatibilidade geral com seu perfil"
    
    def get_learning_stats(self) -> Dict:
        """Retorna estatísticas do sistema de aprendizado"""
        total_interactions = len(self.feedback_data["interactions"])
        users_with_data = len(self.feedback_data["user_preferences"])
        
        # Estatísticas de interação
        if total_interactions > 0:
            interaction_types = Counter(
                interaction['interaction_type'] 
                for interaction in self.feedback_data["interactions"]
            )
            
            # Usuários com aprendizado suficiente
            confident_users = sum(
                1 for prefs in self.feedback_data["user_preferences"].values()
                if prefs['learning_confidence'] > 0.3
            )
        else:
            interaction_types = {}
            confident_users = 0
        
        return {
            'total_interactions': total_interactions,
            'users_with_data': users_with_data,
            'confident_users': confident_users,
            'interaction_breakdown': dict(interaction_types),
            'learning_effectiveness': confident_users / users_with_data if users_with_data > 0 else 0,
            'avg_interactions_per_user': total_interactions / users_with_data if users_with_data > 0 else 0
        }


# Instância global do sistema de feedback
user_feedback_system = UserFeedbackSystem()