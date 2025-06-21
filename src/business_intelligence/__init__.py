"""
Sistema de Business Intelligence e Análise Avançada
=====================================================

Este módulo contém implementações de BI para:
- Análise de tendências salariais
- Mapa de calor de oportunidades regionais 
- Análise de skills em alta demanda
- Relatórios de inteligência de mercado
- Comparação de dados históricos
"""

from .salary_trend_analyzer import salary_trend_analyzer
from .regional_heatmap import regional_heatmap
from .skills_demand_analyzer import skills_demand_analyzer
from .market_intelligence_reports import market_intelligence
from .historical_data_comparator import historical_comparator

__all__ = [
    'salary_trend_analyzer',
    'regional_heatmap', 
    'skills_demand_analyzer',
    'market_intelligence',
    'historical_comparator'
]

__version__ = '1.0.0'