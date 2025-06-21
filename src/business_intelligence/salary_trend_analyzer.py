"""
Analisador de Tendências Salariais

Este módulo analisa tendências salariais com recursos avançados:
- Predição de salários futuros
- Análise por região e senioridade
- Identificação de outliers e padrões
- Visualização de tendências
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import statistics
from dataclasses import dataclass


@dataclass
class SalaryTrend:
    """Representa uma tendência salarial"""
    position: str
    region: str
    seniority: str
    salary_range: Tuple[float, float]
    trend_direction: str  # 'up', 'down', 'stable'
    trend_strength: float  # 0-1
    prediction_confidence: float  # 0-1
    sample_size: int
    

class SalaryTrendAnalyzer:
    """
    Analisador avançado de tendências salariais
    
    Funcionalidades:
    - Extração inteligente de salários de textos
    - Análise temporal de tendências
    - Predição de salários futuros
    - Segmentação por região e senioridade
    - Detecção de outliers
    """
    
    def __init__(self, data_file: str = "data/business_intelligence/salary_trends.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Criar diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Carregar dados históricos
        self.salary_data = self._load_salary_data()
        
        # Padrões para extração de salários
        self.salary_patterns = [
            r'R\$\s*(\d+[.,]?\d*)\s*(?:mil|k)?(?:\s*-\s*R\$\s*(\d+[.,]?\d*)\s*(?:mil|k)?)?',
            r'salário.*?R\$\s*(\d+[.,]?\d*)(?:\s*-\s*R\$\s*(\d+[.,]?\d*))?',
            r'remuneração.*?(\d+[.,]?\d*)\s*(?:mil|k)?(?:\s*-\s*(\d+[.,]?\d*)\s*(?:mil|k)?)?',
            r'(\d+)\s*(?:mil|k)(?:\s*-\s*(\d+)\s*(?:mil|k))?\s*reais?',
            r'faixa.*?(\d+[.,]?\d*)(?:\s*-\s*(\d+[.,]?\d*))?'
        ]
        
        # Mapeamento de regiões
        self.region_mapping = {
            'sao paulo': 'São Paulo',
            'sp': 'São Paulo',
            'rio de janeiro': 'Rio de Janeiro', 
            'rj': 'Rio de Janeiro',
            'minas gerais': 'Minas Gerais',
            'mg': 'Minas Gerais',
            'brasilia': 'Brasília',
            'df': 'Brasília',
            'home office': 'Remoto',
            'remoto': 'Remoto',
            'hibrido': 'Híbrido'
        }
        
        # Mapeamento de senioridade
        self.seniority_mapping = {
            'junior': 'Júnior',
            'jr': 'Júnior',
            'pleno': 'Pleno',
            'mid': 'Pleno',
            'senior': 'Sênior',
            'sr': 'Sênior',
            'lead': 'Lead',
            'especialista': 'Especialista',
            'coordenador': 'Coordenador',
            'gerente': 'Gerente'
        }
    
    def _load_salary_data(self) -> Dict:
        """Carrega dados históricos de salários"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "historical_data": [],
            "trends": {},
            "predictions": {},
            "last_analysis": None,
            "statistics": {
                "total_samples": 0,
                "positions_tracked": 0,
                "regions_covered": 0
            }
        }
    
    def _save_salary_data(self):
        """Salva dados de salários"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.salary_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados salariais: {e}")
    
    def extract_salary_from_text(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Extração inteligente de faixas salariais de texto
        
        Returns:
            Tupla (salário_mínimo, salário_máximo) ou None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        for pattern in self.salary_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                try:
                    groups = match.groups()
                    
                    # Primeiro valor
                    min_salary = float(groups[0].replace(',', '.'))
                    
                    # Segundo valor (se existir)
                    max_salary = min_salary
                    if len(groups) > 1 and groups[1]:
                        max_salary = float(groups[1].replace(',', '.'))
                    
                    # Converter para valores reais se necessário
                    if 'mil' in text_lower or 'k' in text_lower:
                        min_salary *= 1000
                        max_salary *= 1000
                    
                    # Validar valores razoáveis (R$ 1k - R$ 50k)
                    if 1000 <= min_salary <= 50000 and 1000 <= max_salary <= 50000:
                        return (min(min_salary, max_salary), max(min_salary, max_salary))
                        
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def classify_seniority(self, title: str, description: str = "") -> str:
        """Classifica senioridade baseada no título e descrição"""
        text = (title + " " + description).lower()
        
        for keyword, seniority in self.seniority_mapping.items():
            if keyword in text:
                return seniority
        
        # Heurísticas adicionais
        if any(word in text for word in ['trainee', 'estagiario', 'estagio']):
            return 'Trainee'
        elif any(word in text for word in ['diretor', 'vp', 'c-level']):
            return 'Executivo'
        
        return 'Não especificado'
    
    def classify_region(self, location: str) -> str:
        """Classifica região baseada na localização"""
        if not location:
            return 'Não especificado'
        
        location_lower = location.lower()
        
        for keyword, region in self.region_mapping.items():
            if keyword in location_lower:
                return region
        
        return 'Outras'
    
    def analyze_job_salary(self, job: Dict) -> Optional[Dict]:
        """
        Analisa salário de uma vaga específica
        
        Returns:
            Dicionário com análise salarial ou None
        """
        # Extrair salário do texto
        salary_text = job.get('salario', '') + " " + job.get('descricao', '')
        salary_range = self.extract_salary_from_text(salary_text)
        
        if not salary_range:
            return None
        
        # Classificar vaga
        position = job.get('titulo', 'Não especificado')
        region = self.classify_region(job.get('localizacao', ''))
        seniority = self.classify_seniority(job.get('titulo', ''), job.get('descricao', ''))
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'job_id': job.get('link', ''),
            'position': position,
            'region': region,
            'seniority': seniority,
            'salary_min': salary_range[0],
            'salary_max': salary_range[1],
            'salary_avg': (salary_range[0] + salary_range[1]) / 2,
            'source_url': job.get('fonte_url', ''),
            'company': job.get('empresa', 'Não informado')
        }
        
        # Adicionar aos dados históricos
        self.salary_data["historical_data"].append(analysis)
        self.salary_data["statistics"]["total_samples"] += 1
        
        return analysis
    
    def calculate_trends(self, days_back: int = 30) -> Dict[str, SalaryTrend]:
        """
        Calcula tendências salariais nos últimos N dias
        
        Returns:
            Dicionário de tendências por posição/região/senioridade
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Filtrar dados recentes
        recent_data = [
            entry for entry in self.salary_data["historical_data"]
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_date
        ]
        
        # Agrupar por posição, região e senioridade
        grouped_data = defaultdict(list)
        
        for entry in recent_data:
            key = f"{entry['position']}|{entry['region']}|{entry['seniority']}"
            grouped_data[key].append(entry)
        
        trends = {}
        
        for key, entries in grouped_data.items():
            if len(entries) < 3:  # Mínimo de amostras
                continue
            
            position, region, seniority = key.split('|')
            
            # Ordenar por timestamp
            entries.sort(key=lambda x: x['timestamp'])
            
            # Calcular tendência
            salaries = [entry['salary_avg'] for entry in entries]
            
            # Regressão linear simples
            n = len(salaries)
            x = list(range(n))
            
            # Calcular slope
            x_mean = statistics.mean(x)
            y_mean = statistics.mean(salaries)
            
            numerator = sum((x[i] - x_mean) * (salaries[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                slope = 0
            else:
                slope = numerator / denominator
            
            # Determinar direção da tendência
            if abs(slope) < 50:  # Variação menor que R$ 50 por período
                direction = 'stable'
                strength = 0.3
            elif slope > 0:
                direction = 'up'
                strength = min(abs(slope) / 1000, 1.0)  # Normalizar
            else:
                direction = 'down'
                strength = min(abs(slope) / 1000, 1.0)
            
            # Calcular faixa salarial atual
            recent_salaries = salaries[-min(5, len(salaries)):]
            salary_min = min(recent_salaries)
            salary_max = max(recent_salaries)
            
            # Confiança baseada no tamanho da amostra
            confidence = min(len(entries) / 10, 1.0)
            
            trend = SalaryTrend(
                position=position,
                region=region,
                seniority=seniority,
                salary_range=(salary_min, salary_max),
                trend_direction=direction,
                trend_strength=strength,
                prediction_confidence=confidence,
                sample_size=len(entries)
            )
            
            trends[key] = trend
        
        # Salvar tendências
        self.salary_data["trends"] = {
            key: {
                'position': trend.position,
                'region': trend.region,
                'seniority': trend.seniority,
                'salary_range': trend.salary_range,
                'trend_direction': trend.trend_direction,
                'trend_strength': trend.trend_strength,
                'prediction_confidence': trend.prediction_confidence,
                'sample_size': trend.sample_size,
                'analysis_date': datetime.now().isoformat()
            }
            for key, trend in trends.items()
        }
        
        self._save_salary_data()
        return trends
    
    def predict_salary_trend(self, position: str, region: str, seniority: str, months_ahead: int = 6) -> Optional[Dict]:
        """
        Prevê tendência salarial para os próximos meses
        
        Returns:
            Dicionário com predição ou None
        """
        key = f"{position}|{region}|{seniority}"
        
        if key not in self.salary_data.get("trends", {}):
            return None
        
        trend_data = self.salary_data["trends"][key]
        
        current_avg = sum(trend_data['salary_range']) / 2
        direction = trend_data['trend_direction']
        strength = trend_data['trend_strength']
        confidence = trend_data['prediction_confidence']
        
        # Calcular predição baseada na tendência
        if direction == 'stable':
            predicted_change = 0
        elif direction == 'up':
            predicted_change = strength * 500 * months_ahead  # Até R$ 500/mês
        else:  # down
            predicted_change = -strength * 300 * months_ahead  # Até -R$ 300/mês
        
        predicted_salary = current_avg + predicted_change
        
        # Ajustar confiança baseada no horizonte
        adjusted_confidence = confidence * (1 - (months_ahead / 12) * 0.5)
        
        prediction = {
            'position': position,
            'region': region,
            'seniority': seniority,
            'current_salary_avg': current_avg,
            'predicted_salary': predicted_salary,
            'predicted_change': predicted_change,
            'change_percentage': (predicted_change / current_avg) * 100 if current_avg > 0 else 0,
            'confidence': adjusted_confidence,
            'months_ahead': months_ahead,
            'prediction_date': datetime.now().isoformat()
        }
        
        return prediction
    
    def get_market_insights(self) -> Dict:
        """
        Gera insights sobre o mercado salarial
        
        Returns:
            Dicionário com insights do mercado
        """
        insights = {
            'highest_paying_positions': [],
            'fastest_growing_salaries': [],
            'regional_salary_comparison': {},
            'seniority_salary_gaps': {},
            'market_summary': {},
            'recommendations': []
        }
        
        if not self.salary_data["historical_data"]:
            insights['market_summary']['message'] = 'Dados insuficientes para análise'
            return insights
        
        # Calcular tendências atuais
        trends = self.calculate_trends()
        
        # Posições mais bem pagas
        position_salaries = defaultdict(list)
        for entry in self.salary_data["historical_data"]:
            position_salaries[entry['position']].append(entry['salary_avg'])
        
        avg_by_position = {
            pos: statistics.mean(salaries)
            for pos, salaries in position_salaries.items()
            if len(salaries) >= 3
        }
        
        insights['highest_paying_positions'] = [
            {'position': pos, 'avg_salary': round(salary, 2)}
            for pos, salary in sorted(avg_by_position.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Salários em crescimento mais rápido
        growth_trends = [
            trend for trend in trends.values()
            if trend.trend_direction == 'up' and trend.prediction_confidence > 0.5
        ]
        
        insights['fastest_growing_salaries'] = [
            {
                'position': trend.position,
                'region': trend.region,
                'seniority': trend.seniority,
                'growth_strength': round(trend.trend_strength, 2),
                'sample_size': trend.sample_size
            }
            for trend in sorted(growth_trends, key=lambda x: x.trend_strength, reverse=True)[:5]
        ]
        
        # Comparação regional
        regional_data = defaultdict(list)
        for entry in self.salary_data["historical_data"]:
            regional_data[entry['region']].append(entry['salary_avg'])
        
        insights['regional_salary_comparison'] = {
            region: {
                'avg_salary': round(statistics.mean(salaries), 2),
                'sample_size': len(salaries)
            }
            for region, salaries in regional_data.items()
            if len(salaries) >= 3
        }
        
        # Gaps por senioridade
        seniority_data = defaultdict(list)
        for entry in self.salary_data["historical_data"]:
            seniority_data[entry['seniority']].append(entry['salary_avg'])
        
        insights['seniority_salary_gaps'] = {
            seniority: {
                'avg_salary': round(statistics.mean(salaries), 2),
                'sample_size': len(salaries)
            }
            for seniority, salaries in seniority_data.items()
            if len(salaries) >= 3
        }
        
        # Sumário do mercado
        all_salaries = [entry['salary_avg'] for entry in self.salary_data["historical_data"]]
        if all_salaries:
            insights['market_summary'] = {
                'total_samples': len(all_salaries),
                'market_avg_salary': round(statistics.mean(all_salaries), 2),
                'salary_range': (round(min(all_salaries), 2), round(max(all_salaries), 2)),
                'positions_tracked': len(set(entry['position'] for entry in self.salary_data["historical_data"])),
                'regions_covered': len(set(entry['region'] for entry in self.salary_data["historical_data"]))
            }
        
        # Recomendações
        if growth_trends:
            insights['recommendations'].append(
                f"Considere posições em {growth_trends[0].position} - salários em crescimento"
            )
        
        if insights['regional_salary_comparison']:
            best_region = max(
                insights['regional_salary_comparison'].items(),
                key=lambda x: x[1]['avg_salary']
            )[0]
            insights['recommendations'].append(
                f"{best_region} oferece os melhores salários em média"
            )
        
        return insights
    
    def print_salary_trends_report(self):
        """Imprime relatório visual de tendências salariais"""
        from ..utils.menu_system import Colors
        
        print(f"\n{Colors.CYAN}💰 RELATÓRIO DE TENDÊNCIAS SALARIAIS{Colors.RESET}")
        print("=" * 60)
        
        insights = self.get_market_insights()
        
        # Sumário do mercado
        if 'market_avg_salary' in insights['market_summary']:
            summary = insights['market_summary']
            print(f"\n{Colors.YELLOW}📊 Visão Geral do Mercado:{Colors.RESET}")
            print(f"  • Salário médio: R$ {summary['market_avg_salary']:,.2f}")
            print(f"  • Faixa salarial: R$ {summary['salary_range'][0]:,.2f} - R$ {summary['salary_range'][1]:,.2f}")
            print(f"  • Posições analisadas: {summary['positions_tracked']}")
            print(f"  • Regiões cobertas: {summary['regions_covered']}")
        
        # Posições mais bem pagas
        if insights['highest_paying_positions']:
            print(f"\n{Colors.GREEN}💵 Posições Mais Bem Pagas:{Colors.RESET}")
            for i, pos in enumerate(insights['highest_paying_positions'][:5], 1):
                print(f"  {i}. {pos['position']}: R$ {pos['avg_salary']:,.2f}")
        
        # Salários em crescimento
        if insights['fastest_growing_salaries']:
            print(f"\n{Colors.GREEN}📈 Salários em Crescimento Rápido:{Colors.RESET}")
            for trend in insights['fastest_growing_salaries'][:3]:
                print(f"  • {trend['position']} ({trend['seniority']}, {trend['region']})")
                print(f"    Força do crescimento: {trend['growth_strength']:.2f}")
        
        # Comparação regional
        if insights['regional_salary_comparison']:
            print(f"\n{Colors.BLUE}🗺 Comparação Regional:{Colors.RESET}")
            for region, data in sorted(
                insights['regional_salary_comparison'].items(),
                key=lambda x: x[1]['avg_salary'],
                reverse=True
            )[:5]:
                print(f"  • {region}: R$ {data['avg_salary']:,.2f} ({data['sample_size']} vagas)")
        
        # Recomendações
        if insights['recommendations']:
            print(f"\n{Colors.YELLOW}💡 Recomendações:{Colors.RESET}")
            for rec in insights['recommendations']:
                print(f"  • {rec}")
        
        print("\n" + "=" * 60)


# Instância global do analisador de tendências salariais
salary_trend_analyzer = SalaryTrendAnalyzer()