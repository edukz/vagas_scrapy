"""
Handlers para diferentes funcionalidades do sistema
"""

# Importações dos handlers
from .scraping_handler import ScrapingHandler
from .cache_handler import CacheHandler
from .data_handler import DataHandler
from .statistics_handler import StatisticsHandler
from .api_handler import APIHandler

__all__ = [
    'ScrapingHandler',
    'CacheHandler', 
    'DataHandler',
    'StatisticsHandler',
    'APIHandler'
]