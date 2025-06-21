"""
Sistema de Machine Learning e IA para Análise de Vagas
======================================================

Este módulo contém implementações de ML para:
- Classificação de senioridade
- Análise de sentimento
- Predição de salários
- Sistema de recomendação
- Detecção de duplicatas
- Otimização automática de URLs (Fase 3)
- Análise temporal e padrões (Fase 3)
- Auto-ajuste de configurações (Fase 3)
"""

from .models.seniority_classifier import SeniorityClassifier
from .models.sentiment_analyzer import SentimentAnalyzer
from .models.salary_predictor import SalaryPredictor
from .models.job_recommender import JobRecommender
from .models.duplicate_detector import DuplicateDetector

# Novos sistemas da Fase 3
from .url_optimizer import url_optimizer
from .temporal_analyzer import temporal_analyzer
from .auto_tuner import auto_tuner

__all__ = [
    'SeniorityClassifier',
    'SentimentAnalyzer',
    'SalaryPredictor',
    'JobRecommender',
    'DuplicateDetector',
    'url_optimizer',
    'temporal_analyzer',
    'auto_tuner'
]

__version__ = '1.0.0'