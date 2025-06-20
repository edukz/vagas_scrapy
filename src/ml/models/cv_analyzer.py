"""
Analisador de Currículos com IA
===============================

Extrai automaticamente informações do currículo para criar perfil personalizado:
- Habilidades técnicas e soft skills
- Experiência profissional e senioridade
- Formação acadêmica
- Preferências de trabalho
- Criação automática de perfil para recomendações
"""

import re
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import PyPDF2
import docx
from collections import Counter, defaultdict
import spacy
from datetime import datetime, timedelta

from .job_recommender import UserProfile


@dataclass
class CVAnalysisResult:
    """Resultado da análise do currículo"""
    personal_info: Dict[str, str]
    skills: Dict[str, List[str]]
    experience: Dict[str, Union[int, str, List]]
    education: Dict[str, Union[str, List]]
    preferences: Dict[str, Union[str, List]]
    seniority_level: str
    estimated_salary_range: Dict[str, float]
    confidence_score: float
    generated_profile: UserProfile
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        # Converter UserProfile para dict
        result['generated_profile'] = self.generated_profile.to_dict()
        return result


class CVAnalyzer:
    """
    Analisador de currículos que usa IA para extrair informações
    e criar perfis personalizados para recomendação de vagas
    """
    
    def __init__(self):
        # Dicionários de tecnologias por categoria
        self.tech_categories = {
            'linguagens_programacao': {
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 
                'ruby', 'go', 'rust', 'kotlin', 'swift', 'scala', 'r', 'matlab',
                'perl', 'lua', 'dart', 'objective-c', 'assembly'
            },
            'frameworks_web': {
                'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt', 'express',
                'fastapi', 'django', 'flask', 'spring', 'laravel', 'rails', '.net',
                'asp.net', 'blazor', 'ember', 'backbone'
            },
            'mobile': {
                'react native', 'flutter', 'ionic', 'xamarin', 'cordova',
                'android', 'ios', 'kotlin multiplatform', 'unity'
            },
            'databases': {
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'cassandra', 'oracle', 'sql server', 'sqlite', 'dynamodb',
                'firebase', 'couchbase', 'neo4j', 'influxdb'
            },
            'cloud_devops': {
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
                'ansible', 'jenkins', 'gitlab ci', 'github actions', 'circleci',
                'travis ci', 'vagrant', 'helm', 'prometheus', 'grafana'
            },
            'data_science': {
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
                'keras', 'spark', 'hadoop', 'tableau', 'power bi', 'jupyter',
                'apache airflow', 'dbt', 'snowflake', 'databricks'
            },
            'design_ux': {
                'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator',
                'after effects', 'invision', 'zeplin', 'principle'
            },
            'metodologias': {
                'agile', 'scrum', 'kanban', 'lean', 'devops', 'tdd', 'bdd',
                'continuous integration', 'continuous deployment', 'microservices'
            }
        }
        
        # Todas as tecnologias em um set para busca rápida
        self.all_technologies = set()
        for category in self.tech_categories.values():
            self.all_technologies.update(category)
        
        # Soft skills importantes
        self.soft_skills = {
            'lideranca', 'comunicacao', 'trabalho em equipe', 'gestao de projetos',
            'resolucao de problemas', 'criatividade', 'adaptabilidade', 'organizacao',
            'proatividade', 'autonomia', 'colaboracao', 'mentoria', 'coaching',
            'negociacao', 'apresentacao', 'facilitar reunioes', 'vision estrategica',
            'pensamento critico', 'empatia', 'resiliencia', 'flexibilidade'
        }
        
        # Padrões para extração de informações
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'(?:\+55\s?)?(?:\(?[1-9][1-9]\)?\s?)?(?:9\s?)?[0-9]{4}[-\s]?[0-9]{4}'),
            'linkedin': re.compile(r'linkedin\.com/in/([A-Za-z0-9-]+)'),
            'github': re.compile(r'github\.com/([A-Za-z0-9-]+)'),
            'years_experience': re.compile(r'(\d+)\s*(?:anos?|years?)\s*(?:de\s*)?(?:experiência|experience)', re.I),
            'salary_expectation': re.compile(r'(?:R\$|salário|salary)[\s]*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', re.I),
            'graduation_year': re.compile(r'(?:formado|graduado|concluded?)\s*(?:em\s*)?(\d{4})', re.I),
            'birth_year': re.compile(r'(?:nascido|born)\s*(?:em\s*)?(\d{4})', re.I),
            'age': re.compile(r'(\d{2})\s*anos?', re.I)
        }
        
        # Mapeamento de senioridade
        self.seniority_keywords = {
            'estagiario': ['estagiário', 'trainee', 'aprendiz', 'intern'],
            'junior': ['júnior', 'junior', 'jr', 'iniciante', 'entry level'],
            'pleno': ['pleno', 'analista', 'desenvolvedor', 'middle', 'mid-level'],
            'senior': ['sênior', 'senior', 'sr', 'specialist', 'especialista'],
            'especialista': ['arquiteto', 'tech lead', 'principal', 'staff', 'expert', 'líder técnico'],
            'gerente': ['gerente', 'manager', 'coordenador', 'supervisor', 'head'],
            'diretor': ['diretor', 'director', 'vp', 'vice president', 'c-level']
        }
        
        # Indicadores de localização
        self.location_indicators = {
            'presencial': ['presencial', 'escritório', 'on-site'],
            'remoto': ['remoto', 'remote', 'home office', 'trabalho remoto'],
            'hibrido': ['híbrido', 'hybrid', 'flexível', 'semi-presencial']
        }
        
        # Carregar spaCy se disponível
        try:
            self.nlp = spacy.load("pt_core_news_sm")
        except:
            print("⚠️ spaCy português não encontrado. Funcionalidade de NER limitada.")
            self.nlp = None
    
    def analyze_cv(self, file_path: str, user_id: str = None) -> CVAnalysisResult:
        """
        Analisa um arquivo de currículo e extrai informações completas
        
        Args:
            file_path: Caminho para o arquivo (PDF, DOCX, TXT)
            user_id: ID do usuário (opcional)
            
        Returns:
            CVAnalysisResult com todas as informações extraídas
        """
        print(f"📄 Analisando currículo: {file_path}")
        
        # Extrair texto do arquivo
        text = self._extract_text(file_path)
        
        if not text:
            raise ValueError("Não foi possível extrair texto do arquivo")
        
        # Análises específicas
        personal_info = self._extract_personal_info(text)
        skills = self._extract_skills(text)
        experience = self._extract_experience(text)
        education = self._extract_education(text)
        preferences = self._extract_preferences(text)
        
        # Determinar senioridade
        seniority = self._determine_seniority(text, experience)
        
        # Estimar faixa salarial
        salary_range = self._estimate_salary_range(skills, seniority, personal_info.get('location'))
        
        # Calcular confiança na análise
        confidence = self._calculate_confidence(personal_info, skills, experience)
        
        # Gerar perfil para recomendações
        generated_profile = self._generate_user_profile(
            user_id or "user_" + str(hash(text))[:8],
            personal_info, skills, experience, preferences, seniority
        )
        
        result = CVAnalysisResult(
            personal_info=personal_info,
            skills=skills,
            experience=experience,
            education=education,
            preferences=preferences,
            seniority_level=seniority,
            estimated_salary_range=salary_range,
            confidence_score=confidence,
            generated_profile=generated_profile
        )
        
        print(f"✅ Análise concluída com {confidence:.1%} de confiança")
        
        return result
    
    def _extract_text(self, file_path: str) -> str:
        """Extrai texto de diferentes tipos de arquivo"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        text = ""
        
        try:
            if file_path.suffix.lower() == '.pdf':
                text = self._extract_from_pdf(file_path)
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                text = self._extract_from_docx(file_path)
            elif file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                raise ValueError(f"Formato não suportado: {file_path.suffix}")
                
        except Exception as e:
            print(f"Erro ao extrair texto: {e}")
            return ""
        
        return text
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extrai texto de PDF"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Erro ao ler PDF: {e}")
            return ""
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extrai texto de DOCX"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Erro ao ler DOCX: {e}")
            return ""
    
    def _extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extrai informações pessoais do currículo"""
        info = {}
        
        # Email
        email_match = self.patterns['email'].search(text)
        if email_match:
            info['email'] = email_match.group()
        
        # Telefone
        phone_match = self.patterns['phone'].search(text)
        if phone_match:
            info['phone'] = phone_match.group()
        
        # LinkedIn
        linkedin_match = self.patterns['linkedin'].search(text)
        if linkedin_match:
            info['linkedin'] = linkedin_match.group(1)
        
        # GitHub
        github_match = self.patterns['github'].search(text)
        if github_match:
            info['github'] = github_match.group(1)
        
        # Nome (primeira linha geralmente)
        lines = text.split('\n')
        for line in lines[:5]:  # Primeiras 5 linhas
            line = line.strip()
            if line and len(line.split()) >= 2 and len(line) < 60:
                # Provavelmente é o nome
                if not any(char.isdigit() for char in line):
                    info['name'] = line
                    break
        
        # Localização (buscar por padrões de cidade/estado)
        location_patterns = [
            r'([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+)*)\s*[-,]\s*([A-Z]{2})',
            r'(?:mora em|reside em|localizado em)\s*([^,\n]+)',
            r'(?:cidade|city):\s*([^,\n]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                info['location'] = match.group(1).strip()
                break
        
        return info
    
    def _extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extrai habilidades técnicas e soft skills"""
        text_lower = text.lower()
        skills = {
            'technical': [],
            'soft': [],
            'by_category': {}
        }
        
        # Buscar tecnologias por categoria
        for category, techs in self.tech_categories.items():
            found_techs = []
            for tech in techs:
                # Busca mais flexível para tecnologias
                tech_variations = [
                    tech,
                    tech.replace('.', ''),
                    tech.replace('-', ''),
                    tech.replace(' ', ''),
                    tech.replace('js', 'javascript') if 'js' in tech else tech
                ]
                
                for variation in tech_variations:
                    if variation in text_lower:
                        found_techs.append(tech)
                        skills['technical'].append(tech)
                        break
            
            if found_techs:
                skills['by_category'][category] = found_techs
        
        # Buscar soft skills
        for skill in self.soft_skills:
            skill_variations = [
                skill,
                skill.replace('ç', 'c'),
                skill.replace('ã', 'a')
            ]
            
            for variation in skill_variations:
                if variation in text_lower:
                    skills['soft'].append(skill)
                    break
        
        # Remover duplicatas
        skills['technical'] = list(set(skills['technical']))
        skills['soft'] = list(set(skills['soft']))
        
        return skills
    
    def _extract_experience(self, text: str) -> Dict[str, Union[int, str, List]]:
        """Extrai informações de experiência profissional"""
        experience = {
            'total_years': 0,
            'companies': [],
            'positions': [],
            'current_position': '',
            'employment_history': []
        }
        
        # Buscar anos de experiência explícitos
        years_match = self.patterns['years_experience'].search(text)
        if years_match:
            experience['total_years'] = int(years_match.group(1))
        
        # Buscar empresas e posições usando padrões comuns
        lines = text.split('\n')
        
        # Padrões para identificar experiência profissional
        company_patterns = [
            r'(?:empresa|company):\s*([^,\n]+)',
            r'([A-Z][a-z\s&]+(?:S\.?A\.?|LTDA\.?|Inc\.?|Corp\.?))',
            r'(?:trabalho em|work at|trabalhei na?)\s*([^,\n]+)'
        ]
        
        position_patterns = [
            r'(?:cargo|position|função):\s*([^,\n]+)',
            r'((?:Desenvolvedor|Analista|Gerente|Coordenador|Diretor)[^,\n]*)',
            r'((?:Developer|Analyst|Manager|Coordinator|Director)[^,\n]*)'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.I)
            experience['companies'].extend([m.strip() for m in matches])
        
        for pattern in position_patterns:
            matches = re.findall(pattern, text, re.I)
            experience['positions'].extend([m.strip() for m in matches])
        
        # Tentar extrair histórico estruturado
        experience['employment_history'] = self._extract_employment_history(text)
        
        # Determinar posição atual (última mencionada ou mais recente)
        if experience['positions']:
            experience['current_position'] = experience['positions'][-1]
        
        # Estimar anos se não explícito
        if experience['total_years'] == 0:
            experience['total_years'] = self._estimate_years_from_history(
                experience['employment_history']
            )
        
        return experience
    
    def _extract_employment_history(self, text: str) -> List[Dict]:
        """Extrai histórico de empregos estruturado"""
        history = []
        
        # Dividir por seções que parecem ser experiências
        sections = re.split(r'\n\s*\n', text)
        
        for section in sections:
            if len(section.strip()) < 50:  # Muito curto para ser experiência
                continue
            
            # Buscar datas na seção
            date_patterns = [
                r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|atual|present)',
                r'(\d{4})\s*[-–]\s*(\d{4}|atual|present)',
                r'(?:desde|from)\s*(\d{1,2}/\d{4}|\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, section, re.I)
                if match:
                    # Encontrou uma experiência com data
                    job_info = {
                        'text': section.strip()[:200],  # Primeiros 200 chars
                        'start_date': match.group(1),
                        'end_date': match.group(2) if len(match.groups()) > 1 else 'atual'
                    }
                    history.append(job_info)
                    break
        
        return history
    
    def _estimate_years_from_history(self, history: List[Dict]) -> int:
        """Estima anos de experiência baseado no histórico"""
        if not history:
            return 0
        
        total_months = 0
        
        for job in history:
            try:
                start = job.get('start_date', '')
                end = job.get('end_date', 'atual')
                
                # Parser simples de datas
                if '/' in start:
                    start_year = int(start.split('/')[-1])
                else:
                    start_year = int(start)
                
                if end.lower() in ['atual', 'present']:
                    end_year = datetime.now().year
                elif '/' in end:
                    end_year = int(end.split('/')[-1])
                else:
                    end_year = int(end)
                
                months = (end_year - start_year) * 12
                total_months += max(0, months)
                
            except (ValueError, IndexError):
                continue
        
        return max(1, total_months // 12)
    
    def _extract_education(self, text: str) -> Dict[str, Union[str, List]]:
        """Extrai informações educacionais"""
        education = {
            'degree': '',
            'institution': '',
            'graduation_year': '',
            'courses': [],
            'certifications': []
        }
        
        # Padrões para formação
        degree_patterns = [
            r'(?:graduação em|bacharel em|licenciatura em|degree in)\s*([^,\n]+)',
            r'((?:Engenharia|Ciência|Bacharelado|Licenciatura)[^,\n]*)',
            r'((?:Engineering|Computer Science|Information Systems)[^,\n]*)'
        ]
        
        for pattern in degree_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                education['degree'] = match.group(1).strip()
                break
        
        # Instituições
        institution_patterns = [
            r'(?:universidade|faculdade|instituto|university|college)\s*([^,\n]+)',
            r'([A-Z]{3,}(?:\s+[A-Z]{2,})*)',  # Siglas de universidades
        ]
        
        for pattern in institution_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                education['institution'] = match.group(1).strip()
                break
        
        # Ano de formação
        grad_match = self.patterns['graduation_year'].search(text)
        if grad_match:
            education['graduation_year'] = grad_match.group(1)
        
        # Cursos e certificações
        course_keywords = ['curso', 'certificação', 'certificate', 'course', 'training']
        for keyword in course_keywords:
            pattern = rf'{keyword}[:\s]*([^,\n]+)'
            matches = re.findall(pattern, text, re.I)
            education['courses'].extend([m.strip() for m in matches])
        
        return education
    
    def _extract_preferences(self, text: str) -> Dict[str, Union[str, List]]:
        """Extrai preferências de trabalho"""
        preferences = {
            'work_mode': 'hibrido',  # Default
            'salary_expectation': None,
            'preferred_locations': [],
            'availability': 'full_time'
        }
        
        text_lower = text.lower()
        
        # Modalidade de trabalho
        for mode, indicators in self.location_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                preferences['work_mode'] = mode
                break
        
        # Expectativa salarial
        salary_match = self.patterns['salary_expectation'].search(text)
        if salary_match:
            salary_str = salary_match.group(1).replace('.', '').replace(',', '.')
            try:
                preferences['salary_expectation'] = float(salary_str)
            except ValueError:
                pass
        
        # Disponibilidade
        if any(word in text_lower for word in ['meio período', 'part time', 'freelance']):
            preferences['availability'] = 'part_time'
        elif any(word in text_lower for word in ['consultoria', 'projeto', 'temporário']):
            preferences['availability'] = 'contract'
        
        return preferences
    
    def _determine_seniority(self, text: str, experience: Dict) -> str:
        """Determina nível de senioridade"""
        text_lower = text.lower()
        
        # Buscar palavras-chave explícitas
        for level, keywords in self.seniority_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return level
        
        # Basear em anos de experiência
        years = experience.get('total_years', 0)
        
        if years == 0:
            return 'junior'
        elif years <= 2:
            return 'junior'
        elif years <= 5:
            return 'pleno'
        elif years <= 8:
            return 'senior'
        else:
            return 'especialista'
    
    def _estimate_salary_range(self, skills: Dict, seniority: str, location: str = None) -> Dict[str, float]:
        """Estima faixa salarial baseada no perfil"""
        
        # Valores base por senioridade (CLT mensal)
        base_salaries = {
            'estagiario': 1500,
            'junior': 3500,
            'pleno': 7000,
            'senior': 12000,
            'especialista': 18000,
            'gerente': 22000,
            'diretor': 35000
        }
        
        base = base_salaries.get(seniority, 7000)
        
        # Multiplicador por tecnologias
        tech_multiplier = 1.0
        valuable_techs = {
            'react': 1.1, 'angular': 1.1, 'python': 1.1, 'java': 1.1,
            'aws': 1.3, 'azure': 1.3, 'kubernetes': 1.4, 'terraform': 1.3,
            'machine learning': 1.5, 'data science': 1.4, 'blockchain': 1.6
        }
        
        for tech in skills.get('technical', []):
            if tech.lower() in valuable_techs:
                tech_multiplier += valuable_techs[tech.lower()] - 1.0
        
        tech_multiplier = min(tech_multiplier, 2.0)  # Limite de 2x
        
        # Multiplicador por localização
        location_multiplier = 1.0
        if location:
            location_lower = location.lower()
            if 'são paulo' in location_lower or 'sp' in location_lower:
                location_multiplier = 1.25
            elif 'rio de janeiro' in location_lower or 'rj' in location_lower:
                location_multiplier = 1.15
            elif 'remoto' in location_lower:
                location_multiplier = 1.05
        
        # Calcular faixa
        estimated_salary = base * tech_multiplier * location_multiplier
        
        return {
            'min': round(estimated_salary * 0.85, -2),  # -15%
            'max': round(estimated_salary * 1.15, -2),  # +15%
            'median': round(estimated_salary, -2)
        }
    
    def _calculate_confidence(self, personal_info: Dict, skills: Dict, experience: Dict) -> float:
        """Calcula confiança na análise"""
        confidence = 0.0
        
        # Informações pessoais (+30%)
        if personal_info.get('email'):
            confidence += 0.1
        if personal_info.get('phone'):
            confidence += 0.1
        if personal_info.get('name'):
            confidence += 0.1
        
        # Habilidades técnicas (+40%)
        tech_count = len(skills.get('technical', []))
        if tech_count >= 5:
            confidence += 0.4
        elif tech_count >= 3:
            confidence += 0.3
        elif tech_count >= 1:
            confidence += 0.2
        
        # Experiência profissional (+30%)
        if experience.get('total_years', 0) > 0:
            confidence += 0.15
        if experience.get('companies'):
            confidence += 0.1
        if experience.get('current_position'):
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _generate_user_profile(self, user_id: str, personal_info: Dict, 
                             skills: Dict, experience: Dict, preferences: Dict,
                             seniority: str) -> UserProfile:
        """Gera perfil de usuário para o sistema de recomendações"""
        
        # Extrair skills técnicas
        technical_skills = skills.get('technical', [])
        
        # Estimar anos de experiência
        experience_years = experience.get('total_years', 0)
        
        # Determinar localização preferida
        location = personal_info.get('location', '')
        preferred_locations = [location] if location else ['São Paulo']
        
        # Modalidade de trabalho
        work_mode = preferences.get('work_mode', 'hibrido')
        
        # Faixa salarial
        salary_expectation = preferences.get('salary_expectation')
        if salary_expectation:
            salary_min = salary_expectation * 0.9
            salary_max = salary_expectation * 1.1
        else:
            # Usar estimativa baseada no perfil
            estimated = self._estimate_salary_range(skills, seniority, location)
            salary_min = estimated['min']
            salary_max = estimated['max']
        
        return UserProfile(
            user_id=user_id,
            skills=technical_skills,
            experience_years=experience_years,
            seniority_level=seniority,
            preferred_locations=preferred_locations,
            preferred_salary_min=salary_min,
            preferred_salary_max=salary_max,
            preferred_companies=[],  # Vazio inicialmente
            avoided_companies=[],    # Vazio inicialmente
            work_mode_preference=work_mode
        )
    
    def save_analysis(self, result: CVAnalysisResult, output_path: str):
        """Salva resultado da análise em arquivo JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Análise salva em: {output_path}")
    
    def get_recommendations_for_cv(self, cv_result: CVAnalysisResult, 
                                  jobs: List[Dict], n_recommendations: int = 10) -> List:
        """
        Gera recomendações baseadas no currículo analisado
        
        Args:
            cv_result: Resultado da análise do CV
            jobs: Lista de vagas disponíveis
            n_recommendations: Número de recomendações
            
        Returns:
            Lista de recomendações personalizadas
        """
        from .job_recommender import JobRecommender
        
        # Criar recomendador
        recommender = JobRecommender()
        
        # Treinar com as vagas
        recommender.fit(jobs)
        
        # Gerar recomendações usando o perfil extraído do CV
        recommendations = recommender.recommend(
            cv_result.generated_profile,
            n_recommendations=n_recommendations
        )
        
        return recommendations


# Exemplo de uso
if __name__ == "__main__":
    analyzer = CVAnalyzer()
    
    # Exemplo de análise (você precisará de um arquivo real)
    cv_path = "exemplo_curriculo.pdf"
    
    try:
        result = analyzer.analyze_cv(cv_path, user_id="user123")
        
        print("=== RESULTADO DA ANÁLISE ===")
        print(f"Nome: {result.personal_info.get('name', 'N/A')}")
        print(f"Email: {result.personal_info.get('email', 'N/A')}")
        print(f"Senioridade: {result.seniority_level}")
        print(f"Anos de experiência: {result.experience['total_years']}")
        print(f"Tecnologias: {', '.join(result.skills['technical'][:10])}")
        print(f"Faixa salarial estimada: R$ {result.estimated_salary_range['min']:,.0f} - R$ {result.estimated_salary_range['max']:,.0f}")
        print(f"Confiança: {result.confidence_score:.1%}")
        
        # Salvar resultado
        analyzer.save_analysis(result, "analise_curriculo.json")
        
    except Exception as e:
        print(f"Erro na análise: {e}")