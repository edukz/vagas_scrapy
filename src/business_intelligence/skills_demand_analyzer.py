"""
Analisador de Skills em Alta Demanda

Este módulo analisa:
- Skills mais requisitadas no mercado
- Tendências de crescimento de tecnologias
- Correlação entre skills e salários
- Análise de gaps de competências
- Projeções de demanda futura
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
import statistics
from dataclasses import dataclass


@dataclass
class SkillData:
    """Representa dados de uma skill específica"""
    name: str
    frequency: int
    avg_salary: float
    growth_trend: str  # 'rising', 'stable', 'declining'
    demand_level: str  # 'high', 'medium', 'low'
    related_positions: List[str]
    market_penetration: float  # 0-100%


class SkillsDemandAnalyzer:
    """
    Analisador de demanda de skills no mercado
    
    Funcionalidades:
    - Extração de skills de descrições de vagas
    - Análise de tendências temporais
    - Correlação skills-salário
    - Identificação de skills emergentes
    - Recomendações de carreira
    """
    
    def __init__(self, data_file: str = "data/business_intelligence/skills_analysis.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Criar diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Carregar dados históricos
        self.skills_data = self._load_skills_data()
        
        # Base de skills conhecidas com categorias
        self.skill_patterns = {
            # Linguagens de programação
            'python': {'category': 'programming', 'aliases': ['python', 'py']},
            'javascript': {'category': 'programming', 'aliases': ['javascript', 'js', 'node.js', 'nodejs']},
            'java': {'category': 'programming', 'aliases': ['java', 'openjdk']},
            'php': {'category': 'programming', 'aliases': ['php']},
            'c#': {'category': 'programming', 'aliases': ['c#', 'csharp', 'c sharp']},
            'golang': {'category': 'programming', 'aliases': ['go', 'golang']},
            'rust': {'category': 'programming', 'aliases': ['rust']},
            'typescript': {'category': 'programming', 'aliases': ['typescript', 'ts']},
            'kotlin': {'category': 'programming', 'aliases': ['kotlin']},
            'swift': {'category': 'programming', 'aliases': ['swift']},
            'scala': {'category': 'programming', 'aliases': ['scala']},
            
            # Frameworks e bibliotecas
            'react': {'category': 'frontend', 'aliases': ['react', 'reactjs', 'react.js']},
            'angular': {'category': 'frontend', 'aliases': ['angular', 'angularjs']},
            'vue': {'category': 'frontend', 'aliases': ['vue', 'vuejs', 'vue.js']},
            'django': {'category': 'backend', 'aliases': ['django']},
            'flask': {'category': 'backend', 'aliases': ['flask']},
            'spring': {'category': 'backend', 'aliases': ['spring', 'spring boot']},
            'laravel': {'category': 'backend', 'aliases': ['laravel']},
            'express': {'category': 'backend', 'aliases': ['express', 'expressjs']},
            'fastapi': {'category': 'backend', 'aliases': ['fastapi', 'fast api']},
            
            # Bancos de dados
            'postgresql': {'category': 'database', 'aliases': ['postgresql', 'postgres', 'psql']},
            'mysql': {'category': 'database', 'aliases': ['mysql']},
            'mongodb': {'category': 'database', 'aliases': ['mongodb', 'mongo']},
            'redis': {'category': 'database', 'aliases': ['redis']},
            'elasticsearch': {'category': 'database', 'aliases': ['elasticsearch', 'elastic']},
            
            # Cloud e DevOps
            'aws': {'category': 'cloud', 'aliases': ['aws', 'amazon web services']},
            'azure': {'category': 'cloud', 'aliases': ['azure', 'microsoft azure']},
            'gcp': {'category': 'cloud', 'aliases': ['gcp', 'google cloud', 'google cloud platform']},
            'docker': {'category': 'devops', 'aliases': ['docker', 'containerization']},
            'kubernetes': {'category': 'devops', 'aliases': ['kubernetes', 'k8s']},
            'terraform': {'category': 'devops', 'aliases': ['terraform']},
            'jenkins': {'category': 'devops', 'aliases': ['jenkins']},
            'git': {'category': 'devops', 'aliases': ['git', 'github', 'gitlab']},
            
            # Data Science e ML
            'machine learning': {'category': 'data_science', 'aliases': ['machine learning', 'ml', 'ai']},
            'data science': {'category': 'data_science', 'aliases': ['data science', 'ciência de dados']},
            'tensorflow': {'category': 'data_science', 'aliases': ['tensorflow']},
            'pytorch': {'category': 'data_science', 'aliases': ['pytorch']},
            'pandas': {'category': 'data_science', 'aliases': ['pandas']},
            'numpy': {'category': 'data_science', 'aliases': ['numpy']},
            'scikit-learn': {'category': 'data_science', 'aliases': ['scikit-learn', 'sklearn']},
            
            # Metodologias
            'agile': {'category': 'methodology', 'aliases': ['agile', 'ágil', 'scrum', 'kanban']},
            'devops': {'category': 'methodology', 'aliases': ['devops']},
            'tdd': {'category': 'methodology', 'aliases': ['tdd', 'test driven development']},
            'microservices': {'category': 'architecture', 'aliases': ['microservices', 'microserviços']},
            
            # Outras skills importantes
            'linux': {'category': 'system', 'aliases': ['linux', 'ubuntu', 'centos']},
            'api': {'category': 'development', 'aliases': ['api', 'rest api', 'restful']},
            'graphql': {'category': 'development', 'aliases': ['graphql']},
            'ci/cd': {'category': 'devops', 'aliases': ['ci/cd', 'continuous integration']},
        }
    
    def _load_skills_data(self) -> Dict:
        """Carrega dados históricos de skills"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "skill_trends": {},
            "time_series": [],
            "salary_correlations": {},
            "last_update": None,
            "statistics": {
                "total_skills_tracked": 0,
                "total_jobs_analyzed": 0
            }
        }
    
    def _save_skills_data(self):
        """Salva dados de skills"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.skills_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados de skills: {e}")
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extrai skills do texto de uma vaga
        
        Args:
            text: Texto da descrição da vaga
            
        Returns:
            Lista de skills encontradas
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = []
        
        # Buscar por cada skill conhecida
        for skill_name, skill_info in self.skill_patterns.items():
            for alias in skill_info['aliases']:
                # Busca por palavra completa
                pattern = r'\b' + re.escape(alias.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    if skill_name not in found_skills:
                        found_skills.append(skill_name)
                    break
        
        return found_skills
    
    def extract_salary_value(self, salary_text: str) -> Optional[float]:
        """Extrai valor salarial do texto"""
        if not salary_text or salary_text.lower() in ['não informado', 'a combinar']:
            return None
        
        # Usar o analisador de salários se disponível
        try:
            from .salary_trend_analyzer import salary_trend_analyzer
            salary_range = salary_trend_analyzer.extract_salary_from_text(salary_text)
            if salary_range:
                return (salary_range[0] + salary_range[1]) / 2
        except:
            pass
        
        return None
    
    def analyze_skills_demand(self, jobs: List[Dict]) -> Dict[str, SkillData]:
        """
        Analisa demanda de skills baseada nas vagas
        
        Args:
            jobs: Lista de vagas para analisar
            
        Returns:
            Dicionário com dados de skills
        """
        skill_aggregates = defaultdict(lambda: {
            'frequency': 0,
            'salaries': [],
            'positions': [],
            'timestamps': [],
            'companies': []
        })
        
        total_jobs = len(jobs)
        
        # Processar cada vaga
        for job in jobs:
            # Extrair skills da descrição
            description = f"{job.get('titulo', '')} {job.get('descricao', '')} {job.get('requisitos', '')}"
            skills = self.extract_skills_from_text(description)
            
            # Agregar dados para cada skill
            for skill in skills:
                skill_aggregates[skill]['frequency'] += 1
                skill_aggregates[skill]['positions'].append(job.get('titulo', ''))
                skill_aggregates[skill]['companies'].append(job.get('empresa', ''))
                skill_aggregates[skill]['timestamps'].append(
                    job.get('data_coleta', datetime.now().isoformat())
                )
                
                # Tentar extrair salário
                salary = self.extract_salary_value(job.get('salario', ''))
                if salary:
                    skill_aggregates[skill]['salaries'].append(salary)
        
        # Converter para objetos SkillData
        skills_data = {}
        
        for skill, data in skill_aggregates.items():
            # Calcular estatísticas salariais
            if data['salaries']:
                avg_salary = statistics.mean(data['salaries'])
            else:
                avg_salary = 0
            
            # Calcular penetração de mercado
            market_penetration = (data['frequency'] / total_jobs) * 100 if total_jobs > 0 else 0
            
            # Analisar tendência de crescimento
            growth_trend = self._analyze_skill_growth(skill, data['timestamps'])
            
            # Determinar nível de demanda
            demand_level = self._calculate_demand_level(data['frequency'], market_penetration)
            
            # Posições relacionadas mais comuns
            position_counts = Counter(data['positions'])
            related_positions = [pos for pos, count in position_counts.most_common(5)]
            
            skills_data[skill] = SkillData(
                name=skill,
                frequency=data['frequency'],
                avg_salary=avg_salary,
                growth_trend=growth_trend,
                demand_level=demand_level,
                related_positions=related_positions,
                market_penetration=market_penetration
            )
        
        # Salvar dados agregados
        self.skills_data["skill_trends"] = {
            skill: {
                'name': sd.name,
                'frequency': sd.frequency,
                'avg_salary': sd.avg_salary,
                'growth_trend': sd.growth_trend,
                'demand_level': sd.demand_level,
                'related_positions': sd.related_positions,
                'market_penetration': sd.market_penetration,
                'last_update': datetime.now().isoformat()
            }
            for skill, sd in skills_data.items()
        }
        
        # Atualizar estatísticas
        self.skills_data["statistics"] = {
            "total_skills_tracked": len(skills_data),
            "total_jobs_analyzed": total_jobs,
            "last_analysis": datetime.now().isoformat()
        }
        
        self._save_skills_data()
        return skills_data
    
    def _analyze_skill_growth(self, skill: str, timestamps: List[str]) -> str:
        """Analisa tendência de crescimento da skill"""
        if len(timestamps) < 5:
            return 'stable'
        
        try:
            # Agrupar por semana
            weekly_counts = defaultdict(int)
            for timestamp in timestamps:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    week_key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
                    weekly_counts[week_key] += 1
                except:
                    continue
            
            if len(weekly_counts) < 3:
                return 'stable'
            
            # Verificar tendência das últimas semanas
            sorted_weeks = sorted(weekly_counts.items())
            recent_weeks = sorted_weeks[-4:]  # Últimas 4 semanas
            
            if len(recent_weeks) < 3:
                return 'stable'
            
            # Calcular tendência
            counts = [count for week, count in recent_weeks]
            first_half = statistics.mean(counts[:len(counts)//2])
            second_half = statistics.mean(counts[len(counts)//2:])
            
            if second_half > first_half * 1.3:
                return 'rising'
            elif second_half < first_half * 0.7:
                return 'declining'
            else:
                return 'stable'
        
        except Exception:
            return 'stable'
    
    def _calculate_demand_level(self, frequency: int, market_penetration: float) -> str:
        """Calcula nível de demanda da skill"""
        if frequency >= 50 or market_penetration >= 25:
            return 'high'
        elif frequency >= 20 or market_penetration >= 10:
            return 'medium'
        else:
            return 'low'
    
    def get_trending_skills(self, min_frequency: int = 5) -> List[Dict]:
        """
        Retorna skills em alta no mercado
        
        Args:
            min_frequency: Frequência mínima para considerar
            
        Returns:
            Lista de skills trending
        """
        trending = []
        
        if not self.skills_data.get("skill_trends"):
            return trending
        
        for skill, data in self.skills_data["skill_trends"].items():
            if (data['frequency'] >= min_frequency and 
                data['growth_trend'] == 'rising'):
                
                trending.append({
                    'skill': skill,
                    'frequency': data['frequency'],
                    'growth_trend': data['growth_trend'],
                    'market_penetration': data['market_penetration'],
                    'avg_salary': data['avg_salary'],
                    'demand_level': data['demand_level']
                })
        
        # Ordenar por penetração de mercado e frequência
        trending.sort(key=lambda x: (x['market_penetration'], x['frequency']), reverse=True)
        return trending
    
    def get_high_value_skills(self, min_salary: float = 5000) -> List[Dict]:
        """
        Retorna skills com maior valor salarial
        
        Args:
            min_salary: Salário mínimo para considerar
            
        Returns:
            Lista de skills de alto valor
        """
        high_value = []
        
        if not self.skills_data.get("skill_trends"):
            return high_value
        
        for skill, data in self.skills_data["skill_trends"].items():
            if data['avg_salary'] >= min_salary:
                high_value.append({
                    'skill': skill,
                    'avg_salary': data['avg_salary'],
                    'frequency': data['frequency'],
                    'market_penetration': data['market_penetration'],
                    'demand_level': data['demand_level']
                })
        
        # Ordenar por salário médio
        high_value.sort(key=lambda x: x['avg_salary'], reverse=True)
        return high_value
    
    def get_skills_by_category(self) -> Dict[str, List[Dict]]:
        """Agrupa skills por categoria"""
        categories = defaultdict(list)
        
        if not self.skills_data.get("skill_trends"):
            return dict(categories)
        
        for skill, data in self.skills_data["skill_trends"].items():
            category = self.skill_patterns.get(skill, {}).get('category', 'other')
            
            categories[category].append({
                'skill': skill,
                'frequency': data['frequency'],
                'avg_salary': data['avg_salary'],
                'demand_level': data['demand_level'],
                'growth_trend': data['growth_trend']
            })
        
        # Ordenar cada categoria por frequência
        for category in categories:
            categories[category].sort(key=lambda x: x['frequency'], reverse=True)
        
        return dict(categories)
    
    def get_career_recommendations(self, current_skills: List[str] = None) -> Dict:
        """
        Gera recomendações de carreira baseadas em skills
        
        Args:
            current_skills: Skills atuais do usuário
            
        Returns:
            Recomendações personalizadas
        """
        recommendations = {
            'skills_to_learn': [],
            'market_opportunities': [],
            'salary_potential': {},
            'career_paths': [],
            'emerging_technologies': []
        }
        
        if not self.skills_data.get("skill_trends"):
            return recommendations
        
        # Skills em alta para aprender
        trending = self.get_trending_skills()
        recommendations['skills_to_learn'] = trending[:5]
        
        # Skills de alto valor
        high_value = self.get_high_value_skills()
        recommendations['market_opportunities'] = high_value[:5]
        
        # Skills emergentes
        emerging = [
            skill for skill, data in self.skills_data["skill_trends"].items()
            if (data['growth_trend'] == 'rising' and 
                data['market_penetration'] < 15 and 
                data['frequency'] >= 3)
        ]
        recommendations['emerging_technologies'] = emerging[:5]
        
        # Análise baseada em skills atuais
        if current_skills:
            related_opportunities = self._find_related_opportunities(current_skills)
            recommendations['career_paths'] = related_opportunities
        
        return recommendations
    
    def _find_related_opportunities(self, current_skills: List[str]) -> List[Dict]:
        """Encontra oportunidades relacionadas às skills atuais"""
        opportunities = []
        
        # Buscar skills complementares baseadas em padrões de mercado
        skill_categories = self.get_skills_by_category()
        
        for skill in current_skills:
            if skill in self.skill_patterns:
                category = self.skill_patterns[skill]['category']
                related_skills = skill_categories.get(category, [])
                
                for related in related_skills[:3]:
                    if related['skill'] != skill:
                        opportunities.append({
                            'recommended_skill': related['skill'],
                            'reason': f"Complementa {skill} ({category})",
                            'market_demand': related['demand_level'],
                            'avg_salary': related['avg_salary']
                        })
        
        return opportunities[:10]
    
    def print_skills_analysis_report(self):
        """Imprime relatório de análise de skills"""
        from ..utils.menu_system import Colors
        
        print(f"\n{Colors.CYAN}🔧 ANÁLISE DE SKILLS EM DEMANDA{Colors.RESET}")
        print("=" * 60)
        
        # Estatísticas gerais
        stats = self.skills_data.get("statistics", {})
        if stats:
            print(f"\n{Colors.YELLOW}📊 Estatísticas Gerais:{Colors.RESET}")
            print(f"  • Skills rastreadas: {stats.get('total_skills_tracked', 0)}")
            print(f"  • Vagas analisadas: {stats.get('total_jobs_analyzed', 0)}")
        
        # Skills em alta
        trending = self.get_trending_skills()
        if trending:
            print(f"\n{Colors.GREEN}📈 Skills em Alta Demanda:{Colors.RESET}")
            for i, skill in enumerate(trending[:10], 1):
                growth_emoji = "🚀" if skill['growth_trend'] == 'rising' else "📊"
                salary_info = f" - R$ {skill['avg_salary']:,.2f}" if skill['avg_salary'] > 0 else ""
                print(f"  {i}. {skill['skill']} {growth_emoji}")
                print(f"     {skill['frequency']} vagas ({skill['market_penetration']:.1f}%){salary_info}")
        
        # Skills de alto valor
        high_value = self.get_high_value_skills()
        if high_value:
            print(f"\n{Colors.GREEN}💰 Skills de Maior Valor Salarial:{Colors.RESET}")
            for i, skill in enumerate(high_value[:5], 1):
                demand_emoji = {
                    'high': '🔥',
                    'medium': '📊', 
                    'low': '📉'
                }.get(skill['demand_level'], '')
                print(f"  {i}. {skill['skill']}: R$ {skill['avg_salary']:,.2f} {demand_emoji}")
                print(f"     {skill['frequency']} vagas ({skill['market_penetration']:.1f}%)")
        
        # Skills por categoria
        categories = self.get_skills_by_category()
        if categories:
            print(f"\n{Colors.BLUE}🗂 Skills por Categoria:{Colors.RESET}")
            category_emojis = {
                'programming': '💻',
                'frontend': '🎨',
                'backend': '⚙️',
                'database': '🗄️',
                'cloud': '☁️',
                'devops': '🔧',
                'data_science': '📊',
                'methodology': '📋'
            }
            
            for category, skills in categories.items():
                if skills:
                    emoji = category_emojis.get(category, '📌')
                    print(f"\n  {emoji} {category.replace('_', ' ').title()}:")
                    for skill in skills[:3]:
                        print(f"    • {skill['skill']} ({skill['frequency']} vagas)")
        
        print("\n" + "=" * 60)


# Instância global do analisador de skills
skills_demand_analyzer = SkillsDemandAnalyzer()