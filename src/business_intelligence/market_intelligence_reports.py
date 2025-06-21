"""
Sistema de Relatórios de Inteligência de Mercado

Este módulo gera relatórios executivos abrangentes:
- Dashboard de mercado em tempo real
- Relatórios de tendências setoriais
- Análise competitiva
- Insights preditivos
- Relatórios personalizados por perfil
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import statistics


@dataclass
class MarketInsight:
    """Representa um insight de mercado"""
    title: str
    category: str
    impact_level: str  # 'high', 'medium', 'low'
    description: str
    data_points: List[Dict]
    recommendations: List[str]
    confidence_score: float  # 0-100


class MarketIntelligenceReports:
    """
    Gerador de relatórios de inteligência de mercado
    
    Funcionalidades:
    - Consolidação de dados de múltiplas fontes
    - Geração de insights automáticos
    - Relatórios executivos
    - Dashboards interativos
    - Alertas de mercado
    """
    
    def __init__(self, data_file: str = "data/business_intelligence/market_reports.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Criar diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Carregar dados de relatórios
        self.reports_data = self._load_reports_data()
        
        # Inicializar analisadores
        self._initialize_analyzers()
    
    def _initialize_analyzers(self):
        """Inicializa os analisadores de BI"""
        try:
            from .salary_trend_analyzer import salary_trend_analyzer
            from src.systems.diversity_analyzer import diversity_analyzer
            from .regional_heatmap import regional_heatmap
            from .skills_demand_analyzer import skills_demand_analyzer
            
            self.analyzers = {
                'salary': salary_trend_analyzer,
                'diversity': diversity_analyzer,
                'regional': regional_heatmap,
                'skills': skills_demand_analyzer
            }
        except ImportError as e:
            print(f"Aviso: Alguns analisadores não estão disponíveis: {e}")
            self.analyzers = {}
    
    def _load_reports_data(self) -> Dict:
        """Carrega dados históricos de relatórios"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "reports_history": [],
            "insights_cache": {},
            "dashboards": {},
            "alerts": [],
            "last_update": None,
            "statistics": {
                "total_reports_generated": 0,
                "total_insights": 0
            }
        }
    
    def _save_reports_data(self):
        """Salva dados de relatórios"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.reports_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados de relatórios: {e}")
    
    def generate_executive_dashboard(self, jobs: List[Dict]) -> Dict:
        """
        Gera dashboard executivo com principais KPIs
        
        Args:
            jobs: Lista de vagas para analisar
            
        Returns:
            Dashboard com métricas executivas
        """
        dashboard = {
            'generation_date': datetime.now().isoformat(),
            'total_jobs_analyzed': len(jobs),
            'market_overview': {},
            'key_metrics': {},
            'trends': {},
            'alerts': [],
            'recommendations': []
        }
        
        if not jobs:
            dashboard['market_overview']['status'] = 'Dados insuficientes'
            return dashboard
        
        # Visão geral do mercado
        dashboard['market_overview'] = self._generate_market_overview(jobs)
        
        # Métricas-chave
        dashboard['key_metrics'] = self._calculate_key_metrics(jobs)
        
        # Análise de tendências
        dashboard['trends'] = self._analyze_market_trends(jobs)
        
        # Alertas automáticos
        dashboard['alerts'] = self._generate_market_alerts(dashboard)
        
        # Recomendações executivas
        dashboard['recommendations'] = self._generate_executive_recommendations(dashboard)
        
        # Salvar dashboard
        self.reports_data["dashboards"]["executive"] = dashboard
        self._save_reports_data()
        
        return dashboard
    
    def _generate_market_overview(self, jobs: List[Dict]) -> Dict:
        """Gera visão geral do mercado"""
        overview = {
            'market_size': len(jobs),
            'job_posting_velocity': 0,
            'market_temperature': 'neutral',
            'dominant_sectors': [],
            'geographic_distribution': {},
            'remote_work_percentage': 0
        }
        
        try:
            # Velocidade de postagem (jobs dos últimos 7 dias)
            recent_jobs = 0
            week_ago = datetime.now() - timedelta(days=7)
            
            for job in jobs:
                try:
                    job_date = datetime.fromisoformat(job.get('data_coleta', '').replace('Z', '+00:00'))
                    if job_date >= week_ago:
                        recent_jobs += 1
                except:
                    continue
            
            overview['job_posting_velocity'] = recent_jobs
            
            # Temperatura do mercado
            if recent_jobs > len(jobs) * 0.4:  # 40% das vagas são recentes
                overview['market_temperature'] = 'hot'
            elif recent_jobs > len(jobs) * 0.2:  # 20% das vagas são recentes
                overview['market_temperature'] = 'warm'
            else:
                overview['market_temperature'] = 'cool'
            
            # Setores dominantes (baseado em títulos)
            sector_keywords = {
                'tecnologia': ['desenvolvedor', 'programador', 'tech', 'software', 'ti'],
                'vendas': ['vendedor', 'vendas', 'comercial'],
                'marketing': ['marketing', 'digital', 'social media'],
                'recursos_humanos': ['rh', 'recursos humanos', 'pessoas'],
                'financeiro': ['financeiro', 'contabil', 'contador'],
                'saude': ['enfermeiro', 'medico', 'saude', 'hospital']
            }
            
            sector_counts = {sector: 0 for sector in sector_keywords}
            
            for job in jobs:
                titulo = job.get('titulo', '').lower()
                for sector, keywords in sector_keywords.items():
                    if any(keyword in titulo for keyword in keywords):
                        sector_counts[sector] += 1
                        break
            
            # Top 3 setores
            sorted_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)
            overview['dominant_sectors'] = [
                {'sector': sector, 'job_count': count, 'percentage': (count/len(jobs))*100}
                for sector, count in sorted_sectors[:3] if count > 0
            ]
            
            # Distribuição geográfica
            if 'regional' in self.analyzers:
                regional_data = self.analyzers['regional'].analyze_jobs_by_region(jobs)
                overview['geographic_distribution'] = {
                    region: data.job_count for region, data in regional_data.items()
                }
            
            # Percentual de trabalho remoto
            remote_count = 0
            for job in jobs:
                location = job.get('localizacao', '').lower()
                if any(term in location for term in ['remoto', 'home office', 'hibrido']):
                    remote_count += 1
            
            overview['remote_work_percentage'] = (remote_count / len(jobs)) * 100
            
        except Exception as e:
            print(f"Erro ao gerar visão geral: {e}")
        
        return overview
    
    def _calculate_key_metrics(self, jobs: List[Dict]) -> Dict:
        """Calcula métricas-chave do mercado"""
        metrics = {
            'avg_salary': 0,
            'salary_range': {'min': 0, 'max': 0},
            'top_skills': [],
            'top_companies': [],
            'job_types': {},
            'experience_levels': {}
        }
        
        try:
            # Análise salarial
            if 'salary' in self.analyzers:
                salaries = []
                for job in jobs:
                    salary_analysis = self.analyzers['salary'].analyze_job_salary(job)
                    if salary_analysis and salary_analysis.get('avg_salary'):
                        salaries.append(salary_analysis['avg_salary'])
                
                if salaries:
                    metrics['avg_salary'] = statistics.mean(salaries)
                    metrics['salary_range'] = {
                        'min': min(salaries),
                        'max': max(salaries)
                    }
            
            # Top skills
            if 'skills' in self.analyzers:
                skills_data = self.analyzers['skills'].analyze_skills_demand(jobs)
                top_skills = sorted(
                    [(skill, data.frequency) for skill, data in skills_data.items()],
                    key=lambda x: x[1], reverse=True
                )[:5]
                metrics['top_skills'] = [
                    {'skill': skill, 'frequency': freq} for skill, freq in top_skills
                ]
            
            # Top empresas
            company_counts = {}
            for job in jobs:
                company = job.get('empresa', '').strip()
                if company and company.lower() != 'não informado':
                    company_counts[company] = company_counts.get(company, 0) + 1
            
            top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            metrics['top_companies'] = [
                {'company': company, 'job_count': count} for company, count in top_companies
            ]
            
            # Tipos de trabalho
            work_type_keywords = {
                'clt': ['clt', 'efetivo'],
                'pj': ['pj', 'pessoa juridica', 'freelancer'],
                'estagio': ['estagio', 'trainee'],
                'temporario': ['temporario', 'contrato']
            }
            
            type_counts = {wtype: 0 for wtype in work_type_keywords}
            for job in jobs:
                description = f"{job.get('titulo', '')} {job.get('descricao', '')}".lower()
                for wtype, keywords in work_type_keywords.items():
                    if any(keyword in description for keyword in keywords):
                        type_counts[wtype] += 1
                        break
            
            total_typed = sum(type_counts.values())
            if total_typed > 0:
                metrics['job_types'] = {
                    wtype: (count / total_typed) * 100 
                    for wtype, count in type_counts.items() if count > 0
                }
            
        except Exception as e:
            print(f"Erro ao calcular métricas: {e}")
        
        return metrics
    
    def _analyze_market_trends(self, jobs: List[Dict]) -> Dict:
        """Analisa tendências de mercado"""
        trends = {
            'growth_sectors': [],
            'declining_sectors': [],
            'emerging_skills': [],
            'salary_trends': {},
            'regional_trends': {}
        }
        
        try:
            # Tendências salariais
            if 'salary' in self.analyzers:
                salary_insights = self.analyzers['salary'].get_market_insights()
                trends['salary_trends'] = salary_insights.get('trends', {})
            
            # Skills emergentes
            if 'skills' in self.analyzers:
                trending_skills = self.analyzers['skills'].get_trending_skills()
                trends['emerging_skills'] = trending_skills[:5]
            
            # Tendências regionais
            if 'regional' in self.analyzers:
                regional_insights = self.analyzers['regional'].get_regional_insights()
                trends['regional_trends'] = {
                    'emerging_markets': regional_insights.get('emerging_markets', []),
                    'hottest_regions': regional_insights.get('hottest_regions', [])[:3]
                }
            
        except Exception as e:
            print(f"Erro ao analisar tendências: {e}")
        
        return trends
    
    def _generate_market_alerts(self, dashboard: Dict) -> List[Dict]:
        """Gera alertas automáticos baseados no dashboard"""
        alerts = []
        
        try:
            # Alerta de mercado quente
            market_temp = dashboard['market_overview'].get('market_temperature', 'neutral')
            if market_temp == 'hot':
                alerts.append({
                    'type': 'opportunity',
                    'severity': 'high',
                    'message': 'Mercado aquecido: Alta velocidade de postagem de vagas',
                    'action': 'Considere acelerar processos de recrutamento'
                })
            
            # Alerta de trabalho remoto
            remote_pct = dashboard['market_overview'].get('remote_work_percentage', 0)
            if remote_pct > 30:
                alerts.append({
                    'type': 'trend',
                    'severity': 'medium',
                    'message': f'Alto índice de trabalho remoto: {remote_pct:.1f}%',
                    'action': 'Considere políticas de trabalho flexível'
                })
            
            # Alerta de salários
            avg_salary = dashboard['key_metrics'].get('avg_salary', 0)
            if avg_salary > 8000:
                alerts.append({
                    'type': 'market',
                    'severity': 'medium',
                    'message': f'Salários acima da média: R$ {avg_salary:,.2f}',
                    'action': 'Mercado competitivo em salários'
                })
            
        except Exception as e:
            print(f"Erro ao gerar alertas: {e}")
        
        return alerts
    
    def _generate_executive_recommendations(self, dashboard: Dict) -> List[str]:
        """Gera recomendações executivas"""
        recommendations = []
        
        try:
            # Recomendações baseadas em temperatura do mercado
            market_temp = dashboard['market_overview'].get('market_temperature', 'neutral')
            if market_temp == 'hot':
                recommendations.append(
                    "Mercado aquecido: Acelere processos de contratação para aproveitar alta demanda"
                )
            elif market_temp == 'cool':
                recommendations.append(
                    "Mercado desaquecido: Momento ideal para atrair talentos com ofertas competitivas"
                )
            
            # Recomendações de skills
            emerging_skills = dashboard['trends'].get('emerging_skills', [])
            if emerging_skills:
                top_skill = emerging_skills[0]['skill']
                recommendations.append(
                    f"Invista em capacitação: {top_skill} está em alta demanda"
                )
            
            # Recomendações regionais
            regional_trends = dashboard['trends'].get('regional_trends', {})
            emerging_markets = regional_trends.get('emerging_markets', [])
            if emerging_markets:
                market = emerging_markets[0]['region']
                recommendations.append(
                    f"Explore mercado emergente: {market} apresenta crescimento"
                )
            
            # Recomendação de trabalho remoto
            remote_pct = dashboard['market_overview'].get('remote_work_percentage', 0)
            if remote_pct > 25:
                recommendations.append(
                    "Considere expandir opções de trabalho remoto para competir melhor"
                )
            
        except Exception as e:
            print(f"Erro ao gerar recomendações: {e}")
        
        return recommendations
    
    def generate_sector_report(self, jobs: List[Dict], sector: str) -> Dict:
        """Gera relatório específico por setor"""
        report = {
            'sector': sector,
            'generation_date': datetime.now().isoformat(),
            'job_count': 0,
            'avg_salary': 0,
            'top_positions': [],
            'required_skills': [],
            'top_companies': [],
            'growth_trend': 'stable',
            'market_share': 0
        }
        
        # Filtrar vagas do setor
        sector_jobs = []
        sector_keywords = {
            'tecnologia': ['desenvolvedor', 'programador', 'tech', 'software', 'ti', 'dev'],
            'vendas': ['vendedor', 'vendas', 'comercial'],
            'marketing': ['marketing', 'digital', 'social media'],
            'financeiro': ['financeiro', 'contabil', 'contador', 'financas']
        }
        
        keywords = sector_keywords.get(sector.lower(), [sector.lower()])
        
        for job in jobs:
            titulo = job.get('titulo', '').lower()
            if any(keyword in titulo for keyword in keywords):
                sector_jobs.append(job)
        
        report['job_count'] = len(sector_jobs)
        report['market_share'] = (len(sector_jobs) / len(jobs)) * 100 if jobs else 0
        
        if sector_jobs:
            # Análise específica do setor usando analisadores
            if 'salary' in self.analyzers:
                salary_data = self.analyzers['salary'].analyze_salary_trends(sector_jobs)
                report['avg_salary'] = salary_data.get('average_salary', 0)
            
            if 'skills' in self.analyzers:
                skills_data = self.analyzers['skills'].analyze_skills_demand(sector_jobs)
                top_skills = sorted(
                    [(skill, data.frequency) for skill, data in skills_data.items()],
                    key=lambda x: x[1], reverse=True
                )[:5]
                report['required_skills'] = [skill for skill, freq in top_skills]
        
        return report
    
    def generate_competitive_analysis(self, jobs: List[Dict], target_companies: List[str]) -> Dict:
        """Gera análise competitiva entre empresas"""
        analysis = {
            'generation_date': datetime.now().isoformat(),
            'companies_analyzed': len(target_companies),
            'competitive_metrics': {},
            'market_positioning': {},
            'recommendations': []
        }
        
        for company in target_companies:
            company_jobs = [job for job in jobs if company.lower() in job.get('empresa', '').lower()]
            
            if company_jobs:
                # Métricas da empresa
                analysis['competitive_metrics'][company] = {
                    'job_count': len(company_jobs),
                    'avg_salary': 0,
                    'top_skills': [],
                    'locations': [],
                    'market_presence': (len(company_jobs) / len(jobs)) * 100
                }
                
                # Análise salarial se disponível
                if 'salary' in self.analyzers:
                    salary_data = self.analyzers['salary'].analyze_salary_trends(company_jobs)
                    analysis['competitive_metrics'][company]['avg_salary'] = salary_data.get('average_salary', 0)
        
        return analysis
    
    def print_executive_dashboard_report(self, dashboard: Dict = None):
        """Imprime relatório do dashboard executivo"""
        from ..utils.menu_system import Colors
        
        if not dashboard:
            print(f"{Colors.RED}Dashboard não disponível{Colors.RESET}")
            return
        
        print(f"\n{Colors.CYAN}📊 DASHBOARD EXECUTIVO - INTELIGÊNCIA DE MERCADO{Colors.RESET}")
        print("=" * 70)
        
        # Visão geral
        overview = dashboard.get('market_overview', {})
        print(f"\n{Colors.YELLOW}🌡 Temperatura do Mercado:{Colors.RESET}")
        temp = overview.get('market_temperature', 'neutral')
        temp_emoji = {'hot': '🔥', 'warm': '☀️', 'cool': '❄️', 'neutral': '📊'}.get(temp, '📊')
        print(f"  Status: {temp.title()} {temp_emoji}")
        print(f"  Tamanho do mercado: {overview.get('market_size', 0):,} vagas")
        print(f"  Velocidade (7 dias): {overview.get('job_posting_velocity', 0)} vagas")
        print(f"  Trabalho remoto: {overview.get('remote_work_percentage', 0):.1f}%")
        
        # Métricas-chave
        metrics = dashboard.get('key_metrics', {})
        print(f"\n{Colors.GREEN}🎯 Métricas-Chave:{Colors.RESET}")
        if metrics.get('avg_salary', 0) > 0:
            print(f"  Salário médio: R$ {metrics['avg_salary']:,.2f}")
        
        # Top skills
        top_skills = metrics.get('top_skills', [])
        if top_skills:
            print(f"  Top Skills:")
            for skill in top_skills[:3]:
                print(f"    • {skill['skill']} ({skill['frequency']} vagas)")
        
        # Top empresas
        top_companies = metrics.get('top_companies', [])
        if top_companies:
            print(f"  Empresas mais ativas:")
            for company in top_companies[:3]:
                print(f"    • {company['company']} ({company['job_count']} vagas)")
        
        # Setores dominantes
        dominant_sectors = overview.get('dominant_sectors', [])
        if dominant_sectors:
            print(f"\n{Colors.BLUE}🏢 Setores Dominantes:{Colors.RESET}")
            for sector in dominant_sectors:
                print(f"  • {sector['sector'].replace('_', ' ').title()}: {sector['job_count']} vagas ({sector['percentage']:.1f}%)")
        
        # Alertas
        alerts = dashboard.get('alerts', [])
        if alerts:
            print(f"\n{Colors.RED}🚨 Alertas de Mercado:{Colors.RESET}")
            for alert in alerts:
                severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(alert['severity'], '📌')
                print(f"  {severity_emoji} {alert['message']}")
                print(f"     Ação: {alert['action']}")
        
        # Recomendações
        recommendations = dashboard.get('recommendations', [])
        if recommendations:
            print(f"\n{Colors.YELLOW}💡 Recomendações Executivas:{Colors.RESET}")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        print(f"\n{Colors.CYAN}📅 Relatório gerado em: {dashboard.get('generation_date', 'N/A')}{Colors.RESET}")
        print("=" * 70)


# Instância global dos relatórios de inteligência
market_intelligence = MarketIntelligenceReports()