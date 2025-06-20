"""
Modelos de Machine Learning
"""

from .seniority_classifier import SeniorityClassifier
from .sentiment_analyzer import SentimentAnalyzer
from .salary_predictor import SalaryPredictor
from .job_recommender import JobRecommender
from .duplicate_detector import DuplicateDetector
from .cv_analyzer import CVAnalyzer

__all__ = [
    'SeniorityClassifier',
    'SentimentAnalyzer', 
    'SalaryPredictor',
    'JobRecommender',
    'DuplicateDetector',
    'CVAnalyzer'
]