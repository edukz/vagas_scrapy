"""
Analisador de Currículos Simplificado
====================================

Versão sem dependências externas pesadas para funcionar em qualquer ambiente.
Foca na extração de informações e criação de perfis sem Machine Learning complexo.
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime


@dataclass
class SimpleCVResult:
    """Resultado simplificado da análise do currículo"""
    personal_info: Dict[str, str]
    skills: Dict[str, List[str]]
    experience: Dict[str, Union[int, str, List]]
    education: Dict[str, Union[str, List]]
    preferences: Dict[str, Union[str, List]]
    seniority_level: str
    estimated_salary_range: Dict[str, float]
    confidence_score: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SimpleCVAnalyzer:
    """
    Analisador de currículos simplificado sem dependências externas
    """
    
    def __init__(self):
        # Tecnologias por categoria (versão simplificada)
        self.tech_categories = {
            'linguagens': {
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 
                'ruby', 'go', 'rust', 'kotlin', 'swift', 'scala', 'r'
            },
            'frontend': {
                'react', 'angular', 'vue', 'svelte', 'html', 'css', 'sass',
                'jquery', 'bootstrap', 'tailwind'
            },
            'backend': {
                'node.js', 'express', 'django', 'flask', 'spring', 'laravel',
                'rails', '.net', 'fastapi'
            },
            'mobile': {
                'react native', 'flutter', 'ionic', 'xamarin', 'android', 'ios'
            },
            'databases': {
                'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle',
                'cassandra', 'elasticsearch'
            },
            'cloud_devops': {
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
                'jenkins', 'gitlab ci', 'github actions'
            },
            'data_science': {
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
                'tableau', 'power bi', 'jupyter', 'spark'
            }
        }
        
        # Todas as tecnologias em um set
        self.all_technologies = set()
        for category in self.tech_categories.values():
            self.all_technologies.update(category)
        
        # Soft skills
        self.soft_skills = {
            'liderança', 'comunicação', 'trabalho em equipe', 'gestão de projetos',
            'resolução de problemas', 'criatividade', 'adaptabilidade', 'organização',
            'proatividade', 'autonomia', 'colaboração', 'mentoria'
        }
        
        # Padrões regex para extração
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'(?:\+55\s?)?(?:\(?[1-9][1-9]\)?\s?)?(?:9\s?)?[0-9]{4}[-\s]?[0-9]{4}'),
            'linkedin': re.compile(r'linkedin\.com/in/([A-Za-z0-9-]+)'),
            'github': re.compile(r'github\.com/([A-Za-z0-9-]+)'),
            'years_experience': re.compile(r'(\d+)\s*(?:anos?|years?)\s*(?:de\s*)?(?:experiência|experience)', re.I),
            'salary': re.compile(r'(?:R\$|salário)[\s]*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', re.I),
        }
        
        # Níveis de senioridade
        self.seniority_keywords = {
            'estagiario': ['estagiário', 'trainee', 'aprendiz', 'intern'],
            'junior': ['júnior', 'junior', 'jr', 'iniciante'],
            'pleno': ['pleno', 'analista', 'desenvolvedor'],
            'senior': ['sênior', 'senior', 'sr', 'especialista'],
            'lider': ['arquiteto', 'tech lead', 'líder técnico', 'coordenador'],
            'gerente': ['gerente', 'manager', 'diretor']
        }
    
    def analyze_cv(self, file_path: str, user_id: str = None) -> SimpleCVResult:
        """Analisa um currículo e retorna informações extraídas"""
        print(f"📄 Analisando currículo: {file_path}")
        
        # Extrair texto
        text = self._extract_text(file_path)
        if not text:
            raise ValueError("Não foi possível extrair texto do arquivo")
        
        # Extrair informações
        personal_info = self._extract_personal_info(text)
        skills = self._extract_skills(text)
        experience = self._extract_experience(text)
        education = self._extract_education(text)
        preferences = self._extract_preferences(text)
        
        # Determinar senioridade
        seniority = self._determine_seniority(text, experience)
        
        # Estimar salário
        salary_range = self._estimate_salary(skills, seniority, personal_info.get('location'))
        
        # Calcular confiança
        confidence = self._calculate_confidence(personal_info, skills, experience)
        
        result = SimpleCVResult(
            personal_info=personal_info,
            skills=skills,
            experience=experience,
            education=education,
            preferences=preferences,
            seniority_level=seniority,
            estimated_salary_range=salary_range,
            confidence_score=confidence
        )
        
        print(f"✅ Análise concluída com {confidence:.1%} de confiança")
        return result
    
    def _extract_text(self, file_path: str) -> str:
        """Extrai texto do arquivo (apenas TXT por simplicidade)"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        if file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Formato não suportado nesta versão simplificada: {file_path.suffix}")
    
    def _extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extrai informações pessoais"""
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
        
        # Nome (primeira linha não vazia)
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line.split()) >= 2 and len(line) < 60:
                if not any(char.isdigit() for char in line):
                    info['name'] = line
                    break
        
        # Localização
        location_patterns = [
            r'([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-záéíóúâêîôûãõç]+)*)\s*[-,]\s*([A-Z]{2})',
            r'(?:localização|cidade):\s*([^,\n]+)'
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
        
        # Tecnologias por categoria
        for category, techs in self.tech_categories.items():
            found_techs = []
            for tech in techs:
                if tech in text_lower:
                    found_techs.append(tech)
                    skills['technical'].append(tech)
            
            if found_techs:
                skills['by_category'][category] = found_techs
        
        # Soft skills
        for skill in self.soft_skills:
            if skill in text_lower:
                skills['soft'].append(skill)
        
        # Remover duplicatas
        skills['technical'] = list(set(skills['technical']))
        skills['soft'] = list(set(skills['soft']))
        
        return skills
    
    def _extract_experience(self, text: str) -> Dict[str, Union[int, str, List]]:
        """Extrai experiência profissional"""
        experience = {
            'total_years': 0,
            'companies': [],
            'positions': [],
            'current_position': ''
        }
        
        # Anos de experiência
        years_match = self.patterns['years_experience'].search(text)
        if years_match:
            experience['total_years'] = int(years_match.group(1))
        
        # Empresas e posições (padrões simples)
        company_patterns = [
            r'([A-Z][a-z\s&]+(?:S\.?A\.?|LTDA\.?|Inc\.?|Corp\.?))',
            r'(?:empresa|company):\s*([^,\n]+)'
        ]
        
        position_patterns = [
            r'((?:Desenvolvedor|Analista|Gerente|Coordenador|Diretor)[^,\n]*)',
            r'(?:cargo|position):\s*([^,\n]+)'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.I)
            experience['companies'].extend([m.strip() for m in matches])
        
        for pattern in position_patterns:
            matches = re.findall(pattern, text, re.I)
            experience['positions'].extend([m.strip() for m in matches])
        
        if experience['positions']:
            experience['current_position'] = experience['positions'][-1]
        
        return experience
    
    def _extract_education(self, text: str) -> Dict[str, Union[str, List]]:
        """Extrai informações educacionais"""
        education = {
            'degree': '',
            'institution': '',
            'courses': []
        }
        
        # Formação
        degree_patterns = [
            r'(?:graduação em|bacharel em|degree in)\s*([^,\n]+)',
            r'((?:Engenharia|Ciência|Bacharelado)[^,\n]*)'
        ]
        
        for pattern in degree_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                education['degree'] = match.group(1).strip()
                break
        
        # Instituição
        institution_patterns = [
            r'(?:universidade|faculdade|university)\s*([^,\n]+)',
            r'([A-Z]{3,}(?:\s+[A-Z]{2,})*)'
        ]
        
        for pattern in institution_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                education['institution'] = match.group(1).strip()
                break
        
        return education
    
    def _extract_preferences(self, text: str) -> Dict[str, Union[str, List]]:
        """Extrai preferências de trabalho"""
        preferences = {
            'work_mode': 'hibrido',
            'salary_expectation': None
        }
        
        text_lower = text.lower()
        
        # Modalidade de trabalho
        if any(word in text_lower for word in ['remoto', 'remote', 'home office']):
            preferences['work_mode'] = 'remoto'
        elif any(word in text_lower for word in ['híbrido', 'hybrid', 'flexível']):
            preferences['work_mode'] = 'hibrido'
        elif any(word in text_lower for word in ['presencial', 'escritório']):
            preferences['work_mode'] = 'presencial'
        
        # Expectativa salarial
        salary_match = self.patterns['salary'].search(text)
        if salary_match:
            try:
                salary_str = salary_match.group(1).replace('.', '').replace(',', '.')
                preferences['salary_expectation'] = float(salary_str)
            except ValueError:
                pass
        
        return preferences
    
    def _determine_seniority(self, text: str, experience: Dict) -> str:
        """Determina nível de senioridade"""
        text_lower = text.lower()
        
        # Buscar palavras-chave
        for level, keywords in self.seniority_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return level
        
        # Basear em anos de experiência
        years = experience.get('total_years', 0)
        if years <= 2:
            return 'junior'
        elif years <= 5:
            return 'pleno'
        elif years <= 8:
            return 'senior'
        else:
            return 'lider'
    
    def _estimate_salary(self, skills: Dict, seniority: str, location: str = None) -> Dict[str, float]:
        """Estima faixa salarial"""
        base_salaries = {
            'estagiario': 1500,
            'junior': 3500,
            'pleno': 7000,
            'senior': 12000,
            'lider': 18000,
            'gerente': 25000
        }
        
        base = base_salaries.get(seniority, 7000)
        
        # Multiplicador por tecnologias
        tech_count = len(skills.get('technical', []))
        tech_multiplier = 1 + (tech_count * 0.05)  # 5% por tecnologia
        
        # Multiplicador por localização
        location_multiplier = 1.0
        if location:
            location_lower = location.lower()
            if 'são paulo' in location_lower:
                location_multiplier = 1.25
            elif 'rio de janeiro' in location_lower:
                location_multiplier = 1.15
            elif 'remoto' in location_lower:
                location_multiplier = 1.05
        
        estimated = base * tech_multiplier * location_multiplier
        
        return {
            'min': round(estimated * 0.85, -2),
            'max': round(estimated * 1.15, -2),
            'median': round(estimated, -2)
        }
    
    def _calculate_confidence(self, personal_info: Dict, skills: Dict, experience: Dict) -> float:
        """Calcula confiança na análise"""
        confidence = 0.0
        
        # Informações pessoais (+30%)
        if personal_info.get('email'):
            confidence += 0.1
        if personal_info.get('name'):
            confidence += 0.1
        if personal_info.get('phone'):
            confidence += 0.1
        
        # Habilidades (+40%)
        tech_count = len(skills.get('technical', []))
        if tech_count >= 5:
            confidence += 0.4
        elif tech_count >= 3:
            confidence += 0.3
        elif tech_count >= 1:
            confidence += 0.2
        
        # Experiência (+30%)
        if experience.get('total_years', 0) > 0:
            confidence += 0.15
        if experience.get('companies'):
            confidence += 0.1
        if experience.get('current_position'):
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def save_analysis(self, result: SimpleCVResult, output_path: str):
        """Salva análise em arquivo JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        print(f"✅ Análise salva em: {output_path}")


# Exemplo de uso
if __name__ == "__main__":
    analyzer = SimpleCVAnalyzer()
    
    # Teste com arquivo exemplo
    try:
        result = analyzer.analyze_cv("exemplo_curriculo.txt", "user123")
        
        print("\n=== RESULTADO DA ANÁLISE ===")
        print(f"Nome: {result.personal_info.get('name', 'N/A')}")
        print(f"Email: {result.personal_info.get('email', 'N/A')}")
        print(f"Senioridade: {result.seniority_level}")
        print(f"Anos de experiência: {result.experience['total_years']}")
        print(f"Tecnologias: {', '.join(result.skills['technical'][:10])}")
        print(f"Faixa salarial: R$ {result.estimated_salary_range['min']:,.0f} - R$ {result.estimated_salary_range['max']:,.0f}")
        print(f"Confiança: {result.confidence_score:.1%}")
        
    except Exception as e:
        print(f"Erro: {e}")