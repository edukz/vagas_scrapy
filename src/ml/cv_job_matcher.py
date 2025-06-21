"""
Sistema Integrado de Matching CV-Vagas
=====================================

Sistema avançado que integra análise de CV com recomendação de vagas
usando algoritmos de Machine Learning e NLP para matching inteligente.
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import re
from datetime import datetime


@dataclass
class MatchResult:
    """Resultado de um matching CV-Vaga"""
    job_id: str
    job_title: str
    company: str
    overall_score: float
    breakdown_scores: Dict[str, float]
    matched_skills: List[str]
    missing_skills: List[str]
    salary_compatibility: float
    recommendation_reason: str


class AdvancedCVJobMatcher:
    """
    Matcher avançado que integra análise de CV com vagas
    
    Funcionalidades:
    - Matching semântico usando TF-IDF e cosine similarity
    - Análise de compatibilidade multi-dimensional
    - Learning baseado em feedback do usuário
    - Scoring ponderado e explicável
    - Cache inteligente para performance
    """
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.scaler = StandardScaler()
        
        # Inicializar analisadores existentes
        self._initialize_analyzers()
        
        # Pesos do algoritmo de matching
        self.weights = {
            'skills_semantic': 0.25,     # Similaridade semântica de skills
            'skills_exact': 0.20,       # Match exato de skills
            'seniority': 0.15,          # Compatibilidade de senioridade
            'salary': 0.15,             # Compatibilidade salarial
            'location': 0.10,           # Preferência de localização
            'company_type': 0.08,       # Tipo de empresa
            'work_mode': 0.07           # Modo de trabalho (remoto/híbrido)
        }
        
        # Cache para performance
        self.cv_cache = {}
        self.job_cache = {}
        
        # Histórico de interações para learning
        self.interaction_history = []
    
    def _initialize_analyzers(self):
        """Inicializa analisadores existentes"""
        try:
            from src.ml.models.simple_cv_analyzer import SimpleCVAnalyzer
            from src.business_intelligence.skills_demand_analyzer import skills_demand_analyzer
            from src.business_intelligence.salary_trend_analyzer import salary_trend_analyzer
            
            self.cv_analyzer = SimpleCVAnalyzer()
            self.skills_analyzer = skills_demand_analyzer
            self.salary_analyzer = salary_trend_analyzer
            
        except ImportError as e:
            print(f"Aviso: Alguns analisadores não disponíveis: {e}")
            self.cv_analyzer = None
            self.skills_analyzer = None
            self.salary_analyzer = None
    
    def analyze_cv_for_matching(self, cv_file_path: str, user_id: str) -> Dict:
        """
        Analisa CV e prepara dados para matching
        
        Args:
            cv_file_path: Caminho para o arquivo de CV
            user_id: ID do usuário
            
        Returns:
            Dados estruturados do CV para matching
        """
        if user_id in self.cv_cache:
            return self.cv_cache[user_id]
        
        if not self.cv_analyzer:
            raise Exception("CV Analyzer não disponível")
        
        # Análise completa do CV
        cv_result = self.cv_analyzer.analyze_cv(cv_file_path, user_id)
        
        # Estruturar dados para matching
        cv_data = {
            'user_id': user_id,
            'personal_info': cv_result.personal_info,
            'skills': {
                'technical': cv_result.skills.get('technical', []),
                'soft': cv_result.skills.get('soft', []),
                'by_category': cv_result.skills.get('by_category', {})
            },
            'experience': cv_result.experience,
            'seniority': cv_result.seniority_level,
            'salary_range': cv_result.estimated_salary_range,
            'preferences': cv_result.preferences,
            'confidence': cv_result.confidence_score,
            
            # Dados calculados para matching
            'skills_text': self._create_skills_text(cv_result.skills),
            'experience_text': self._create_experience_text(cv_result.experience),
            'full_profile_text': self._create_full_profile_text(cv_result)
        }
        
        # Cache para performance
        self.cv_cache[user_id] = cv_data
        return cv_data
    
    def _create_skills_text(self, skills: Dict) -> str:
        """Cria texto unificado das skills para análise semântica"""
        all_skills = []
        
        # Skills técnicas
        technical = skills.get('technical', [])
        all_skills.extend(technical)
        
        # Skills por categoria
        by_category = skills.get('by_category', {})
        for category, skill_list in by_category.items():
            all_skills.extend(skill_list)
        
        # Skills soft
        soft = skills.get('soft', [])
        all_skills.extend(soft)
        
        return ' '.join(set(all_skills))  # Remove duplicatas
    
    def _create_experience_text(self, experience: Dict) -> str:
        """Cria texto da experiência para análise"""
        exp_text = []
        
        if experience.get('current_position'):
            exp_text.append(experience['current_position'])
        
        if experience.get('companies'):
            exp_text.extend(experience['companies'])
        
        if experience.get('total_years'):
            exp_text.append(f"{experience['total_years']} anos experiencia")
        
        return ' '.join(exp_text)
    
    def _create_full_profile_text(self, cv_result) -> str:
        """Cria texto completo do perfil para análise semântica"""
        profile_parts = []
        
        # Skills
        skills_text = self._create_skills_text(cv_result.skills)
        if skills_text:
            profile_parts.append(skills_text)
        
        # Experiência
        exp_text = self._create_experience_text(cv_result.experience)
        if exp_text:
            profile_parts.append(exp_text)
        
        # Senioridade
        if cv_result.seniority_level:
            profile_parts.append(cv_result.seniority_level)
        
        # Educação
        if cv_result.education.get('degree'):
            profile_parts.append(cv_result.education['degree'])
        
        return ' '.join(profile_parts)
    
    def prepare_job_for_matching(self, job: Dict) -> Dict:
        """
        Prepara dados da vaga para matching
        
        Args:
            job: Dados da vaga
            
        Returns:
            Dados estruturados da vaga para matching
        """
        job_id = job.get('id', str(hash(str(job))))
        
        if job_id in self.job_cache:
            return self.job_cache[job_id]
        
        # Extrair e processar skills da vaga
        job_skills = self._extract_job_skills(job)
        
        # Determinar senioridade da vaga
        job_seniority = self._extract_job_seniority(job)
        
        # Processar localização
        location_info = self._process_job_location(job)
        
        # Estimativa salarial se não disponível
        salary_info = self._get_job_salary_info(job)
        
        job_data = {
            'job_id': job_id,
            'title': job.get('titulo', ''),
            'company': job.get('empresa', ''),
            'location': job.get('localizacao', ''),
            'description': job.get('descricao', ''),
            'requirements': job.get('requisitos', ''),
            
            # Dados processados
            'skills': job_skills,
            'seniority': job_seniority,
            'location_info': location_info,
            'salary_info': salary_info,
            
            # Textos para análise semântica
            'skills_text': ' '.join(job_skills),
            'full_text': self._create_job_full_text(job),
            'requirements_text': self._create_requirements_text(job)
        }
        
        # Cache
        self.job_cache[job_id] = job_data
        return job_data
    
    def _extract_job_skills(self, job: Dict) -> List[str]:
        """Extrai skills da descrição da vaga"""
        if self.skills_analyzer:
            # Usar analisador existente
            full_text = f"{job.get('titulo', '')} {job.get('descricao', '')} {job.get('requisitos', '')}"
            return self.skills_analyzer.extract_skills_from_text(full_text)
        
        # Fallback: usar skills já detectadas
        return job.get('tecnologias_detectadas', [])
    
    def _extract_job_seniority(self, job: Dict) -> str:
        """Extrai nível de senioridade da vaga"""
        if 'nivel_categorizado' in job:
            return job['nivel_categorizado']
        
        # Extrair do título
        title = job.get('titulo', '').lower()
        if any(word in title for word in ['junior', 'jr', 'trainee', 'estagiario']):
            return 'junior'
        elif any(word in title for word in ['senior', 'sr', 'especialista']):
            return 'senior'
        elif any(word in title for word in ['pleno', 'mid', 'middle']):
            return 'pleno'
        else:
            return 'pleno'  # Default
    
    def _process_job_location(self, job: Dict) -> Dict:
        """Processa informações de localização da vaga"""
        location = job.get('localizacao', '').lower()
        
        return {
            'is_remote': any(term in location for term in ['remoto', 'home office']),
            'is_hybrid': 'hibrido' in location or 'híbrido' in location,
            'city': self._extract_city(location),
            'state': self._extract_state(location)
        }
    
    def _extract_city(self, location: str) -> str:
        """Extrai cidade da localização"""
        # Mapeamento básico de cidades
        cities = {
            'sp': 'São Paulo',
            'rj': 'Rio de Janeiro', 
            'bh': 'Belo Horizonte',
            'curitiba': 'Curitiba',
            'porto alegre': 'Porto Alegre'
        }
        
        location_lower = location.lower()
        for key, city in cities.items():
            if key in location_lower:
                return city
        
        return 'Outras'
    
    def _extract_state(self, location: str) -> str:
        """Extrai estado da localização"""
        states = {
            'sp': 'São Paulo',
            'rj': 'Rio de Janeiro',
            'mg': 'Minas Gerais',
            'pr': 'Paraná',
            'rs': 'Rio Grande do Sul'
        }
        
        location_lower = location.lower()
        for key, state in states.items():
            if key in location_lower:
                return state
        
        return 'Outros'
    
    def _get_job_salary_info(self, job: Dict) -> Dict:
        """Obtém informações salariais da vaga"""
        if 'predicted_salary' in job:
            return job['predicted_salary']
        
        # Tentar extrair do texto
        salary_text = job.get('salario', '')
        if salary_text and salary_text.lower() not in ['não informado', 'a combinar']:
            # Usar analisador de salários se disponível
            if self.salary_analyzer:
                salary_range = self.salary_analyzer.extract_salary_from_text(salary_text)
                if salary_range:
                    return {
                        'min': salary_range[0],
                        'max': salary_range[1],
                        'median': (salary_range[0] + salary_range[1]) / 2
                    }
        
        # Estimativa baseada em senioridade se não encontrar
        seniority = self._extract_job_seniority(job)
        salary_estimates = {
            'junior': {'min': 3000, 'max': 6000, 'median': 4500},
            'pleno': {'min': 6000, 'max': 12000, 'median': 9000},
            'senior': {'min': 12000, 'max': 25000, 'median': 18000}
        }
        
        return salary_estimates.get(seniority, salary_estimates['pleno'])
    
    def _create_job_full_text(self, job: Dict) -> str:
        """Cria texto completo da vaga para análise"""
        parts = []
        
        if job.get('titulo'):
            parts.append(job['titulo'])
        
        if job.get('descricao'):
            parts.append(job['descricao'])
        
        if job.get('requisitos'):
            parts.append(job['requisitos'])
        
        return ' '.join(parts)
    
    def _create_requirements_text(self, job: Dict) -> str:
        """Cria texto dos requisitos da vaga"""
        return job.get('requisitos', job.get('descricao', ''))
    
    def calculate_match_score(self, cv_data: Dict, job_data: Dict) -> MatchResult:
        """
        Calcula score de compatibilidade entre CV e vaga
        
        Args:
            cv_data: Dados processados do CV
            job_data: Dados processados da vaga
            
        Returns:
            Resultado detalhado do matching
        """
        scores = {}
        
        # 1. Similaridade semântica de skills
        scores['skills_semantic'] = self._calculate_semantic_similarity(
            cv_data['skills_text'], job_data['skills_text']
        )
        
        # 2. Match exato de skills
        scores['skills_exact'] = self._calculate_exact_skills_match(
            cv_data['skills']['technical'], job_data['skills']
        )
        
        # 3. Compatibilidade de senioridade
        scores['seniority'] = self._calculate_seniority_compatibility(
            cv_data['seniority'], job_data['seniority']
        )
        
        # 4. Compatibilidade salarial
        scores['salary'] = self._calculate_salary_compatibility(
            cv_data['salary_range'], job_data['salary_info']
        )
        
        # 5. Compatibilidade de localização
        scores['location'] = self._calculate_location_compatibility(
            cv_data['preferences'], job_data['location_info']
        )
        
        # 6. Tipo de empresa (se disponível)
        scores['company_type'] = self._calculate_company_compatibility(
            cv_data.get('preferences', {}), job_data['company']
        )
        
        # 7. Modo de trabalho
        scores['work_mode'] = self._calculate_work_mode_compatibility(
            cv_data['preferences'], job_data['location_info']
        )
        
        # Calcular score final ponderado
        overall_score = sum(
            scores[factor] * weight 
            for factor, weight in self.weights.items()
            if factor in scores
        )
        
        # Identificar skills em comum e faltantes
        matched_skills = list(set(cv_data['skills']['technical']) & set(job_data['skills']))
        missing_skills = list(set(job_data['skills']) - set(cv_data['skills']['technical']))
        
        # Gerar razão da recomendação
        recommendation_reason = self._generate_recommendation_reason(
            scores, matched_skills, missing_skills
        )
        
        return MatchResult(
            job_id=job_data['job_id'],
            job_title=job_data['title'],
            company=job_data['company'],
            overall_score=overall_score,
            breakdown_scores=scores,
            matched_skills=matched_skills,
            missing_skills=missing_skills[:5],  # Top 5 missing
            salary_compatibility=scores['salary'],
            recommendation_reason=recommendation_reason
        )
    
    def _calculate_semantic_similarity(self, cv_skills_text: str, job_skills_text: str) -> float:
        """Calcula similaridade semântica entre texts de skills"""
        if not cv_skills_text or not job_skills_text:
            return 0.0
        
        try:
            # Criar corpus
            corpus = [cv_skills_text, job_skills_text]
            
            # Calcular TF-IDF
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Calcular similaridade coseno
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception:
            return 0.0
    
    def _calculate_exact_skills_match(self, cv_skills: List[str], job_skills: List[str]) -> float:
        """Calcula match exato de skills"""
        if not cv_skills or not job_skills:
            return 0.0
        
        cv_skills_set = set(skill.lower() for skill in cv_skills)
        job_skills_set = set(skill.lower() for skill in job_skills)
        
        intersection = cv_skills_set & job_skills_set
        union = cv_skills_set | job_skills_set
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_seniority_compatibility(self, cv_seniority: str, job_seniority: str) -> float:
        """Calcula compatibilidade de senioridade"""
        seniority_levels = {
            'estagiario': 1,
            'junior': 2, 
            'pleno': 3,
            'senior': 4,
            'especialista': 5,
            'lead': 5,
            'gerente': 6
        }
        
        cv_level = seniority_levels.get(cv_seniority.lower(), 3)
        job_level = seniority_levels.get(job_seniority.lower(), 3)
        
        # Compatibilidade baseada na diferença de níveis
        diff = abs(cv_level - job_level)
        
        if diff == 0:
            return 1.0  # Match perfeito
        elif diff == 1:
            return 0.8  # Compatível
        elif diff == 2:
            return 0.5  # Aceitável
        else:
            return 0.2  # Pouco compatível
    
    def _calculate_salary_compatibility(self, cv_salary: Dict, job_salary: Dict) -> float:
        """Calcula compatibilidade salarial"""
        if not cv_salary or not job_salary:
            return 0.5  # Neutro se não há informação
        
        cv_median = cv_salary.get('median', cv_salary.get('max', 0))
        job_median = job_salary.get('median', job_salary.get('max', 0))
        
        if cv_median == 0 or job_median == 0:
            return 0.5
        
        # Calcular proporção
        ratio = min(cv_median, job_median) / max(cv_median, job_median)
        
        # Bonus se salário da vaga é maior que expectativa
        if job_median > cv_median:
            ratio = min(1.0, ratio * 1.2)
        
        return ratio
    
    def _calculate_location_compatibility(self, cv_preferences: Dict, job_location: Dict) -> float:
        """Calcula compatibilidade de localização"""
        # Se trabalho é remoto, alta compatibilidade
        if job_location.get('is_remote'):
            return 1.0
        
        # Se é híbrido, boa compatibilidade
        if job_location.get('is_hybrid'):
            return 0.8
        
        # Verificar se está na mesma cidade/estado (simulado)
        # Em implementação real, usar localização do CV
        return 0.6  # Compatibilidade média para presencial
    
    def _calculate_company_compatibility(self, cv_preferences: Dict, company: str) -> float:
        """Calcula compatibilidade com tipo de empresa"""
        # Implementação básica - pode ser expandida
        return 0.7  # Neutro
    
    def _calculate_work_mode_compatibility(self, cv_preferences: Dict, job_location: Dict) -> float:
        """Calcula compatibilidade de modo de trabalho"""
        # Preferência por remoto é assumida como alta
        if job_location.get('is_remote'):
            return 1.0
        elif job_location.get('is_hybrid'):
            return 0.8
        else:
            return 0.6
    
    def _generate_recommendation_reason(self, scores: Dict, matched_skills: List[str], 
                                      missing_skills: List[str]) -> str:
        """Gera explicação da recomendação"""
        reasons = []
        
        if matched_skills:
            reasons.append(f"Skills em comum: {', '.join(matched_skills[:3])}")
        
        if scores.get('salary', 0) > 0.8:
            reasons.append("Excelente compatibilidade salarial")
        
        if scores.get('seniority', 0) > 0.8:
            reasons.append("Nível de senioridade compatível")
        
        if missing_skills:
            reasons.append(f"Oportunidade de aprender: {', '.join(missing_skills[:2])}")
        
        return "; ".join(reasons) if reasons else "Compatibilidade geral boa"
    
    def generate_detailed_analysis(self, match_result: MatchResult, cv_data: Dict, job_data: Dict) -> Dict:
        """
        Gera análise detalhada e insights específicos para uma recomendação
        
        Args:
            match_result: Resultado do matching
            cv_data: Dados do CV
            job_data: Dados da vaga
            
        Returns:
            Análise detalhada com insights específicos
        """
        analysis = {
            'compatibility_breakdown': self._generate_compatibility_breakdown(match_result.breakdown_scores),
            'skills_analysis': self._generate_skills_analysis(cv_data, job_data, match_result),
            'career_progression': self._analyze_career_progression(cv_data, job_data),
            'learning_opportunities': self._identify_learning_opportunities(cv_data, job_data),
            'risk_assessment': self._assess_application_risks(cv_data, job_data, match_result),
            'negotiation_insights': self._generate_negotiation_insights(cv_data, job_data),
            'preparation_tips': self._generate_preparation_tips(cv_data, job_data, match_result),
            'timeline_expectations': self._estimate_application_timeline(cv_data, job_data)
        }
        
        return analysis
    
    def _generate_compatibility_breakdown(self, scores: Dict) -> Dict:
        """Análise detalhada da compatibilidade"""
        breakdown = {}
        
        for factor, score in scores.items():
            percentage = score * 100
            
            if factor == 'skills_semantic':
                breakdown['Compatibilidade Técnica'] = {
                    'score': f"{percentage:.1f}%",
                    'level': self._get_score_level(score),
                    'explanation': self._explain_technical_compatibility(score)
                }
            elif factor == 'skills_exact':
                breakdown['Match de Tecnologias'] = {
                    'score': f"{percentage:.1f}%",
                    'level': self._get_score_level(score),
                    'explanation': self._explain_tech_match(score)
                }
            elif factor == 'seniority':
                breakdown['Nível Profissional'] = {
                    'score': f"{percentage:.1f}%",
                    'level': self._get_score_level(score),
                    'explanation': self._explain_seniority_match(score)
                }
            elif factor == 'salary':
                breakdown['Expectativa Salarial'] = {
                    'score': f"{percentage:.1f}%",
                    'level': self._get_score_level(score),
                    'explanation': self._explain_salary_compatibility(score)
                }
            elif factor == 'location':
                breakdown['Localização e Flexibilidade'] = {
                    'score': f"{percentage:.1f}%",
                    'level': self._get_score_level(score),
                    'explanation': self._explain_location_compatibility(score)
                }
        
        return breakdown
    
    def _get_score_level(self, score: float) -> str:
        """Converte score numérico em nível descritivo"""
        if score >= 0.85:
            return "EXCELENTE"
        elif score >= 0.70:
            return "MUITO BOM"
        elif score >= 0.55:
            return "BOM"
        elif score >= 0.40:
            return "REGULAR"
        else:
            return "BAIXO"
    
    def _explain_technical_compatibility(self, score: float) -> str:
        """Explica compatibilidade técnica"""
        if score >= 0.80:
            return "Suas habilidades técnicas se alinham perfeitamente com os requisitos da vaga. Você possui o background ideal para esta posição."
        elif score >= 0.60:
            return "Boa compatibilidade técnica. Você tem a maioria das habilidades necessárias, com pequenas lacunas que podem ser preenchidas rapidamente."
        elif score >= 0.40:
            return "Compatibilidade moderada. Você tem algumas habilidades relevantes, mas precisará desenvolver conhecimentos adicionais."
        else:
            return "Baixa compatibilidade técnica. Esta vaga exige habilidades significativamente diferentes do seu perfil atual."
    
    def _explain_tech_match(self, score: float) -> str:
        """Explica match exato de tecnologias"""
        if score >= 0.70:
            return "Você domina a maioria das tecnologias especificamente mencionadas na vaga."
        elif score >= 0.40:
            return "Você possui experiência com algumas das tecnologias principais requeridas."
        else:
            return "Poucas tecnologias em comum. Seria necessário aprender novas ferramentas."
    
    def _explain_seniority_match(self, score: float) -> str:
        """Explica compatibilidade de senioridade"""
        if score >= 0.90:
            return "Seu nível de experiência corresponde exatamente ao que a empresa busca."
        elif score >= 0.70:
            return "Seu nível de senioridade é compatível, com pequena variação que não impacta negativamente."
        else:
            return "Há uma diferença significativa entre seu nível atual e o requerido pela vaga."
    
    def _explain_salary_compatibility(self, score: float) -> str:
        """Explica compatibilidade salarial"""
        if score >= 0.80:
            return "A faixa salarial desta vaga está alinhada ou acima de suas expectativas."
        elif score >= 0.60:
            return "A faixa salarial é razoavelmente compatível com suas expectativas."
        else:
            return "A faixa salarial pode estar abaixo de suas expectativas atuais."
    
    def _explain_location_compatibility(self, score: float) -> str:
        """Explica compatibilidade de localização"""
        if score >= 0.90:
            return "Modalidade de trabalho totalmente flexível (remoto ou híbrido)."
        elif score >= 0.70:
            return "Boa flexibilidade de localização, com opções de trabalho remoto."
        else:
            return "Trabalho presencial que pode requerer deslocamento ou mudança."
    
    def _generate_skills_analysis(self, cv_data: Dict, job_data: Dict, match_result: MatchResult) -> Dict:
        """Análise detalhada de habilidades"""
        cv_skills = set(skill.lower() for skill in cv_data['skills']['technical'])
        job_skills = set(skill.lower() for skill in job_data['skills'])
        
        matched = cv_skills & job_skills
        missing = job_skills - cv_skills
        extra = cv_skills - job_skills
        
        # Categorizar skills por nível de dificuldade para aprender
        skill_categories = {
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring'],
            'languages': ['python', 'javascript', 'java', 'typescript', 'go', 'rust'],
            'databases': ['postgresql', 'mysql', 'mongodb', 'redis'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
            'tools': ['git', 'jenkins', 'terraform', 'ansible']
        }
        
        missing_by_category = {}
        for category, skills in skill_categories.items():
            missing_in_category = [skill for skill in missing if skill in skills]
            if missing_in_category:
                missing_by_category[category] = missing_in_category
        
        return {
            'matched_skills': {
                'count': len(matched),
                'skills': list(matched),
                'impact': "Essas habilidades demonstram que você tem a base necessária para a função."
            },
            'missing_skills': {
                'count': len(missing),
                'by_category': missing_by_category,
                'priority_to_learn': list(missing)[:3],
                'learning_difficulty': self._assess_learning_difficulty(list(missing)[:3])
            },
            'additional_skills': {
                'count': len(extra),
                'skills': list(extra)[:5],
                'value': "Essas habilidades adicionais podem ser um diferencial na sua candidatura."
            }
        }
    
    def _assess_learning_difficulty(self, skills: List[str]) -> Dict[str, str]:
        """Avalia dificuldade de aprendizado para skills faltantes"""
        difficulty_map = {
            # Linguagens - Médio a Alto
            'python': 'Médio (2-3 meses para proficiência básica)',
            'javascript': 'Médio (2-3 meses para proficiência básica)',
            'typescript': 'Fácil se você já sabe JavaScript (3-4 semanas)',
            'java': 'Médio-Alto (3-4 meses)',
            'go': 'Médio (2-3 meses)',
            
            # Frameworks - Fácil a Médio
            'react': 'Fácil se você sabe JavaScript (4-6 semanas)',
            'angular': 'Médio (6-8 semanas)',
            'vue': 'Fácil se você sabe JavaScript (3-4 semanas)',
            'django': 'Médio se você sabe Python (4-6 semanas)',
            'flask': 'Fácil se você sabe Python (2-3 semanas)',
            
            # Cloud - Médio
            'aws': 'Médio (6-8 semanas para certificação básica)',
            'docker': 'Médio (3-4 semanas)',
            'kubernetes': 'Alto (3-4 meses)',
            
            # Banco de dados - Fácil a Médio
            'postgresql': 'Fácil se você sabe SQL (2-3 semanas)',
            'mongodb': 'Médio (4-6 semanas)',
            'redis': 'Fácil (1-2 semanas)',
        }
        
        result = {}
        for skill in skills:
            result[skill] = difficulty_map.get(skill.lower(), 'Médio (4-6 semanas estimadas)')
        
        return result
    
    def _analyze_career_progression(self, cv_data: Dict, job_data: Dict) -> Dict:
        """Analisa progressão de carreira"""
        cv_seniority = cv_data.get('seniority', 'pleno').lower()
        job_seniority = job_data.get('seniority', 'pleno').lower()
        
        seniority_progression = {
            'estagiario': 1, 'junior': 2, 'pleno': 3, 'senior': 4, 'lead': 5, 'gerente': 6
        }
        
        cv_level = seniority_progression.get(cv_seniority, 3)
        job_level = seniority_progression.get(job_seniority, 3)
        
        progression_type = ""
        career_impact = ""
        
        if job_level > cv_level:
            progression_type = "PROMOÇÃO"
            career_impact = f"Esta vaga representa um avanço na sua carreira, do nível {cv_seniority} para {job_seniority}."
        elif job_level == cv_level:
            progression_type = "LATERAL"
            career_impact = f"Esta vaga mantém seu nível atual ({cv_seniority}) mas pode oferecer novas experiências."
        else:
            progression_type = "REGRESSÃO"
            career_impact = f"Esta vaga está abaixo do seu nível atual, pode não ser ideal para progressão."
        
        return {
            'progression_type': progression_type,
            'current_level': cv_seniority.title(),
            'target_level': job_seniority.title(),
            'career_impact': career_impact,
            'recommendation': self._get_career_recommendation(progression_type, cv_level, job_level)
        }
    
    def _get_career_recommendation(self, progression_type: str, cv_level: int, job_level: int) -> str:
        """Gera recomendação de carreira"""
        if progression_type == "PROMOÇÃO":
            return "Excelente oportunidade de crescimento! Certifique-se de destacar suas realizações que demonstram readiness para o próximo nível."
        elif progression_type == "LATERAL":
            return "Boa oportunidade para diversificar experiência. Foque em como esta posição pode adicionar novas habilidades ao seu perfil."
        else:
            return "Avalie cuidadosamente se esta posição oferece outros benefícios (flexibilidade, aprendizado, empresa dos sonhos) que compensem a regressão de nível."
    
    def _identify_learning_opportunities(self, cv_data: Dict, job_data: Dict) -> Dict:
        """Identifica oportunidades de aprendizado"""
        job_skills = set(skill.lower() for skill in job_data['skills'])
        cv_skills = set(skill.lower() for skill in cv_data['skills']['technical'])
        
        skills_to_learn = job_skills - cv_skills
        
        # Categorizar por área de conhecimento
        learning_areas = {
            'Frontend': [s for s in skills_to_learn if s in ['react', 'angular', 'vue', 'javascript', 'typescript', 'css', 'html']],
            'Backend': [s for s in skills_to_learn if s in ['python', 'java', 'node.js', 'django', 'spring', 'flask']],
            'Database': [s for s in skills_to_learn if s in ['postgresql', 'mysql', 'mongodb', 'redis', 'sql']],
            'DevOps/Cloud': [s for s in skills_to_learn if s in ['aws', 'docker', 'kubernetes', 'jenkins', 'terraform']],
            'Ferramentas': [s for s in skills_to_learn if s in ['git', 'jira', 'confluence', 'slack']]
        }
        
        learning_areas = {k: v for k, v in learning_areas.items() if v}  # Remove categorias vazias
        
        return {
            'total_new_skills': len(skills_to_learn),
            'by_area': learning_areas,
            'priority_skills': list(skills_to_learn)[:3],
            'learning_path': self._suggest_learning_path(learning_areas),
            'estimated_time': self._estimate_learning_time(skills_to_learn)
        }
    
    def _suggest_learning_path(self, learning_areas: Dict) -> List[str]:
        """Sugere caminho de aprendizado"""
        path = []
        
        # Priorizar por facilidade e impacto
        if 'Ferramentas' in learning_areas:
            path.append("1. Comece com ferramentas básicas (Git, etc.) - 1-2 semanas")
        
        if 'Frontend' in learning_areas:
            path.append("2. Desenvolva habilidades frontend - 4-6 semanas")
        
        if 'Backend' in learning_areas:
            path.append("3. Aprenda tecnologias backend - 6-8 semanas")
        
        if 'Database' in learning_areas:
            path.append("4. Estude bancos de dados - 3-4 semanas")
        
        if 'DevOps/Cloud' in learning_areas:
            path.append("5. Explore DevOps e Cloud - 8-10 semanas")
        
        return path
    
    def _estimate_learning_time(self, skills: set) -> str:
        """Estima tempo total de aprendizado"""
        total_weeks = len(skills) * 3  # Estimativa média de 3 semanas por skill
        
        if total_weeks <= 4:
            return f"1 mês intensivo ({total_weeks} semanas)"
        elif total_weeks <= 12:
            return f"{total_weeks//4} meses dedicados ({total_weeks} semanas)"
        else:
            return f"{total_weeks//4} meses (considere focar nas skills prioritárias primeiro)"
    
    def _assess_application_risks(self, cv_data: Dict, job_data: Dict, match_result: MatchResult) -> Dict:
        """Avalia riscos da candidatura"""
        risks = []
        opportunities = []
        
        # Análise de compatibilidade
        if match_result.overall_score < 0.3:
            risks.append("Baixa compatibilidade geral - candidatura pode não ser bem-sucedida")
        elif match_result.overall_score < 0.5:
            risks.append("Compatibilidade moderada - prepare-se bem para entrevistas")
        
        # Análise de skills gap
        missing_count = len(match_result.missing_skills)
        if missing_count > 5:
            risks.append(f"Muitas skills faltantes ({missing_count}) - pode ser desafiador")
        elif missing_count > 2:
            risks.append("Algumas skills importantes faltando - foque no aprendizado")
        
        # Análise de senioridade
        seniority_score = match_result.breakdown_scores.get('seniority', 0)
        if seniority_score < 0.5:
            risks.append("Incompatibilidade de nível - pode ser rejeitado por overqualification/underqualification")
        
        # Oportunidades
        if match_result.overall_score > 0.6:
            opportunities.append("Alta compatibilidade - boa chance de sucesso")
        
        if len(match_result.matched_skills) > 3:
            opportunities.append("Muitas skills em comum - destaque isso na candidatura")
        
        salary_score = match_result.breakdown_scores.get('salary', 0)
        if salary_score > 0.8:
            opportunities.append("Excelente alinhamento salarial - negocie com confiança")
        
        return {
            'risk_level': self._calculate_risk_level(risks),
            'risks': risks,
            'opportunities': opportunities,
            'recommendation': self._get_application_recommendation(len(risks), len(opportunities))
        }
    
    def _calculate_risk_level(self, risks: List[str]) -> str:
        """Calcula nível de risco da candidatura"""
        if len(risks) == 0:
            return "BAIXO"
        elif len(risks) <= 2:
            return "MÉDIO"
        else:
            return "ALTO"
    
    def _get_application_recommendation(self, risk_count: int, opportunity_count: int) -> str:
        """Gera recomendação de candidatura"""
        if opportunity_count > risk_count:
            return "RECOMENDADO - Vá em frente com a candidatura!"
        elif opportunity_count == risk_count:
            return "CONSIDERAR - Avalie pros e contras antes de aplicar"
        else:
            return "CUIDADO - Prepare-se muito bem ou considere outras oportunidades primeiro"
    
    def _generate_negotiation_insights(self, cv_data: Dict, job_data: Dict) -> Dict:
        """Gera insights para negociação"""
        cv_salary = cv_data.get('salary_range', {})
        job_salary = job_data.get('salary_info', {})
        
        insights = {
            'salary_position': self._analyze_salary_position(cv_salary, job_salary),
            'negotiation_strengths': self._identify_negotiation_strengths(cv_data, job_data),
            'market_position': self._assess_market_position(cv_data),
            'negotiation_strategy': self._suggest_negotiation_strategy(cv_salary, job_salary)
        }
        
        return insights
    
    def _analyze_salary_position(self, cv_salary: Dict, job_salary: Dict) -> str:
        """Analisa posição salarial"""
        if not cv_salary or not job_salary:
            return "Informações salariais insuficientes para análise"
        
        cv_median = cv_salary.get('median', 0)
        job_median = job_salary.get('median', 0)
        
        if job_median > cv_median * 1.1:
            return f"Vaga oferece salário {((job_median/cv_median - 1) * 100):.0f}% acima de sua expectativa"
        elif job_median < cv_median * 0.9:
            return f"Vaga oferece salário {((1 - job_median/cv_median) * 100):.0f}% abaixo de sua expectativa"
        else:
            return "Faixa salarial alinhada com suas expectativas"
    
    def _identify_negotiation_strengths(self, cv_data: Dict, job_data: Dict) -> List[str]:
        """Identifica pontos fortes para negociação"""
        strengths = []
        
        # Skills raras ou em alta demanda
        high_demand_skills = ['python', 'react', 'aws', 'kubernetes', 'machine learning']
        cv_skills = [s.lower() for s in cv_data['skills']['technical']]
        
        for skill in high_demand_skills:
            if skill in cv_skills:
                strengths.append(f"Domínio de {skill} (alta demanda no mercado)")
        
        # Senioridade
        seniority = cv_data.get('seniority', '').lower()
        if seniority in ['senior', 'especialista', 'lead']:
            strengths.append("Nível de senioridade elevado")
        
        # Experiência
        experience = cv_data.get('experience', {})
        total_years = experience.get('total_years', 0)
        if total_years > 5:
            strengths.append(f"{total_years} anos de experiência")
        
        return strengths[:3]  # Top 3 strengths
    
    def _assess_market_position(self, cv_data: Dict) -> str:
        """Avalia posição no mercado"""
        seniority = cv_data.get('seniority', '').lower()
        skills_count = len(cv_data['skills']['technical'])
        experience = cv_data.get('experience', {}).get('total_years', 0)
        
        score = 0
        if seniority in ['senior', 'especialista']:
            score += 3
        elif seniority == 'pleno':
            score += 2
        
        if skills_count > 8:
            score += 2
        elif skills_count > 5:
            score += 1
        
        if experience > 7:
            score += 2
        elif experience > 3:
            score += 1
        
        if score >= 6:
            return "FORTE - Você está em posição vantajosa para negociar"
        elif score >= 4:
            return "BOA - Você tem bons argumentos para negociação"
        else:
            return "MODERADA - Foque em demonstrar valor e potencial"
    
    def _suggest_negotiation_strategy(self, cv_salary: Dict, job_salary: Dict) -> List[str]:
        """Sugere estratégia de negociação"""
        strategy = []
        
        if not cv_salary or not job_salary:
            strategy.append("Pesquise faixas salariais de mercado antes de negociar")
            return strategy
        
        cv_median = cv_salary.get('median', 0)
        job_median = job_salary.get('median', 0)
        
        if job_median > cv_median:
            strategy.append("Empresa oferece acima de sua expectativa - aceite ou negocie benefícios")
            strategy.append("Foque em negociar férias, flexibilidade ou desenvolvimento profissional")
        else:
            strategy.append("Demonstre valor único que você traz para justificar salário maior")
            strategy.append("Apresente pesquisa de mercado para fundamentar sua expectativa")
            strategy.append("Considere negociar revisão salarial em 6 meses")
        
        return strategy
    
    def _generate_preparation_tips(self, cv_data: Dict, job_data: Dict, match_result: MatchResult) -> Dict:
        """Gera dicas de preparação para entrevista"""
        return {
            'technical_preparation': self._suggest_technical_prep(cv_data, job_data, match_result),
            'behavioral_preparation': self._suggest_behavioral_prep(cv_data, job_data),
            'questions_to_ask': self._suggest_questions_to_ask(job_data),
            'portfolio_highlights': self._suggest_portfolio_highlights(cv_data, job_data)
        }
    
    def _suggest_technical_prep(self, cv_data: Dict, job_data: Dict, match_result: MatchResult) -> Dict[str, List[str]]:
        """Sugere preparação técnica detalhada e específica"""
        prep = {
            'priority_skills': [],
            'coding_challenges': [],
            'study_plan': [],
            'practice_projects': [],
            'key_concepts': []
        }
        
        # 1. Skills prioritárias para estudar
        missing_skills = match_result.missing_skills[:3]
        for skill in missing_skills:
            skill_lower = skill.lower()
            
            if skill_lower == 'django':
                prep['priority_skills'].extend([
                    f"📚 Django Framework:",
                    f"   • Estude Models, Views, Templates (MVT pattern)",
                    f"   • Pratique Django ORM e migrations",
                    f"   • Aprenda Django REST Framework para APIs",
                    f"   • Recursos: Django Girls Tutorial, documentação oficial"
                ])
            elif skill_lower == 'postgresql':
                prep['priority_skills'].extend([
                    f"📚 PostgreSQL:",
                    f"   • Revise SQL avançado (JOINs, subqueries, window functions)",
                    f"   • Pratique otimização de queries e indexação",
                    f"   • Estude stored procedures e triggers",
                    f"   • Recursos: PostgreSQL Tutorial, SQL Bolt"
                ])
            elif skill_lower == 'react':
                prep['priority_skills'].extend([
                    f"📚 React:",
                    f"   • Domine hooks (useState, useEffect, useContext)",
                    f"   • Pratique component lifecycle e state management",
                    f"   • Estude React Router e context API",
                    f"   • Recursos: React docs, FreeCodeCamp"
                ])
            elif skill_lower == 'aws':
                prep['priority_skills'].extend([
                    f"📚 AWS:",
                    f"   • Foque em EC2, S3, RDS, Lambda",
                    f"   • Pratique AWS CLI e CloudFormation básico",
                    f"   • Estude IAM (usuários, roles, policies)",
                    f"   • Recursos: AWS Free Tier, AWS Training"
                ])
            elif skill_lower == 'docker':
                prep['priority_skills'].extend([
                    f"📚 Docker:",
                    f"   • Aprenda Dockerfile, docker-compose",
                    f"   • Pratique containerização de aplicações Python/Node",
                    f"   • Estude volumes, networks, multi-stage builds",
                    f"   • Recursos: Docker docs, Play with Docker"
                ])
            elif skill_lower == 'kubernetes':
                prep['priority_skills'].extend([
                    f"📚 Kubernetes:",
                    f"   • Conceitos: pods, services, deployments, configmaps",
                    f"   • Pratique kubectl commands básicos",
                    f"   • Estude ingress, persistent volumes",
                    f"   • Recursos: Kubernetes.io, Minikube tutorial"
                ])
            else:
                prep['priority_skills'].append(f"📚 {skill.title()}: Estude fundamentos e sintaxe básica")
        
        # 2. Coding challenges específicos
        job_title = job_data.get('title', '').lower()
        if 'desenvolvedor' in job_title or 'developer' in job_title:
            prep['coding_challenges'].extend([
                "💻 Desafios de Programação:",
                "   • LeetCode: Easy/Medium problems (arrays, strings, hash tables)",
                "   • HackerRank: Pratique problemas da linguagem principal da vaga",
                "   • Codility: Algoritmos e estruturas de dados",
                "   • Prepare solução para FizzBuzz, Fibonacci, Palindromes"
            ])
        elif 'dados' in job_title or 'data' in job_title:
            prep['coding_challenges'].extend([
                "📊 Desafios de Dados:",
                "   • Kaggle: Complete um mini-projeto com dataset público",
                "   • SQL Challenges: HackerRank SQL, LeetCode Database",
                "   • Pandas: Manipulação e limpeza de dados",
                "   • Prepare análise exploratória de dados (EDA) exemplo"
            ])
        elif 'devops' in job_title:
            prep['coding_challenges'].extend([
                "🔧 Desafios DevOps:",
                "   • Crie pipeline CI/CD simples com GitHub Actions",
                "   • Dockerize uma aplicação completa",
                "   • Configure monitoring básico (logs, métricas)",
                "   • Implemente infraestrutura como código (Terraform)"
            ])
        
        # 3. Plano de estudos estruturado
        days_to_interview = 7  # Assumindo 1 semana de preparação
        prep['study_plan'].extend([
            f"📅 Plano de Estudos (próximos {days_to_interview} dias):",
            f"   📅 Dias 1-2: Foque na skill mais crítica ({missing_skills[0] if missing_skills else 'tecnologia principal'})",
            f"   📅 Dias 3-4: Revise conceitos das suas skills fortes",
            f"   📅 Dias 5-6: Pratique coding challenges e projetos",
            f"   📅 Dia 7: Revisão geral e preparação de exemplos"
        ])
        
        # 4. Projetos práticos para demonstrar
        matched_skills = match_result.matched_skills[:2]
        if matched_skills:
            prep['practice_projects'].extend([
                f"🛠️ Projetos para Demonstrar:",
                f"   • Crie mini-projeto combinando {' + '.join(matched_skills)}",
                f"   • Publique no GitHub com README detalhado",
                f"   • Inclua testes unitários básicos",
                f"   • Documente decisões técnicas e desafios enfrentados"
            ])
        
        # 5. Conceitos-chave para revisão
        seniority = cv_data.get('seniority', 'pleno').lower()
        if seniority in ['senior', 'especialista']:
            prep['key_concepts'].extend([
                "🎯 Conceitos para Nível Senior:",
                "   • Design Patterns: Singleton, Factory, Observer",
                "   • Arquitetura: Clean Code, SOLID principles",
                "   • Performance: Otimização de código e banco de dados",
                "   • Liderança: Code review, mentoria, arquitetura de sistemas"
            ])
        elif seniority == 'pleno':
            prep['key_concepts'].extend([
                "🎯 Conceitos para Nível Pleno:",
                "   • Melhores práticas de desenvolvimento",
                "   • Testes automatizados (unitários, integração)",
                "   • Versionamento avançado com Git",
                "   • Debugging e profiling de aplicações"
            ])
        else:  # junior
            prep['key_concepts'].extend([
                "🎯 Conceitos para Nível Junior:",
                "   • Fundamentos da linguagem principal",
                "   • Controle de versão com Git (básico)",
                "   • Debugging e resolução de problemas",
                "   • Boas práticas de código limpo"
            ])
        
        return prep
    
    def _suggest_behavioral_prep(self, cv_data: Dict, job_data: Dict) -> Dict[str, List[str]]:
        """Sugere preparação comportamental detalhada"""
        prep = {
            'star_examples': [],
            'company_research': [],
            'soft_skills': [],
            'leadership_scenarios': [],
            'common_questions': []
        }
        
        seniority = cv_data.get('seniority', 'pleno').lower()
        job_title = job_data.get('title', '').lower()
        company = job_data.get('company', '')
        
        # 1. Exemplos STAR específicos
        prep['star_examples'].extend([
            "📝 Prepare 5-7 exemplos STAR estruturados:",
            "   🎯 Situação de resolução de problema técnico complexo",
            "   🎯 Momento de trabalho em equipe sob pressão",
            "   🎯 Ocasião onde tomou iniciativa em projeto",
            "   🎯 Erro/falha e como aprendeu com ele",
            "   🎯 Melhoria de processo que implementou"
        ])
        
        if seniority in ['senior', 'especialista', 'lead']:
            prep['star_examples'].extend([
                "   🎯 Exemplo de mentoria ou ensino para colega",
                "   🎯 Situação de liderança técnica em projeto crítico",
                "   🎯 Decisão arquitetural importante que tomou"
            ])
        elif seniority == 'pleno':
            prep['star_examples'].extend([
                "   🎯 Projeto onde cresceu além de suas responsabilidades",
                "   🎯 Colaboração com outras áreas/times"
            ])
        
        # 2. Pesquisa sobre a empresa
        prep['company_research'].extend([
            f"🏢 Pesquise sobre {company}:",
            "   📊 Modelo de negócio e principais produtos/serviços",
            "   🎯 Missão, visão, valores da empresa",
            "   📈 Notícias recentes e crescimento",
            "   👥 Equipe de tecnologia (LinkedIn, blog técnico)",
            "   💼 Cultura organizacional (Glassdoor, redes sociais)",
            "   🚀 Projetos técnicos interessantes ou open source"
        ])
        
        # 3. Soft skills com exemplos
        if 'dados' in job_title or 'data' in job_title:
            prep['soft_skills'].extend([
                "🧠 Soft Skills para Área de Dados:",
                "   🔍 Pensamento analítico - Prepare exemplo de insight descoberto",
                "   💬 Comunicação - Como explicou análise complexa para não-técnicos",
                "   📊 Orientação a negócios - Projeto que gerou valor mensurável",
                "   🎯 Curiosidade - Situação onde fez perguntas que ninguém pensou"
            ])
        elif 'desenvolvedor' in job_title or 'developer' in job_title:
            prep['soft_skills'].extend([
                "🧠 Soft Skills para Desenvolvimento:",
                "   🔧 Resolução de problemas - Bug complexo que resolveu",
                "   👥 Colaboração - Code review construtivo que deu/recebeu",
                "   📚 Aprendizado contínuo - Nova tecnologia que dominou rapidamente",
                "   🎨 Atenção aos detalhes - Situação onde qualidade fez diferença"
            ])
        elif 'devops' in job_title:
            prep['soft_skills'].extend([
                "🧠 Soft Skills para DevOps:",
                "   🚨 Gestão de crise - Incident response que liderou",
                "   🤝 Facilitação - Como melhorou comunicação entre dev e ops",
                "   📈 Melhoria contínua - Processo que otimizou",
                "   🛡️ Responsabilidade - Sistema crítico que manteve funcionando"
            ])
        
        # 4. Cenários de liderança (para níveis senior+)
        if seniority in ['senior', 'especialista', 'lead']:
            prep['leadership_scenarios'].extend([
                "👨‍💼 Cenários de Liderança:",
                "   🎓 Como você mentoraria um desenvolvedor junior?",
                "   ⚖️ Como resolveria conflito técnico entre membros da equipe?",
                "   🚀 Como você estabeleceria prioridades em projeto com prazos apertados?",
                "   📋 Como conduziria uma reunião de retrospectiva eficaz?",
                "   🔧 Como você abordaria uma dívida técnica significativa?"
            ])
        
        # 5. Perguntas comportamentais comuns
        prep['common_questions'].extend([
            "❓ Perguntas Comportamentais Frequentes:",
            "   💪 'Conte sobre seu maior desafio profissional'",
            "   🎯 'Por que quer trabalhar aqui especificamente?'",
            "   📈 'Onde se vê em 3-5 anos?'",
            "   🤔 'Como lida com feedback negativo?'",
            "   ⏰ 'Conte sobre uma vez que perdeu um deadline'",
            "   🚀 'Qual projeto você mais se orgulha e por quê?'",
            "   🔄 'Como você se mantém atualizado tecnicamente?'"
        ])
        
        if 'startup' in company.lower() or 'startupbr' in company.lower():
            prep['common_questions'].extend([
                "   ⚡ 'Como você trabalha em ambiente de alta velocidade?'",
                "   🎯 'Já trabalhou em empresa de crescimento rápido?'"
            ])
        
        return prep
    
    def _suggest_questions_to_ask(self, job_data: Dict) -> Dict[str, List[str]]:
        """Sugere perguntas categorizadas para fazer na entrevista"""
        job_title = job_data.get('title', '').lower()
        company = job_data.get('company', '')
        
        questions = {
            'technical_role': [],
            'team_culture': [],
            'growth_learning': [],
            'company_vision': [],
            'day_to_day': []
        }
        
        # 1. Perguntas sobre o papel técnico
        questions['technical_role'].extend([
            "🔧 Sobre o Papel Técnico:",
            "   • Quais são os principais desafios técnicos que a equipe enfrenta atualmente?",
            "   • Como é a arquitetura atual do sistema/produto principal?",
            "   • Qual é o stack tecnológico completo utilizado?",
            "   • Como vocês abordam dívida técnica e refatoração?",
            "   • Quais métricas técnicas são mais importantes para o time?"
        ])
        
        if 'dados' in job_title or 'data' in job_title:
            questions['technical_role'].extend([
                "   • Qual o volume de dados processados diariamente?",
                "   • Como é feita a governança e qualidade dos dados?",
                "   • Quais ferramentas de visualização e BI são utilizadas?"
            ])
        elif 'devops' in job_title:
            questions['technical_role'].extend([
                "   • Como é o pipeline de CI/CD atual?",
                "   • Qual é a estratégia de monitoramento e observabilidade?",
                "   • Como vocês gerenciam infrastructure as code?"
            ])
        
        # 2. Perguntas sobre equipe e cultura
        questions['team_culture'].extend([
            "👥 Sobre a Equipe e Cultura:",
            "   • Como é a dinâmica da equipe de desenvolvimento?",
            "   • Qual é o processo de code review e pair programming?",
            "   • Como vocês tomam decisões técnicas em grupo?",
            "   • Como é tratado o work-life balance na empresa?",
            "   • Existe rotação entre projetos/squads?",
            "   • Como vocês celebram sucessos e lidam com falhas?"
        ])
        
        # 3. Perguntas sobre crescimento e aprendizado
        questions['growth_learning'].extend([
            "📈 Crescimento e Aprendizado:",
            "   • Qual é o plano de carreira típico para esta posição?",
            "   • Como funciona o processo de feedback e avaliação?",
            "   • A empresa oferece budget para cursos/conferências?",
            "   • Existe programa de mentoria interna?",
            "   • Como vocês incentivam inovação e experimentação?",
            "   • Quais oportunidades de liderança técnica existem?"
        ])
        
        # 4. Perguntas sobre visão da empresa
        questions['company_vision'].extend([
            f"🚀 Visão da {company}:",
            "   • Quais são os principais objetivos para os próximos 2 anos?",
            "   • Como a área de tecnologia se alinha com a estratégia do negócio?",
            "   • Quais tecnologias emergentes a empresa está considerando?",
            "   • Como vocês medem o impacto da tecnologia no resultado?",
            "   • Qual é a maior oportunidade técnica que vocês veem?"
        ])
        
        # 5. Perguntas sobre o dia a dia
        questions['day_to_day'].extend([
            "📅 Rotina e Operacional:",
            "   • Como é um dia típico nesta posição?",
            "   • Qual é a frequência de deploys/releases?",
            "   • Como vocês organizam sprints e planning?",
            "   • Quais ferramentas de comunicação e gestão usam?",
            "   • Como é feito o on-boarding de novos desenvolvedores?",
            "   • Que tipo de documentação técnica vocês mantêm?"
        ])
        
        return questions
    
    def _suggest_portfolio_highlights(self, cv_data: Dict, job_data: Dict) -> List[str]:
        """Sugere destaques do portfólio"""
        highlights = []
        
        job_skills = set(skill.lower() for skill in job_data['skills'])
        cv_skills = cv_data['skills']['technical']
        
        # Projetos relacionados às skills da vaga
        for skill in cv_skills:
            if skill.lower() in job_skills:
                highlights.append(f"Projeto demonstrando uso de {skill}")
        
        highlights.extend([
            "Projeto mais complexo que liderou ou participou ativamente",
            "Exemplo de solução criativa para problema técnico",
            "Projeto que demonstra aprendizado rápido de nova tecnologia"
        ])
        
        return highlights[:4]  # Top 4 highlights
    
    def _estimate_application_timeline(self, cv_data: Dict, job_data: Dict) -> Dict:
        """Estima timeline do processo de candidatura"""
        # Estimativas baseadas em padrões de mercado
        return {
            'preparation_time': "3-5 dias para preparação adequada",
            'application_response': "1-2 semanas para resposta inicial",
            'interview_process': "2-4 semanas (geralmente 2-3 rodadas)",
            'total_timeline': "1-2 meses do envio até decisão final",
            'tips': [
                "Candidate-se rapidamente se muito interessado",
                "Continue aplicando para outras vagas em paralelo",
                "Acompanhe o processo semanalmente se não houver resposta"
            ]
        }
    
    def print_detailed_recommendation(self, match_result: MatchResult, cv_data: Dict, job_data: Dict):
        """
        Imprime análise detalhada e aprofundada da recomendação
        """
        from src.utils.enhanced_menu_system import Colors
        
        analysis = self.generate_detailed_analysis(match_result, cv_data, job_data)
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}📋 ANÁLISE DETALHADA DA RECOMENDAÇÃO{Colors.RESET}")
        print("=" * 80)
        
        # Informações básicas da vaga
        print(f"\n{Colors.BOLD}🎯 {match_result.job_title}{Colors.RESET}")
        print(f"🏢 {match_result.company}")
        print(f"📊 Compatibilidade geral: {Colors.GREEN}{match_result.overall_score*100:.1f}%{Colors.RESET}")
        
        # Breakdown detalhado de compatibilidade
        print(f"\n{Colors.BOLD}{Colors.BLUE}📊 ANÁLISE DE COMPATIBILIDADE{Colors.RESET}")
        for aspect, details in analysis['compatibility_breakdown'].items():
            level_color = Colors.GREEN if details['level'] in ['EXCELENTE', 'MUITO BOM'] else Colors.YELLOW if details['level'] == 'BOM' else Colors.RED
            print(f"\n{Colors.BOLD}{aspect}:{Colors.RESET} {level_color}{details['score']} ({details['level']}){Colors.RESET}")
            print(f"   {details['explanation']}")
        
        # Análise de habilidades
        print(f"\n{Colors.BOLD}{Colors.PURPLE}🛠️ ANÁLISE DE HABILIDADES{Colors.RESET}")
        skills_analysis = analysis['skills_analysis']
        
        if skills_analysis['matched_skills']['skills']:
            print(f"\n{Colors.GREEN}✅ Habilidades em comum ({skills_analysis['matched_skills']['count']}):{Colors.RESET}")
            for skill in skills_analysis['matched_skills']['skills']:
                print(f"   • {skill.title()}")
            print(f"   💡 {skills_analysis['matched_skills']['impact']}")
        
        if skills_analysis['missing_skills']['by_category']:
            print(f"\n{Colors.YELLOW}📚 Habilidades para desenvolver:{Colors.RESET}")
            for category, skills in skills_analysis['missing_skills']['by_category'].items():
                print(f"\n   {Colors.BOLD}{category}:{Colors.RESET}")
                for skill in skills:
                    difficulty = skills_analysis['missing_skills']['learning_difficulty'].get(skill, 'Tempo não estimado')
                    print(f"      • {skill.title()} - {difficulty}")
        
        # Progressão de carreira
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}📈 IMPACTO NA CARREIRA{Colors.RESET}")
        career = analysis['career_progression']
        progression_color = Colors.GREEN if career['progression_type'] == 'PROMOÇÃO' else Colors.YELLOW if career['progression_type'] == 'LATERAL' else Colors.RED
        
        print(f"Tipo: {progression_color}{career['progression_type']}{Colors.RESET}")
        print(f"Nível atual: {career['current_level']} → Nível da vaga: {career['target_level']}")
        print(f"💡 {career['career_impact']}")
        print(f"🎯 {career['recommendation']}")
        
        # Oportunidades de aprendizado
        learning = analysis['learning_opportunities']
        if learning['by_area']:
            print(f"\n{Colors.BOLD}{Colors.CYAN}🎓 OPORTUNIDADES DE APRENDIZADO{Colors.RESET}")
            print(f"Total de novas habilidades: {learning['total_new_skills']}")
            print(f"Tempo estimado de aprendizado: {learning['estimated_time']}")
            
            if learning['learning_path']:
                print(f"\n{Colors.BOLD}Caminho de aprendizado sugerido:{Colors.RESET}")
                for step in learning['learning_path']:
                    print(f"   {step}")
        
        # Avaliação de riscos
        print(f"\n{Colors.BOLD}{Colors.RED}⚠️ AVALIAÇÃO DE RISCOS{Colors.RESET}")
        risks = analysis['risk_assessment']
        risk_color = Colors.RED if risks['risk_level'] == 'ALTO' else Colors.YELLOW if risks['risk_level'] == 'MÉDIO' else Colors.GREEN
        
        print(f"Nível de risco: {risk_color}{risks['risk_level']}{Colors.RESET}")
        
        if risks['risks']:
            print(f"\n{Colors.BOLD}Riscos identificados:{Colors.RESET}")
            for risk in risks['risks']:
                print(f"   ⚠️ {risk}")
        
        if risks['opportunities']:
            print(f"\n{Colors.BOLD}Oportunidades identificadas:{Colors.RESET}")
            for opportunity in risks['opportunities']:
                print(f"   ✅ {opportunity}")
        
        print(f"\n{Colors.BOLD}Recomendação de candidatura:{Colors.RESET} {risks['recommendation']}")
        
        # Insights de negociação
        print(f"\n{Colors.BOLD}{Colors.GREEN}💰 INSIGHTS PARA NEGOCIAÇÃO{Colors.RESET}")
        negotiation = analysis['negotiation_insights']
        
        print(f"Posição salarial: {negotiation['salary_position']}")
        print(f"Posição no mercado: {negotiation['market_position']}")
        
        if negotiation['negotiation_strengths']:
            print(f"\n{Colors.BOLD}Seus pontos fortes para negociação:{Colors.RESET}")
            for strength in negotiation['negotiation_strengths']:
                print(f"   💪 {strength}")
        
        if negotiation['negotiation_strategy']:
            print(f"\n{Colors.BOLD}Estratégia sugerida:{Colors.RESET}")
            for strategy in negotiation['negotiation_strategy']:
                print(f"   🎯 {strategy}")
        
        # Dicas de preparação
        print(f"\n{Colors.BOLD}{Colors.BLUE}📝 PREPARAÇÃO PARA ENTREVISTA{Colors.RESET}")
        prep = analysis['preparation_tips']
        
        # Preparação técnica estruturada
        technical_prep = prep['technical_preparation']
        print(f"\n{Colors.BOLD}🔧 PREPARAÇÃO TÉCNICA:{Colors.RESET}")
        
        # Skills prioritárias
        if 'priority_skills' in technical_prep and technical_prep['priority_skills']:
            for tip in technical_prep['priority_skills']:
                print(f"   {tip}")
        
        # Plano de estudos
        if 'study_plan' in technical_prep and technical_prep['study_plan']:
            print(f"\n{Colors.BOLD}   📅 CRONOGRAMA DE ESTUDOS:{Colors.RESET}")
            for tip in technical_prep['study_plan']:
                print(f"   {tip}")
        
        # Coding challenges
        if 'coding_challenges' in technical_prep and technical_prep['coding_challenges']:
            print(f"\n{Colors.BOLD}   💻 DESAFIOS PRÁTICOS:{Colors.RESET}")
            for tip in technical_prep['coding_challenges']:
                print(f"   {tip}")
        
        # Projetos práticos
        if 'practice_projects' in technical_prep and technical_prep['practice_projects']:
            print(f"\n{Colors.BOLD}   🛠️ PROJETOS DEMONSTRATIVOS:{Colors.RESET}")
            for tip in technical_prep['practice_projects']:
                print(f"   {tip}")
        
        # Preparação comportamental estruturada
        behavioral_prep = prep['behavioral_preparation']
        print(f"\n{Colors.BOLD}🗣️ PREPARAÇÃO COMPORTAMENTAL:{Colors.RESET}")
        
        # Exemplos STAR
        if 'star_examples' in behavioral_prep and behavioral_prep['star_examples']:
            for tip in behavioral_prep['star_examples']:
                print(f"   {tip}")
        
        # Pesquisa da empresa
        if 'company_research' in behavioral_prep and behavioral_prep['company_research']:
            print(f"\n{Colors.BOLD}   🏢 PESQUISA DA EMPRESA:{Colors.RESET}")
            for tip in behavioral_prep['company_research'][:7]:  # Limite para não ficar muito longo
                print(f"   {tip}")
        
        # Soft skills específicas
        if 'soft_skills' in behavioral_prep and behavioral_prep['soft_skills']:
            print(f"\n{Colors.BOLD}   🧠 SOFT SKILLS ESPECÍFICAS:{Colors.RESET}")
            for tip in behavioral_prep['soft_skills']:
                print(f"   {tip}")
        
        # Cenários de liderança (se aplicável)
        if 'leadership_scenarios' in behavioral_prep and behavioral_prep['leadership_scenarios']:
            print(f"\n{Colors.BOLD}   👨‍💼 CENÁRIOS DE LIDERANÇA:{Colors.RESET}")
            for tip in behavioral_prep['leadership_scenarios']:
                print(f"   {tip}")
        
        # Perguntas para fazer
        questions = prep['questions_to_ask']
        print(f"\n{Colors.BOLD}❓ PERGUNTAS ESTRATÉGICAS PARA FAZER:{Colors.RESET}")
        
        # Perguntas técnicas
        if 'technical_role' in questions and questions['technical_role']:
            for question in questions['technical_role'][:6]:  # Primeiras 6
                print(f"   {question}")
        
        # Perguntas sobre crescimento
        if 'growth_learning' in questions and questions['growth_learning']:
            print(f"\n{Colors.BOLD}   📈 SOBRE CRESCIMENTO:{Colors.RESET}")
            for question in questions['growth_learning'][:5]:  # Primeiras 5
                print(f"   {question}")
        
        # Perguntas sobre cultura
        if 'team_culture' in questions and questions['team_culture']:
            print(f"\n{Colors.BOLD}   👥 SOBRE EQUIPE E CULTURA:{Colors.RESET}")
            for question in questions['team_culture'][:4]:  # Primeiras 4
                print(f"   {question}")
        
        # Timeline
        print(f"\n{Colors.BOLD}{Colors.GRAY}⏰ TIMELINE ESPERADO{Colors.RESET}")
        timeline = analysis['timeline_expectations']
        print(f"Preparação: {timeline['preparation_time']}")
        print(f"Resposta inicial: {timeline['application_response']}")
        print(f"Processo de entrevistas: {timeline['interview_process']}")
        print(f"Timeline total: {timeline['total_timeline']}")
        
        print(f"\n{Colors.DIM}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}💡 Esta análise foi gerada automaticamente pelo sistema de IA{Colors.RESET}")
        print(f"{Colors.DIM}   Use essas informações como guia, mas sempre aplique seu julgamento pessoal{Colors.RESET}")
        
        return analysis
    
    def get_job_recommendations(self, user_id: str, available_jobs: List[Dict], 
                               top_n: int = 10) -> List[MatchResult]:
        """
        Obtém recomendações de vagas para um usuário
        
        Args:
            user_id: ID do usuário
            available_jobs: Lista de vagas disponíveis
            top_n: Número de recomendações a retornar
            
        Returns:
            Lista de recomendações ordenadas por score
        """
        if user_id not in self.cv_cache:
            raise ValueError(f"CV não analisado para usuário {user_id}")
        
        cv_data = self.cv_cache[user_id]
        recommendations = []
        
        for job in available_jobs:
            job_data = self.prepare_job_for_matching(job)
            match_result = self.calculate_match_score(cv_data, job_data)
            recommendations.append(match_result)
        
        # Ordenar por score e retornar top N
        recommendations.sort(key=lambda x: x.overall_score, reverse=True)
        return recommendations[:top_n]
    
    def record_user_interaction(self, user_id: str, job_id: str, 
                               interaction_type: str, metadata: Dict = None):
        """
        Registra interação do usuário para learning
        
        Args:
            user_id: ID do usuário
            job_id: ID da vaga
            interaction_type: Tipo de interação (view, like, dislike, apply, interview, hired)
            metadata: Metadados adicionais
        """
        interaction = {
            'user_id': user_id,
            'job_id': job_id,
            'interaction_type': interaction_type,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.interaction_history.append(interaction)
        
        # Atualizar modelo baseado no feedback (implementação futura)
        self._update_model_with_feedback(interaction)
    
    def _update_model_with_feedback(self, interaction: Dict):
        """
        Atualiza modelo baseado no feedback do usuário
        (Implementação futura para learning)
        """
        # TODO: Implementar aprendizado baseado em feedback
        # - Ajustar pesos do algoritmo
        # - Atualizar preferências do usuário
        # - Melhorar detecção de skills
        pass
    
    def get_matching_statistics(self) -> Dict:
        """Retorna estatísticas do sistema de matching"""
        stats = {
            'cvs_processed': len(self.cv_cache),
            'jobs_processed': len(self.job_cache),
            'interactions_recorded': len(self.interaction_history),
            'avg_scores': {},
            'weights_used': self.weights.copy()
        }
        
        # Calcular scores médios se há dados
        if self.interaction_history:
            # Implementar cálculo de estatísticas
            pass
        
        return stats


# Instância global do matcher
cv_job_matcher = AdvancedCVJobMatcher()