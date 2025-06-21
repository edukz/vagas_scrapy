"""
Mapa de Calor de Oportunidades Regionais

Este módulo gera mapas de calor para visualizar:
- Concentração de vagas por região
- Médias salariais regionais
- Tendências de crescimento por área
- Análise de competição regional
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
import statistics
from dataclasses import dataclass


@dataclass
class RegionalData:
    """Representa dados regionais agregados"""
    region: str
    job_count: int
    avg_salary: float
    salary_range: Tuple[float, float]
    top_positions: List[str]
    growth_trend: str  # 'growing', 'stable', 'declining'
    competition_level: str  # 'low', 'medium', 'high'
    opportunity_score: float  # 0-100
    

class RegionalHeatmap:
    """
    Gerador de mapas de calor regionais
    
    Funcionalidades:
    - Agregação de dados por região
    - Cálculo de índices de oportunidade
    - Visualização de dados regionais
    - Análise comparativa entre regiões
    - Detecção de mercados emergentes
    """
    
    def __init__(self, data_file: str = "data/business_intelligence/regional_heatmap.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Criar diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Carregar dados regionais
        self.regional_data = self._load_regional_data()
        
        # Mapeamento de regiões e suas coordenadas (para visualização)
        self.region_coordinates = {
            'São Paulo': {'lat': -23.5505, 'lon': -46.6333, 'population': 12400000},
            'Rio de Janeiro': {'lat': -22.9068, 'lon': -43.1729, 'population': 6748000},
            'Brasília': {'lat': -15.8267, 'lon': -47.9218, 'population': 3094325},
            'Minas Gerais': {'lat': -19.9167, 'lon': -43.9345, 'population': 21411923},
            'Remoto': {'lat': 0, 'lon': 0, 'population': 0},  # Virtual
            'Híbrido': {'lat': 0, 'lon': 0, 'population': 0},  # Virtual
            'Outras': {'lat': -15.7801, 'lon': -47.9292, 'population': 5000000}  # Centro do Brasil
        }
        
        # Classificação de cidades por região
        self.city_to_region = {
            # São Paulo
            'sao paulo': 'São Paulo',
            'sp': 'São Paulo',
            'santos': 'São Paulo',
            'campinas': 'São Paulo',
            'abc': 'São Paulo',
            
            # Rio de Janeiro
            'rio de janeiro': 'Rio de Janeiro',
            'rj': 'Rio de Janeiro',
            'niterói': 'Rio de Janeiro',
            
            # Minas Gerais
            'belo horizonte': 'Minas Gerais',
            'mg': 'Minas Gerais',
            'uberlandia': 'Minas Gerais',
            
            # Brasília
            'brasilia': 'Brasília',
            'df': 'Brasília',
            
            # Modalidades
            'home office': 'Remoto',
            'remoto': 'Remoto',
            'hibrido': 'Híbrido'
        }
    
    def _load_regional_data(self) -> Dict:
        """Carrega dados regionais históricos"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "regional_aggregates": {},
            "time_series": [],
            "heatmap_data": {},
            "last_update": None,
            "statistics": {
                "total_regions": 0,
                "total_jobs_analyzed": 0
            }
        }
    
    def _save_regional_data(self):
        """Salva dados regionais"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.regional_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados regionais: {e}")
    
    def normalize_region(self, location: str) -> str:
        """Normaliza localização para região padrão"""
        if not location:
            return 'Não especificado'
        
        location_lower = location.lower().strip()
        
        # Buscar correspondência direta
        for city_key, region in self.city_to_region.items():
            if city_key in location_lower:
                return region
        
        # Se não encontrou, categorizar como "Outras"
        return 'Outras'
    
    def extract_salary_value(self, salary_text: str) -> Optional[float]:
        """Extração simples de valor salarial"""
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
    
    def analyze_jobs_by_region(self, jobs: List[Dict]) -> Dict[str, RegionalData]:
        """
        Analisa vagas e agrega dados por região
        
        Args:
            jobs: Lista de vagas para analisar
            
        Returns:
            Dicionário com dados regionais agregados
        """
        regional_aggregates = defaultdict(lambda: {
            'job_count': 0,
            'salaries': [],
            'positions': [],
            'companies': [],
            'timestamps': []
        })
        
        # Processar cada vaga
        for job in jobs:
            region = self.normalize_region(job.get('localizacao', ''))
            
            # Agregar dados
            regional_aggregates[region]['job_count'] += 1
            regional_aggregates[region]['positions'].append(job.get('titulo', ''))
            regional_aggregates[region]['companies'].append(job.get('empresa', ''))
            regional_aggregates[region]['timestamps'].append(
                job.get('data_coleta', datetime.now().isoformat())
            )
            
            # Tentar extrair salário
            salary = self.extract_salary_value(job.get('salario', ''))
            if salary:
                regional_aggregates[region]['salaries'].append(salary)
        
        # Converter para objetos RegionalData
        regional_data = {}
        
        for region, data in regional_aggregates.items():
            # Calcular estatísticas salariais
            if data['salaries']:
                avg_salary = statistics.mean(data['salaries'])
                salary_range = (min(data['salaries']), max(data['salaries']))
            else:
                avg_salary = 0
                salary_range = (0, 0)
            
            # Top posições
            position_counts = Counter(data['positions'])
            top_positions = [pos for pos, count in position_counts.most_common(5)]
            
            # Análise de tendência temporal
            growth_trend = self._analyze_regional_growth(region, data['timestamps'])
            
            # Nível de competição
            competition_level = self._calculate_competition_level(data['job_count'], len(set(data['companies'])))
            
            # Score de oportunidade
            opportunity_score = self._calculate_opportunity_score(
                data['job_count'], avg_salary, competition_level, growth_trend
            )
            
            regional_data[region] = RegionalData(
                region=region,
                job_count=data['job_count'],
                avg_salary=avg_salary,
                salary_range=salary_range,
                top_positions=top_positions,
                growth_trend=growth_trend,
                competition_level=competition_level,
                opportunity_score=opportunity_score
            )
        
        # Salvar dados agregados
        self.regional_data["regional_aggregates"] = {
            region: {
                'region': rd.region,
                'job_count': rd.job_count,
                'avg_salary': rd.avg_salary,
                'salary_range': rd.salary_range,
                'top_positions': rd.top_positions,
                'growth_trend': rd.growth_trend,
                'competition_level': rd.competition_level,
                'opportunity_score': rd.opportunity_score,
                'last_update': datetime.now().isoformat()
            }
            for region, rd in regional_data.items()
        }
        
        # Atualizar estatísticas gerais
        self.regional_data["statistics"] = {
            "total_regions": len(regional_data),
            "total_jobs_analyzed": sum(rd.job_count for rd in regional_data.values()),
            "last_analysis": datetime.now().isoformat()
        }
        
        self._save_regional_data()
        return regional_data
    
    def _analyze_regional_growth(self, region: str, timestamps: List[str]) -> str:
        """Analisa tendência de crescimento da região"""
        if len(timestamps) < 10:  # Poucos dados
            return 'stable'
        
        try:
            # Agrupar por dia
            daily_counts = defaultdict(int)
            for timestamp in timestamps:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    day_key = dt.date().isoformat()
                    daily_counts[day_key] += 1
                except:
                    continue
            
            if len(daily_counts) < 3:
                return 'stable'
            
            # Verificar tendência dos últimos dias
            sorted_days = sorted(daily_counts.items())
            recent_days = sorted_days[-7:]  # Últimos 7 dias
            
            if len(recent_days) < 3:
                return 'stable'
            
            # Calcular tendência
            counts = [count for day, count in recent_days]
            first_half = statistics.mean(counts[:len(counts)//2])
            second_half = statistics.mean(counts[len(counts)//2:])
            
            if second_half > first_half * 1.2:
                return 'growing'
            elif second_half < first_half * 0.8:
                return 'declining'
            else:
                return 'stable'
                
        except Exception:
            return 'stable'
    
    def _calculate_competition_level(self, job_count: int, unique_companies: int) -> str:
        """Calcula nível de competição na região"""
        if job_count == 0:
            return 'low'
        
        # Ratio de vagas por empresa
        jobs_per_company = job_count / max(unique_companies, 1)
        
        if jobs_per_company > 5:  # Muitas vagas por empresa
            return 'low'
        elif jobs_per_company > 2:
            return 'medium'
        else:
            return 'high'
    
    def _calculate_opportunity_score(self, job_count: int, avg_salary: float, 
                                   competition_level: str, growth_trend: str) -> float:
        """Calcula score de oportunidade (0-100)"""
        score = 0
        
        # Base score por número de vagas (0-40 pontos)
        if job_count > 50:
            score += 40
        elif job_count > 20:
            score += 30
        elif job_count > 10:
            score += 20
        elif job_count > 5:
            score += 10
        
        # Bonus por salário (0-25 pontos)
        if avg_salary > 8000:
            score += 25
        elif avg_salary > 6000:
            score += 20
        elif avg_salary > 4000:
            score += 15
        elif avg_salary > 2000:
            score += 10
        
        # Bonus por baixa competição (0-20 pontos)
        competition_bonus = {
            'low': 20,
            'medium': 10,
            'high': 0
        }
        score += competition_bonus.get(competition_level, 0)
        
        # Bonus por crescimento (0-15 pontos)
        growth_bonus = {
            'growing': 15,
            'stable': 5,
            'declining': 0
        }
        score += growth_bonus.get(growth_trend, 0)
        
        return min(score, 100)  # Máximo 100
    
    def generate_heatmap_data(self) -> Dict:
        """
        Gera dados formatados para visualização de mapa de calor
        
        Returns:
            Dados prontos para visualização
        """
        if not self.regional_data.get("regional_aggregates"):
            return {'regions': [], 'max_jobs': 0, 'max_salary': 0}
        
        heatmap_regions = []
        max_jobs = 0
        max_salary = 0
        
        for region, data in self.regional_data["regional_aggregates"].items():
            # Obter coordenadas
            coords = self.region_coordinates.get(region, {'lat': 0, 'lon': 0, 'population': 0})
            
            region_data = {
                'name': region,
                'lat': coords['lat'],
                'lon': coords['lon'],
                'job_count': data['job_count'],
                'avg_salary': data['avg_salary'],
                'opportunity_score': data['opportunity_score'],
                'growth_trend': data['growth_trend'],
                'competition_level': data['competition_level'],
                'top_positions': data['top_positions'][:3],  # Top 3
                'population': coords.get('population', 0)
            }
            
            heatmap_regions.append(region_data)
            max_jobs = max(max_jobs, data['job_count'])
            max_salary = max(max_salary, data['avg_salary'])
        
        # Ordenar por score de oportunidade
        heatmap_regions.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        heatmap_data = {
            'regions': heatmap_regions,
            'max_jobs': max_jobs,
            'max_salary': max_salary,
            'generation_date': datetime.now().isoformat(),
            'total_regions': len(heatmap_regions)
        }
        
        # Salvar dados do heatmap
        self.regional_data["heatmap_data"] = heatmap_data
        self._save_regional_data()
        
        return heatmap_data
    
    def get_regional_insights(self) -> Dict:
        """
        Gera insights sobre oportunidades regionais
        
        Returns:
            Dicionário com insights regionais
        """
        insights = {
            'hottest_regions': [],
            'emerging_markets': [],
            'salary_leaders': [],
            'growth_champions': [],
            'best_opportunities': [],
            'regional_summary': {},
            'recommendations': []
        }
        
        if not self.regional_data.get("regional_aggregates"):
            insights['regional_summary']['message'] = 'Dados regionais insuficientes'
            return insights
        
        aggregates = self.regional_data["regional_aggregates"]
        
        # Regiões mais quentes (mais vagas)
        insights['hottest_regions'] = sorted(
            [{'region': r, 'job_count': d['job_count'], 'avg_salary': d['avg_salary']}
             for r, d in aggregates.items()],
            key=lambda x: x['job_count'], reverse=True
        )[:5]
        
        # Mercados emergentes (crescimento)
        insights['emerging_markets'] = [
            {'region': r, 'growth_trend': d['growth_trend'], 'job_count': d['job_count']}
            for r, d in aggregates.items()
            if d['growth_trend'] == 'growing'
        ][:5]
        
        # Líderes em salário
        insights['salary_leaders'] = sorted(
            [{'region': r, 'avg_salary': d['avg_salary'], 'job_count': d['job_count']}
             for r, d in aggregates.items() if d['avg_salary'] > 0],
            key=lambda x: x['avg_salary'], reverse=True
        )[:5]
        
        # Campeões de crescimento
        insights['growth_champions'] = [
            {'region': r, 'opportunity_score': d['opportunity_score'], 
             'growth_trend': d['growth_trend']}
            for r, d in aggregates.items()
            if d['growth_trend'] in ['growing', 'stable'] and d['opportunity_score'] > 50
        ]
        
        # Melhores oportunidades (score alto)
        insights['best_opportunities'] = sorted(
            [{'region': r, 'opportunity_score': d['opportunity_score'],
              'job_count': d['job_count'], 'competition_level': d['competition_level']}
             for r, d in aggregates.items()],
            key=lambda x: x['opportunity_score'], reverse=True
        )[:5]
        
        # Sumário regional
        total_jobs = sum(d['job_count'] for d in aggregates.values())
        avg_salaries = [d['avg_salary'] for d in aggregates.values() if d['avg_salary'] > 0]
        
        insights['regional_summary'] = {
            'total_regions_analyzed': len(aggregates),
            'total_jobs_mapped': total_jobs,
            'avg_salary_across_regions': round(statistics.mean(avg_salaries), 2) if avg_salaries else 0,
            'regions_with_growth': len([d for d in aggregates.values() if d['growth_trend'] == 'growing']),
            'high_opportunity_regions': len([d for d in aggregates.values() if d['opportunity_score'] > 70])
        }
        
        # Recomendações
        if insights['best_opportunities']:
            best_region = insights['best_opportunities'][0]
            insights['recommendations'].append(
                f"Foque em {best_region['region']} - maior score de oportunidade ({best_region['opportunity_score']:.0f})"
            )
        
        if insights['emerging_markets']:
            insights['recommendations'].append(
                f"Monitore mercados emergentes: {', '.join([m['region'] for m in insights['emerging_markets'][:3]])}"
            )
        
        if insights['salary_leaders']:
            top_salary_region = insights['salary_leaders'][0]
            insights['recommendations'].append(
                f"{top_salary_region['region']} oferece os melhores salários (R$ {top_salary_region['avg_salary']:,.2f})"
            )
        
        return insights
    
    def print_regional_heatmap_report(self):
        """Imprime relatório visual do mapa de calor regional"""
        from ..utils.menu_system import Colors
        
        print(f"\n{Colors.CYAN}🗺 MAPA DE CALOR REGIONAL - OPORTUNIDADES{Colors.RESET}")
        print("=" * 60)
        
        insights = self.get_regional_insights()
        
        # Sumário regional
        if 'total_regions_analyzed' in insights['regional_summary']:
            summary = insights['regional_summary']
            print(f"\n{Colors.YELLOW}📈 Visão Geral Regional:{Colors.RESET}")
            print(f"  • Regiões analisadas: {summary['total_regions_analyzed']}")
            print(f"  • Total de vagas mapeadas: {summary['total_jobs_mapped']}")
            if summary['avg_salary_across_regions'] > 0:
                print(f"  • Salário médio geral: R$ {summary['avg_salary_across_regions']:,.2f}")
            print(f"  • Regiões em crescimento: {summary['regions_with_growth']}")
            print(f"  • Regiões de alta oportunidade: {summary['high_opportunity_regions']}")
        
        # Regiões mais quentes
        if insights['hottest_regions']:
            print(f"\n{Colors.RED}🔥 Regiões Mais Quentes (Volume):{Colors.RESET}")
            for i, region in enumerate(insights['hottest_regions'], 1):
                salary_info = f" - R$ {region['avg_salary']:,.2f}" if region['avg_salary'] > 0 else ""
                print(f"  {i}. {region['region']}: {region['job_count']} vagas{salary_info}")
        
        # Melhores oportunidades
        if insights['best_opportunities']:
            print(f"\n{Colors.GREEN}🎆 Melhores Oportunidades (Score):{Colors.RESET}")
            for i, opp in enumerate(insights['best_opportunities'], 1):
                competition_emoji = {
                    'low': '�︩',  # Baixa competição
                    'medium': '🟨',  # Média
                    'high': '🟥'  # Alta
                }.get(opp['competition_level'], '')
                print(f"  {i}. {opp['region']}: {opp['opportunity_score']:.0f}/100 {competition_emoji}")
                print(f"     {opp['job_count']} vagas, competição {opp['competition_level']}")
        
        # Líderes em salário
        if insights['salary_leaders']:
            print(f"\n{Colors.GREEN}💰 Líderes em Salário:{Colors.RESET}")
            for i, leader in enumerate(insights['salary_leaders'], 1):
                print(f"  {i}. {leader['region']}: R$ {leader['avg_salary']:,.2f} ({leader['job_count']} vagas)")
        
        # Mercados emergentes
        if insights['emerging_markets']:
            print(f"\n{Colors.BLUE}📈 Mercados Emergentes:{Colors.RESET}")
            for market in insights['emerging_markets']:
                print(f"  • {market['region']}: {market['job_count']} vagas (crescendo)")
        
        # Recomendações
        if insights['recommendations']:
            print(f"\n{Colors.YELLOW}💡 Recomendações Estratégicas:{Colors.RESET}")
            for rec in insights['recommendations']:
                print(f"  • {rec}")
        
        print("\n" + "=" * 60)


# Instância global do mapa de calor regional
regional_heatmap = RegionalHeatmap()