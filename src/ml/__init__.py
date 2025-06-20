"""
Sistema de Machine Learning e IA para Análise de Vagas
======================================================

Este módulo contém implementações de ML para:
- Classificação de senioridade
- Análise de sentimento
- Predição de salários
- Sistema de recomendação
- Detecção de duplicatas
"""

from .models.seniority_classifier import SeniorityClassifier
from .models.sentiment_analyzer import SentimentAnalyzer
from .models.salary_predictor import SalaryPredictor
from .models.job_recommender import JobRecommender
from .models.duplicate_detector import DuplicateDetector

__all__ = [
    'SeniorityClassifier',
    'SentimentAnalyzer',
    'SalaryPredictor',
    'JobRecommender',
    'DuplicateDetector'
]

__version__ = '1.0.0'