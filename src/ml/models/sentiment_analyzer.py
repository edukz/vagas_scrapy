"""
Analisador de Sentimento para Descrições de Vagas
=================================================

Analisa o tom e sentimento das descrições para identificar:
- Ambiente de trabalho (positivo/negativo)
- Cultura da empresa
- Urgência da contratação
- Benefícios e vantagens
"""

import re
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter
import joblib
from pathlib import Path


@dataclass
class SentimentScore:
    """Scores de sentimento"""
    positive: float
    negative: float
    neutral: float
    
    @property
    def overall(self) -> str:
        """Sentimento predominante"""
        scores = {
            'positive': self.positive,
            'negative': self.negative,
            'neutral': self.neutral
        }
        return max(scores, key=scores.get)
    
    @property
    def confidence(self) -> float:
        """Confiança na classificação"""
        return max(self.positive, self.negative, self.neutral)


class SentimentAnalyzer:
    """
    Analisador de sentimento especializado em vagas de emprego
    
    Características analisadas:
    - Tom geral da descrição
    - Palavras positivas vs negativas
    - Urgência e pressão
    - Benefícios oferecidos
    - Cultura organizacional
    """
    
    def __init__(self):
        # Dicionários de palavras por categoria
        self.lexicons = {
            'positive': {
                'ambiente': ['dinâmico', 'inovador', 'colaborativo', 'descontraído', 
                           'flexível', 'moderno', 'agradável', 'motivador', 'inspirador'],
                'crescimento': ['crescimento', 'desenvolvimento', 'carreira', 'evolução',
                              'aprendizado', 'capacitação', 'mentoria', 'treinamento'],
                'benefícios': ['benefícios', 'vantagens', 'bônus', 'premiação', 'plr',
                              'home office', 'flexibilidade', 'vale', 'convênio', 
                              'gympass', 'plano de saúde'],
                'cultura': ['equilíbrio', 'work-life balance', 'qualidade de vida',
                          'diversidade', 'inclusão', 'respeito', 'reconhecimento'],
                'oportunidade': ['oportunidade', 'desafio', 'impacto', 'diferença',
                               'contribuir', 'transformar', 'liderar', 'construir']
            },
            'negative': {
                'pressão': ['urgente', 'imediato', 'pressão', 'prazo apertado', 
                          'alta demanda', 'estressante', 'corrido'],
                'exigências': ['imprescindível', 'obrigatório', 'exige-se', 'fundamental',
                             'indispensável', 'rigoroso', 'estrito'],
                'sobrecarga': ['multitarefas', 'acúmulo', 'sobrecarga', 'hora extra',
                             'disponibilidade total', 'dedicação exclusiva'],
                'ambiente': ['tradicional', 'hierárquico', 'rígido', 'conservador',
                           'burocrático', 'formal'],
                'indefinido': ['a combinar', 'não informado', 'variável', 'depende']
            },
            'urgency': {
                'high': ['urgente', 'imediato', 'asap', 'início imediato', 
                        'vaga emergencial', 'com urgência'],
                'medium': ['breve', 'em breve', 'próximas semanas', 'rapidamente'],
                'low': ['sem pressa', 'processo seletivo', 'etapas', 'análise']
            }
        }
        
        # Pesos para diferentes aspectos
        self.aspect_weights = {
            'benefícios': 1.5,      # Benefícios têm peso maior
            'cultura': 1.3,         # Cultura positiva é importante
            'crescimento': 1.2,     # Oportunidades de crescimento
            'ambiente': 1.0,        # Ambiente de trabalho
            'pressão': -1.5,        # Pressão negativa tem peso maior
            'sobrecarga': -1.3,     # Sobrecarga é muito negativa
            'exigências': -0.8      # Muitas exigências
        }
        
        # Emojis e sua polaridade
        self.emoji_sentiment = {
            'positive': ['😊', '🚀', '💪', '🌟', '✨', '🎯', '💡', '🏆', '👏', '❤️'],
            'negative': ['😓', '😰', '⚠️', '🔥', '⏰', '😤', '😩'],
            'neutral': ['📍', '📧', '📱', '💻', '🏢', '📊', '📈']
        }
        
        # Padrões de regex
        self.patterns = {
            'salary_mentioned': re.compile(r'sal[áa]rio|remunera[çc][ãa]o|CLT|PJ|faixa', re.I),
            'benefits_section': re.compile(r'benef[íi]cios|vantagens|oferecemos|diferenciais', re.I),
            'requirements_section': re.compile(r'requisitos|exig[êe]ncias|precisa|necess[áa]rio', re.I),
            'company_culture': re.compile(r'cultura|valores|miss[ãa]o|prop[óo]sito', re.I)
        }
    
    def analyze(self, text: str, title: str = "") -> Dict[str, any]:
        """
        Analisa o sentimento de uma descrição de vaga
        
        Args:
            text: Descrição da vaga
            title: Título da vaga (opcional)
            
        Returns:
            Análise completa de sentimento
        """
        full_text = f"{title} {text}".lower()
        
        # Análise básica de sentimento
        sentiment_scores = self._calculate_sentiment_scores(full_text)
        
        # Análise de aspectos específicos
        aspects = self._analyze_aspects(full_text)
        
        # Detectar urgência
        urgency = self._detect_urgency(full_text)
        
        # Analisar benefícios
        benefits_score = self._analyze_benefits(full_text)
        
        # Analisar cultura
        culture_indicators = self._analyze_culture(full_text)
        
        # Calcular score geral
        overall_score = self._calculate_overall_score(
            sentiment_scores, aspects, benefits_score
        )
        
        # Gerar insights
        insights = self._generate_insights(
            sentiment_scores, aspects, urgency, 
            benefits_score, culture_indicators
        )
        
        return {
            'sentiment': sentiment_scores.overall,
            'scores': {
                'positive': sentiment_scores.positive,
                'negative': sentiment_scores.negative,
                'neutral': sentiment_scores.neutral
            },
            'confidence': sentiment_scores.confidence,
            'aspects': aspects,
            'urgency': urgency,
            'benefits_score': benefits_score,
            'culture_indicators': culture_indicators,
            'overall_score': overall_score,
            'insights': insights,
            'recommendation': self._generate_recommendation(overall_score)
        }
    
    def _calculate_sentiment_scores(self, text: str) -> SentimentScore:
        """Calcula scores básicos de sentimento"""
        positive_count = 0
        negative_count = 0
        total_relevant_words = 0
        
        # Contar palavras positivas
        for category, words in self.lexicons['positive'].items():
            for word in words:
                count = text.lower().count(word.lower())
                if count > 0:
                    weight = self.aspect_weights.get(category, 1.0)
                    positive_count += count * abs(weight)
                    total_relevant_words += count
        
        # Contar palavras negativas
        for category, words in self.lexicons['negative'].items():
            for word in words:
                count = text.lower().count(word.lower())
                if count > 0:
                    weight = self.aspect_weights.get(category, -1.0)
                    negative_count += count * abs(weight)
                    total_relevant_words += count
        
        # Contar emojis
        for emoji_type, emojis in self.emoji_sentiment.items():
            for emoji in emojis:
                if emoji in text:
                    if emoji_type == 'positive':
                        positive_count += 2  # Emojis têm peso maior
                    elif emoji_type == 'negative':
                        negative_count += 2
                    total_relevant_words += 1
        
        # Calcular proporções
        if total_relevant_words == 0:
            return SentimentScore(0.0, 0.0, 1.0)  # Neutro por padrão
        
        positive_ratio = positive_count / (positive_count + negative_count + 1)
        negative_ratio = negative_count / (positive_count + negative_count + 1)
        
        # Ajustar para somar 1.0
        neutral_ratio = max(0, 1.0 - positive_ratio - negative_ratio)
        
        # Normalizar
        total = positive_ratio + negative_ratio + neutral_ratio
        if total > 0:
            positive_ratio /= total
            negative_ratio /= total
            neutral_ratio /= total
        
        return SentimentScore(
            positive=round(positive_ratio, 3),
            negative=round(negative_ratio, 3),
            neutral=round(neutral_ratio, 3)
        )
    
    def _analyze_aspects(self, text: str) -> Dict[str, Dict]:
        """Analisa aspectos específicos da vaga"""
        aspects = {}
        
        # Analisar cada categoria
        for sentiment_type in ['positive', 'negative']:
            for category, words in self.lexicons[sentiment_type].items():
                found_words = []
                score = 0
                
                for word in words:
                    if word.lower() in text:
                        found_words.append(word)
                        score += 1
                
                if found_words:
                    aspects[category] = {
                        'sentiment': sentiment_type,
                        'score': score,
                        'words_found': found_words[:5],  # Top 5
                        'weight': self.aspect_weights.get(category, 1.0)
                    }
        
        return aspects
    
    def _detect_urgency(self, text: str) -> Dict[str, any]:
        """Detecta nível de urgência na contratação"""
        urgency_scores = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for level, keywords in self.lexicons['urgency'].items():
            for keyword in keywords:
                if keyword.lower() in text:
                    urgency_scores[level] += 1
        
        # Determinar nível predominante
        max_level = max(urgency_scores, key=urgency_scores.get)
        total_indicators = sum(urgency_scores.values())
        
        return {
            'level': max_level if total_indicators > 0 else 'medium',
            'indicators': urgency_scores,
            'confidence': urgency_scores[max_level] / max(total_indicators, 1)
        }
    
    def _analyze_benefits(self, text: str) -> Dict[str, any]:
        """Analisa benefícios mencionados"""
        benefits_found = []
        benefit_keywords = self.lexicons['positive']['benefícios']
        
        for benefit in benefit_keywords:
            if benefit.lower() in text:
                benefits_found.append(benefit)
        
        # Verificar se há seção de benefícios
        has_benefits_section = bool(self.patterns['benefits_section'].search(text))
        
        # Calcular score
        score = len(benefits_found)
        if has_benefits_section:
            score *= 1.5  # Bonus por ter seção dedicada
        
        return {
            'score': min(score / 10, 1.0),  # Normalizado 0-1
            'count': len(benefits_found),
            'benefits': benefits_found[:10],  # Top 10
            'has_section': has_benefits_section
        }
    
    def _analyze_culture(self, text: str) -> Dict[str, any]:
        """Analisa indicadores de cultura organizacional"""
        culture_positive = []
        culture_negative = []
        
        # Palavras positivas de cultura
        for word in self.lexicons['positive']['cultura']:
            if word.lower() in text:
                culture_positive.append(word)
        
        # Palavras negativas de ambiente
        for word in self.lexicons['negative']['ambiente']:
            if word.lower() in text:
                culture_negative.append(word)
        
        # Verificar menção explícita de cultura
        mentions_culture = bool(self.patterns['company_culture'].search(text))
        
        # Calcular score de cultura
        culture_score = (len(culture_positive) - len(culture_negative)) / 10
        culture_score = max(-1, min(1, culture_score))  # Limitar entre -1 e 1
        
        return {
            'score': culture_score,
            'positive_indicators': culture_positive,
            'negative_indicators': culture_negative,
            'mentions_culture': mentions_culture,
            'assessment': self._assess_culture(culture_score)
        }
    
    def _assess_culture(self, score: float) -> str:
        """Avalia a cultura com base no score"""
        if score >= 0.5:
            return "Muito Positiva"
        elif score >= 0.2:
            return "Positiva"
        elif score >= -0.2:
            return "Neutra"
        elif score >= -0.5:
            return "Negativa"
        else:
            return "Muito Negativa"
    
    def _calculate_overall_score(self, sentiment: SentimentScore,
                                aspects: Dict, benefits: Dict) -> float:
        """Calcula score geral da vaga (0-10)"""
        # Base score do sentimento
        base_score = (sentiment.positive - sentiment.negative) * 5 + 5
        
        # Ajustar por aspectos
        aspect_adjustment = 0
        for aspect, data in aspects.items():
            weight = data['weight']
            if data['sentiment'] == 'positive':
                aspect_adjustment += weight * 0.5
            else:
                aspect_adjustment += weight * 0.5  # weight já é negativo
        
        # Ajustar por benefícios
        benefits_adjustment = benefits['score'] * 2
        
        # Score final
        final_score = base_score + aspect_adjustment + benefits_adjustment
        
        # Limitar entre 0 e 10
        return max(0, min(10, final_score))
    
    def _generate_insights(self, sentiment: SentimentScore, aspects: Dict,
                          urgency: Dict, benefits: Dict, culture: Dict) -> List[str]:
        """Gera insights sobre a vaga"""
        insights = []
        
        # Insight sobre sentimento geral
        if sentiment.positive > 0.6:
            insights.append("✅ Descrição muito positiva e acolhedora")
        elif sentiment.negative > 0.6:
            insights.append("⚠️ Tom da descrição pode afastar candidatos")
        
        # Insights sobre aspectos
        if 'crescimento' in aspects and aspects['crescimento']['sentiment'] == 'positive':
            insights.append("📈 Forte ênfase em desenvolvimento profissional")
        
        if 'pressão' in aspects:
            insights.append("⏰ Ambiente aparenta ter alta pressão")
        
        if 'benefícios' in aspects and aspects['benefícios']['score'] > 3:
            insights.append("🎁 Pacote de benefícios atrativo")
        
        # Insight sobre urgência
        if urgency['level'] == 'high':
            insights.append("🚨 Contratação urgente - processo pode ser acelerado")
        
        # Insight sobre cultura
        if culture['score'] > 0.5:
            insights.append("🌟 Cultura organizacional aparenta ser muito positiva")
        elif culture['score'] < -0.3:
            insights.append("🏢 Ambiente mais tradicional e hierárquico")
        
        # Insight sobre transparência
        if not self.patterns['salary_mentioned'].search(sentiment.overall):
            insights.append("💰 Salário não mencionado - perguntar na entrevista")
        
        return insights
    
    def _generate_recommendation(self, overall_score: float) -> str:
        """Gera recomendação baseada no score"""
        if overall_score >= 8:
            return "Altamente Recomendada - Excelente oportunidade"
        elif overall_score >= 6.5:
            return "Recomendada - Boa oportunidade"
        elif overall_score >= 5:
            return "Neutra - Avaliar com cuidado"
        elif overall_score >= 3.5:
            return "Cautela - Alguns pontos negativos"
        else:
            return "Não Recomendada - Muitos aspectos negativos"
    
    def batch_analyze(self, jobs: List[Dict]) -> List[Dict]:
        """Analisa sentimento de múltiplas vagas"""
        results = []
        
        for job in jobs:
            title = job.get('titulo', '')
            description = job.get('descricao', '')
            
            if description:
                analysis = self.analyze(description, title)
                
                # Adicionar análise ao job
                job_with_sentiment = job.copy()
                job_with_sentiment['sentiment_analysis'] = analysis
                job_with_sentiment['sentiment_score'] = analysis['overall_score']
                job_with_sentiment['sentiment_recommendation'] = analysis['recommendation']
                
                results.append(job_with_sentiment)
            else:
                results.append(job)
        
        return results
    
    def get_statistics(self, analyzed_jobs: List[Dict]) -> Dict:
        """Gera estatísticas sobre jobs analisados"""
        if not analyzed_jobs:
            return {}
        
        sentiments = []
        scores = []
        urgencies = []
        cultures = []
        
        for job in analyzed_jobs:
            if 'sentiment_analysis' in job:
                analysis = job['sentiment_analysis']
                sentiments.append(analysis['sentiment'])
                scores.append(analysis['overall_score'])
                urgencies.append(analysis['urgency']['level'])
                cultures.append(analysis['culture_indicators']['assessment'])
        
        if not sentiments:
            return {}
        
        # Calcular estatísticas
        sentiment_dist = Counter(sentiments)
        urgency_dist = Counter(urgencies)
        culture_dist = Counter(cultures)
        avg_score = np.mean(scores)
        
        return {
            'total_analyzed': len(sentiments),
            'sentiment_distribution': dict(sentiment_dist),
            'average_score': round(avg_score, 2),
            'score_distribution': {
                'excellent': len([s for s in scores if s >= 8]),
                'good': len([s for s in scores if 6.5 <= s < 8]),
                'neutral': len([s for s in scores if 5 <= s < 6.5]),
                'caution': len([s for s in scores if 3.5 <= s < 5]),
                'not_recommended': len([s for s in scores if s < 3.5])
            },
            'urgency_distribution': dict(urgency_dist),
            'culture_distribution': dict(culture_dist),
            'top_positive_companies': self._get_top_companies(analyzed_jobs, 'positive'),
            'top_negative_companies': self._get_top_companies(analyzed_jobs, 'negative')
        }
    
    def _get_top_companies(self, jobs: List[Dict], 
                          sentiment_type: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Identifica empresas com melhor/pior sentimento"""
        company_scores = {}
        company_counts = {}
        
        for job in jobs:
            company = job.get('empresa', 'N/A')
            if company != 'N/A' and 'sentiment_analysis' in job:
                score = job['sentiment_analysis']['overall_score']
                
                if company not in company_scores:
                    company_scores[company] = []
                company_scores[company].append(score)
        
        # Calcular médias
        company_avg = {
            company: np.mean(scores)
            for company, scores in company_scores.items()
            if len(scores) >= 2  # Mínimo 2 vagas para ser relevante
        }
        
        # Ordenar
        if sentiment_type == 'positive':
            sorted_companies = sorted(
                company_avg.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
        else:
            sorted_companies = sorted(
                company_avg.items(), 
                key=lambda x: x[1]
            )
        
        return sorted_companies[:limit]


# Exemplo de uso
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    # Exemplo positivo
    positive_example = """
    Junte-se ao nosso time incrível! 🚀
    
    Somos uma startup em crescimento acelerado, com ambiente descontraído
    e cultura de inovação. Oferecemos:
    
    ✅ Salário competitivo + Stock Options
    ✅ Home office flexível
    ✅ Plano de saúde premium
    ✅ Gympass e auxílio bem-estar
    ✅ Budget para educação
    ✅ Horário flexível
    
    Buscamos pessoas que queiram fazer a diferença e crescer conosco!
    Processo seletivo humanizado e rápido.
    """
    
    # Exemplo negativo
    negative_example = """
    URGENTE - Vaga para início IMEDIATO
    
    Exige-se total disponibilidade e dedicação exclusiva.
    Ambiente de alta pressão e prazos apertados.
    Necessário experiência comprovada em multitarefas.
    
    Requisitos obrigatórios:
    - Disponibilidade para horas extras
    - Trabalho sob pressão constante
    - Resiliência para ambiente tradicional
    
    Salário a combinar.
    """
    
    print("=== Análise Positiva ===")
    result1 = analyzer.analyze(positive_example, "Desenvolvedor Full Stack")
    print(f"Sentimento: {result1['sentiment']}")
    print(f"Score: {result1['overall_score']:.1f}/10")
    print(f"Recomendação: {result1['recommendation']}")
    print(f"Insights: {result1['insights']}")
    
    print("\n=== Análise Negativa ===")
    result2 = analyzer.analyze(negative_example, "Analista de Sistemas")
    print(f"Sentimento: {result2['sentiment']}")
    print(f"Score: {result2['overall_score']:.1f}/10")
    print(f"Recomendação: {result2['recommendation']}")
    print(f"Insights: {result2['insights']}")