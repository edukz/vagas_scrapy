"""
Sistema de Fallback para Seletores CSS/XPath

Este módulo implementa estratégias de fallback para tornar o scraping
mais resistente a mudanças no HTML do site.

Funcionalidades:
- Múltiplos seletores alternativos para cada elemento
- Scoring de confiabilidade
- Auto-aprendizado de seletores bem-sucedidos
- Validação de dados extraídos
"""

import re
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime


class SelectorType(Enum):
    """Tipos de seletores suportados"""
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    ATTRIBUTE = "attribute"


@dataclass
class SelectorStrategy:
    """Estratégia individual de seletor"""
    selector: str
    type: SelectorType
    confidence: float = 1.0  # 0.0 a 1.0
    last_success: Optional[datetime] = None
    success_count: int = 0
    fail_count: int = 0
    
    @property
    def reliability_score(self) -> float:
        """Calcula score de confiabilidade baseado em histórico"""
        total_attempts = self.success_count + self.fail_count
        if total_attempts == 0:
            return self.confidence
        
        success_rate = self.success_count / total_attempts
        # Peso maior para tentativas recentes
        recency_factor = 1.0
        if self.last_success:
            days_since_success = (datetime.now() - self.last_success).days
            recency_factor = max(0.5, 1.0 - (days_since_success * 0.1))
        
        return success_rate * recency_factor * self.confidence


class FallbackSelector:
    """Sistema principal de fallback para seletores"""
    
    def __init__(self):
        self.selector_groups = self._initialize_selectors()
        self.validation_rules = self._initialize_validators()
    
    def _initialize_selectors(self) -> Dict[str, List[SelectorStrategy]]:
        """Inicializa grupos de seletores com fallbacks"""
        return {
            # Título da vaga
            'job_title': [
                SelectorStrategy('h2 a[href*="/vagas/"]', SelectorType.CSS, 0.9),
                SelectorStrategy('h1.job-title', SelectorType.CSS, 0.8),
                SelectorStrategy('[data-testid="job-title"]', SelectorType.CSS, 0.85),
                SelectorStrategy('//h2/a[contains(@href, "/vagas/")]', SelectorType.XPATH, 0.7),
                SelectorStrategy('.vaga-title a', SelectorType.CSS, 0.6),
                SelectorStrategy('[class*="title"] a[href*="vagas"]', SelectorType.CSS, 0.5),
            ],
            
            # Link da vaga
            'job_link': [
                SelectorStrategy('h2 a[href*="/vagas/"]', SelectorType.CSS, 0.9),
                SelectorStrategy('a[href*="/vagas/"][href*="/"]', SelectorType.CSS, 0.8),
                SelectorStrategy('[data-testid="job-link"]', SelectorType.CSS, 0.85),
                SelectorStrategy('.job-link', SelectorType.CSS, 0.7),
                SelectorStrategy('//a[contains(@href, "/vagas/") and contains(@href, "/")]', SelectorType.XPATH, 0.6),
            ],
            
            # Empresa
            'company': [
                SelectorStrategy('span.sc-gEvEer', SelectorType.CSS, 0.8),
                SelectorStrategy('[data-testid="company-name"]', SelectorType.CSS, 0.9),
                SelectorStrategy('[class*="company"]', SelectorType.CSS, 0.7),
                SelectorStrategy('[class*="empresa"]', SelectorType.CSS, 0.7),
                SelectorStrategy('.job-company', SelectorType.CSS, 0.6),
                SelectorStrategy('//span[contains(@class, "company")]', SelectorType.XPATH, 0.5),
                SelectorStrategy('span:has-text("Ltda")', SelectorType.TEXT, 0.4),
                SelectorStrategy('span:has-text("S.A.")', SelectorType.TEXT, 0.4),
            ],
            
            # Localização
            'location': [
                SelectorStrategy('button[title*="Local"]', SelectorType.CSS, 0.8),
                SelectorStrategy('[data-testid="job-location"]', SelectorType.CSS, 0.9),
                SelectorStrategy('[class*="location"]', SelectorType.CSS, 0.7),
                SelectorStrategy('[class*="local"]', SelectorType.CSS, 0.7),
                SelectorStrategy('.job-location', SelectorType.CSS, 0.6),
                SelectorStrategy('span:has-text("Home Office")', SelectorType.TEXT, 0.8),
                SelectorStrategy('span:has-text("Remoto")', SelectorType.TEXT, 0.8),
                SelectorStrategy('[class*="cidade"]', SelectorType.CSS, 0.5),
                SelectorStrategy('//button[contains(@title, "Local")]', SelectorType.XPATH, 0.5),
            ],
            
            # Descrição
            'description': [
                SelectorStrategy('[data-testid="job-description"]', SelectorType.CSS, 0.9),
                SelectorStrategy('.job-description', SelectorType.CSS, 0.8),
                SelectorStrategy('[class*="description"]', SelectorType.CSS, 0.7),
                SelectorStrategy('.sc-gEvEer', SelectorType.CSS, 0.5),
                SelectorStrategy('section:has-text("Descrição")', SelectorType.TEXT, 0.6),
                SelectorStrategy('div:has-text("Descrição")', SelectorType.TEXT, 0.5),
                SelectorStrategy('[class*="descricao"]', SelectorType.CSS, 0.6),
                SelectorStrategy('//section[contains(., "Descrição")]', SelectorType.XPATH, 0.4),
            ],
            
            # Salário
            'salary': [
                SelectorStrategy('[data-testid="salary"]', SelectorType.CSS, 0.9),
                SelectorStrategy('[data-testid="job-salary"]', SelectorType.CSS, 0.9),
                SelectorStrategy('.salary', SelectorType.CSS, 0.8),
                SelectorStrategy('[class*="salario"]', SelectorType.CSS, 0.7),
                SelectorStrategy('[class*="salary"]', SelectorType.CSS, 0.7),
                SelectorStrategy('[class*="remuneracao"]', SelectorType.CSS, 0.6),
                SelectorStrategy('span:has-text("R$")', SelectorType.TEXT, 0.8),
                SelectorStrategy('div:has-text("Salário")', SelectorType.TEXT, 0.5),
                SelectorStrategy('//span[contains(text(), "R$")]', SelectorType.XPATH, 0.6),
            ],
            
            # Requisitos
            'requirements': [
                SelectorStrategy('[data-testid="job-requirements"]', SelectorType.CSS, 0.9),
                SelectorStrategy('section:has-text("Requisitos")', SelectorType.TEXT, 0.7),
                SelectorStrategy('div:has-text("Requisitos")', SelectorType.TEXT, 0.6),
                SelectorStrategy('[class*="requirements"]', SelectorType.CSS, 0.7),
                SelectorStrategy('[class*="requisitos"]', SelectorType.CSS, 0.7),
                SelectorStrategy('section:has-text("Qualificações")', SelectorType.TEXT, 0.6),
                SelectorStrategy('.job-requirements', SelectorType.CSS, 0.6),
                SelectorStrategy('//section[contains(., "Requisitos")]', SelectorType.XPATH, 0.5),
            ],
            
            # Benefícios
            'benefits': [
                SelectorStrategy('[data-testid="job-benefits"]', SelectorType.CSS, 0.9),
                SelectorStrategy('section:has-text("Benefícios")', SelectorType.TEXT, 0.7),
                SelectorStrategy('div:has-text("Benefícios")', SelectorType.TEXT, 0.6),
                SelectorStrategy('[class*="benefits"]', SelectorType.CSS, 0.7),
                SelectorStrategy('[class*="beneficios"]', SelectorType.CSS, 0.7),
                SelectorStrategy('section:has-text("Oferecemos")', SelectorType.TEXT, 0.6),
                SelectorStrategy('.job-benefits', SelectorType.CSS, 0.6),
                SelectorStrategy('ul:has-text("Vale")', SelectorType.TEXT, 0.5),
            ],
            
            # Experiência
            'experience': [
                SelectorStrategy('[data-testid="experience-level"]', SelectorType.CSS, 0.9),
                SelectorStrategy('[class*="experience"]', SelectorType.CSS, 0.7),
                SelectorStrategy('[class*="nivel"]', SelectorType.CSS, 0.6),
                SelectorStrategy('span:has-text("anos")', SelectorType.TEXT, 0.5),
                SelectorStrategy('div:has-text("Experiência")', SelectorType.TEXT, 0.5),
                SelectorStrategy('span:has-text("Júnior")', SelectorType.TEXT, 0.6),
                SelectorStrategy('span:has-text("Pleno")', SelectorType.TEXT, 0.6),
                SelectorStrategy('span:has-text("Sênior")', SelectorType.TEXT, 0.6),
            ],
            
            # Modalidade
            'work_mode': [
                SelectorStrategy('[data-testid="work-mode"]', SelectorType.CSS, 0.9),
                SelectorStrategy('[class*="work-mode"]', SelectorType.CSS, 0.7),
                SelectorStrategy('[class*="modalidade"]', SelectorType.CSS, 0.7),
                SelectorStrategy('span:has-text("Home Office")', SelectorType.TEXT, 0.8),
                SelectorStrategy('span:has-text("Remoto")', SelectorType.TEXT, 0.8),
                SelectorStrategy('span:has-text("Presencial")', SelectorType.TEXT, 0.7),
                SelectorStrategy('span:has-text("Híbrido")', SelectorType.TEXT, 0.7),
                SelectorStrategy('div:has-text("Modalidade")', SelectorType.TEXT, 0.5),
            ],
            
            # Data publicação
            'publish_date': [
                SelectorStrategy('[data-testid="publish-date"]', SelectorType.CSS, 0.9),
                SelectorStrategy('[class*="date"]', SelectorType.CSS, 0.7),
                SelectorStrategy('[class*="publicada"]', SelectorType.CSS, 0.7),
                SelectorStrategy('time', SelectorType.CSS, 0.8),
                SelectorStrategy('span:has-text("dia")', SelectorType.TEXT, 0.5),
                SelectorStrategy('span:has-text("publicada")', SelectorType.TEXT, 0.5),
                SelectorStrategy('div:has-text("Publicada")', SelectorType.TEXT, 0.4),
                SelectorStrategy('[datetime]', SelectorType.ATTRIBUTE, 0.6),
            ],
        }
    
    def _initialize_validators(self) -> Dict[str, Callable]:
        """Inicializa validadores para cada tipo de dado"""
        return {
            'job_title': lambda x: bool(x and len(x.strip()) > 5),
            'job_link': lambda x: bool(x and ('/vagas/' in x or x.startswith('/'))),
            'company': lambda x: bool(x and len(x.strip()) > 2 and x != 'Não informada'),
            'location': lambda x: bool(x and len(x.strip()) > 2),
            'description': lambda x: bool(x and len(x.strip()) > 20),
            'salary': lambda x: bool(x and ('R$' in x or 'combinar' in x.lower() or 'competitive' in x.lower())),
            'requirements': lambda x: bool(x and len(x.strip()) > 10),
            'benefits': lambda x: bool(x and len(x.strip()) > 5),
            'experience': lambda x: bool(x and any(word in x.lower() for word in ['júnior', 'pleno', 'sênior', 'anos', 'experiência'])),
            'work_mode': lambda x: bool(x and any(word in x.lower() for word in ['home', 'remoto', 'presencial', 'híbrido', 'office'])),
            'publish_date': lambda x: bool(x and any(word in x.lower() for word in ['dia', 'publicada', 'há', 'ontem', 'hoje', '/', '-'])),
        }
    
    async def extract_with_fallback(self, page, element_type: str, parent_element=None) -> Optional[str]:
        """
        Extrai dados usando estratégias de fallback
        
        Args:
            page: Página do Playwright
            element_type: Tipo de elemento a extrair (ex: 'job_title')
            parent_element: Elemento pai opcional para busca contextual
        
        Returns:
            Valor extraído ou None se falhar
        """
        if element_type not in self.selector_groups:
            print(f"⚠️ Tipo de elemento não reconhecido: {element_type}")
            return None
        
        strategies = sorted(
            self.selector_groups[element_type],
            key=lambda s: s.reliability_score,
            reverse=True
        )
        
        context = parent_element or page
        validator = self.validation_rules.get(element_type, lambda x: bool(x))
        
        for strategy in strategies:
            try:
                result = None
                
                if strategy.type == SelectorType.CSS:
                    elem = await context.query_selector(strategy.selector)
                    if elem:
                        result = await elem.inner_text()
                
                elif strategy.type == SelectorType.XPATH:
                    elems = await context.query_selector_all(f'xpath={strategy.selector}')
                    if elems:
                        result = await elems[0].inner_text()
                
                elif strategy.type == SelectorType.TEXT:
                    elem = await context.query_selector(strategy.selector)
                    if elem:
                        result = await elem.inner_text()
                
                elif strategy.type == SelectorType.ATTRIBUTE:
                    elem = await context.query_selector(strategy.selector)
                    if elem:
                        # Tentar diferentes atributos
                        for attr in ['datetime', 'title', 'content', 'value']:
                            result = await elem.get_attribute(attr)
                            if result:
                                break
                
                # Validar resultado
                if result and validator(result):
                    # Atualizar estatísticas de sucesso
                    strategy.success_count += 1
                    strategy.last_success = datetime.now()
                    
                    # Log de sucesso apenas em modo debug
                    if element_type in ['salary', 'requirements']:  # Elementos mais difíceis
                        print(f"✅ [{element_type}] Sucesso com seletor: {strategy.selector[:30]}...")
                    
                    return result.strip()
                
            except Exception as e:
                # Atualizar estatísticas de falha
                strategy.fail_count += 1
                continue
        
        # Se todos falharam, retornar None
        print(f"⚠️ [{element_type}] Todos os seletores falharam")
        return None
    
    async def extract_multiple(self, page, element_type: str, parent_element=None) -> List[str]:
        """
        Extrai múltiplos elementos usando fallback
        
        Returns:
            Lista de valores extraídos
        """
        results = []
        
        if element_type not in self.selector_groups:
            return results
        
        strategies = sorted(
            self.selector_groups[element_type],
            key=lambda s: s.reliability_score,
            reverse=True
        )
        
        context = parent_element or page
        validator = self.validation_rules.get(element_type, lambda x: bool(x))
        
        for strategy in strategies[:3]:  # Tentar apenas top 3 estratégias para múltiplos
            try:
                elements = []
                
                if strategy.type == SelectorType.CSS:
                    elements = await context.query_selector_all(strategy.selector)
                
                elif strategy.type == SelectorType.XPATH:
                    elements = await context.query_selector_all(f'xpath={strategy.selector}')
                
                if elements:
                    for elem in elements:
                        try:
                            text = await elem.inner_text()
                            if text and validator(text):
                                results.append(text.strip())
                        except:
                            continue
                    
                    if results:
                        strategy.success_count += 1
                        strategy.last_success = datetime.now()
                        break
                
            except Exception:
                strategy.fail_count += 1
                continue
        
        return results
    
    def get_selector_stats(self) -> Dict[str, Dict]:
        """Retorna estatísticas dos seletores para análise"""
        stats = {}
        
        for element_type, strategies in self.selector_groups.items():
            stats[element_type] = {
                'total_strategies': len(strategies),
                'top_performer': max(strategies, key=lambda s: s.reliability_score).selector[:30] + '...',
                'average_reliability': sum(s.reliability_score for s in strategies) / len(strategies),
                'total_attempts': sum(s.success_count + s.fail_count for s in strategies),
                'success_rate': sum(s.success_count for s in strategies) / max(1, sum(s.success_count + s.fail_count for s in strategies))
            }
        
        return stats
    
    def adapt_selectors(self, element_type: str, successful_selector: str):
        """
        Adapta prioridades baseado em seletores bem-sucedidos
        Útil para auto-aprendizado
        """
        if element_type in self.selector_groups:
            for strategy in self.selector_groups[element_type]:
                if strategy.selector == successful_selector:
                    # Aumentar confiança do seletor bem-sucedido
                    strategy.confidence = min(1.0, strategy.confidence + 0.1)
                    break


# Instância global para reutilização
fallback_selector = FallbackSelector()