"""
Comparador de Dados Históricos

Este módulo implementa:
- Comparação temporal de métricas
- Análise de evolução do mercado
- Detecção de padrões sazonais
- Benchmarking histórico
- Projeções baseadas em tendências
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import statistics
from dataclasses import dataclass


@dataclass
class HistoricalComparison:
    """Representa uma comparação entre períodos"""
    metric: str
    current_period: Dict
    previous_period: Dict
    change_percentage: float
    trend: str  # 'up', 'down', 'stable'
    significance: str  # 'high', 'medium', 'low'


@dataclass
class SeasonalPattern:
    """Representa um padrão sazonal identificado"""
    pattern_type: str
    frequency: str  # 'weekly', 'monthly', 'quarterly'
    peak_periods: List[str]
    low_periods: List[str]
    amplitude: float
    confidence: float


class HistoricalDataComparator:
    """
    Comparador de dados históricos para análise temporal
    
    Funcionalidades:
    - Comparação período-a-período
    - Análise de tendências de longo prazo
    - Detecção de sazonalidade
    - Benchmarking histórico
    - Projeções futuras
    """
    
    def __init__(self, data_file: str = "data/business_intelligence/historical_comparisons.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Criar diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Carregar dados históricos
        self.historical_data = self._load_historical_data()
        
        # Períodos padrão para comparação
        self.comparison_periods = {
            'week': timedelta(days=7),
            'month': timedelta(days=30),
            'quarter': timedelta(days=90),
            'year': timedelta(days=365)
        }
    
    def _load_historical_data(self) -> Dict:
        """Carrega dados históricos de comparações"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "time_series": {},
            "comparisons": [],
            "seasonal_patterns": {},
            "benchmarks": {},
            "projections": {},
            "last_update": None,
            "statistics": {
                "periods_analyzed": 0,
                "comparisons_made": 0
            }
        }
    
    def _save_historical_data(self):
        """Salva dados históricos"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.historical_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados históricos: {e}")
    
    def add_time_series_data(self, metric_name: str, data_point: Dict):
        """
        Adiciona ponto de dados à série temporal
        
        Args:
            metric_name: Nome da métrica
            data_point: Dados do ponto temporal
        """
        timestamp = data_point.get('timestamp', datetime.now().isoformat())
        
        if metric_name not in self.historical_data["time_series"]:
            self.historical_data["time_series"][metric_name] = []
        
        # Adicionar ponto com timestamp
        data_point['timestamp'] = timestamp
        self.historical_data["time_series"][metric_name].append(data_point)
        
        # Manter apenas os últimos 365 pontos (1 ano)
        if len(self.historical_data["time_series"][metric_name]) > 365:
            self.historical_data["time_series"][metric_name] = \
                self.historical_data["time_series"][metric_name][-365:]
        
        self._save_historical_data()
    
    def compare_periods(self, jobs_current: List[Dict], 
                       jobs_previous: List[Dict], 
                       period_name: str = "month") -> Dict[str, HistoricalComparison]:
        """
        Compara dois períodos de dados
        
        Args:
            jobs_current: Vagas do período atual
            jobs_previous: Vagas do período anterior
            period_name: Nome do período de comparação
            
        Returns:
            Dicionário com comparações por métrica
        """
        comparisons = {}
        
        # Métricas para comparar
        metrics_to_compare = [
            'job_count',
            'avg_salary',
            'remote_percentage',
            'top_skills_frequency',
            'regional_distribution'
        ]
        
        for metric in metrics_to_compare:
            comparison = self._compare_metric(
                metric, jobs_current, jobs_previous, period_name
            )
            if comparison:
                comparisons[metric] = comparison
        
        # Salvar comparações
        comparison_record = {
            'timestamp': datetime.now().isoformat(),
            'period_name': period_name,
            'comparisons': {
                metric: {
                    'metric': comp.metric,
                    'current_value': comp.current_period.get('value'),
                    'previous_value': comp.previous_period.get('value'),
                    'change_percentage': comp.change_percentage,
                    'trend': comp.trend,
                    'significance': comp.significance
                }
                for metric, comp in comparisons.items()
            }
        }
        
        self.historical_data["comparisons"].append(comparison_record)
        
        # Manter apenas as últimas 100 comparações
        if len(self.historical_data["comparisons"]) > 100:
            self.historical_data["comparisons"] = self.historical_data["comparisons"][-100:]
        
        self._save_historical_data()
        return comparisons
    
    def _compare_metric(self, metric_name: str, current_jobs: List[Dict], 
                       previous_jobs: List[Dict], period_name: str) -> Optional[HistoricalComparison]:
        """Compara uma métrica específica entre períodos"""
        try:
            current_value = self._calculate_metric_value(metric_name, current_jobs)
            previous_value = self._calculate_metric_value(metric_name, previous_jobs)
            
            if current_value is None or previous_value is None:
                return None
            
            # Calcular mudança percentual
            if previous_value != 0:
                change_pct = ((current_value - previous_value) / previous_value) * 100
            else:
                change_pct = 100 if current_value > 0 else 0
            
            # Determinar tendência
            if abs(change_pct) < 5:  # Mudança menor que 5%
                trend = 'stable'
            elif change_pct > 0:
                trend = 'up'
            else:
                trend = 'down'
            
            # Determinar significância
            if abs(change_pct) > 25:
                significance = 'high'
            elif abs(change_pct) > 10:
                significance = 'medium'
            else:
                significance = 'low'
            
            return HistoricalComparison(
                metric=metric_name,
                current_period={
                    'value': current_value,
                    'period': 'current',
                    'job_count': len(current_jobs)
                },
                previous_period={
                    'value': previous_value,
                    'period': 'previous',
                    'job_count': len(previous_jobs)
                },
                change_percentage=change_pct,
                trend=trend,
                significance=significance
            )
            
        except Exception as e:
            print(f"Erro ao comparar métrica {metric_name}: {e}")
            return None
    
    def _calculate_metric_value(self, metric_name: str, jobs: List[Dict]) -> Optional[float]:
        """Calcula valor de uma métrica específica"""
        if not jobs:
            return None
        
        try:
            if metric_name == 'job_count':
                return float(len(jobs))
            
            elif metric_name == 'avg_salary':
                salaries = []
                for job in jobs:
                    salary = self._extract_salary_value(job.get('salario', ''))
                    if salary:
                        salaries.append(salary)
                return statistics.mean(salaries) if salaries else 0
            
            elif metric_name == 'remote_percentage':
                remote_count = 0
                for job in jobs:
                    location = job.get('localizacao', '').lower()
                    if any(term in location for term in ['remoto', 'home office', 'hibrido']):
                        remote_count += 1
                return (remote_count / len(jobs)) * 100
            
            elif metric_name == 'top_skills_frequency':
                # Frequência média das top 5 skills
                skills_count = defaultdict(int)
                for job in jobs:
                    description = f"{job.get('titulo', '')} {job.get('descricao', '')}"
                    skills = self._extract_basic_skills(description)
                    for skill in skills:
                        skills_count[skill] += 1
                
                if skills_count:
                    top_5_counts = sorted(skills_count.values(), reverse=True)[:5]
                    return statistics.mean(top_5_counts) if top_5_counts else 0
                return 0
            
            elif metric_name == 'regional_distribution':
                # Índice de concentração regional (entropia)
                regional_counts = defaultdict(int)
                for job in jobs:
                    region = self._normalize_region(job.get('localizacao', ''))
                    regional_counts[region] += 1
                
                if not regional_counts:
                    return 0
                
                # Calcular entropia como medida de distribuição
                total = sum(regional_counts.values())
                entropy = 0
                for count in regional_counts.values():
                    p = count / total
                    if p > 0:
                        entropy -= p * (p ** 0.5)  # Simplified entropy
                
                return entropy
            
        except Exception as e:
            print(f"Erro ao calcular métrica {metric_name}: {e}")
            return None
    
    def _extract_salary_value(self, salary_text: str) -> Optional[float]:
        """Extrai valor salarial simples"""
        if not salary_text or salary_text.lower() in ['não informado', 'a combinar']:
            return None
        
        # Extração básica de números
        import re
        numbers = re.findall(r'[\d,\.]+', salary_text.replace('.', '').replace(',', '.'))
        if numbers:
            try:
                return float(numbers[0])
            except:
                pass
        return None
    
    def _extract_basic_skills(self, text: str) -> List[str]:
        """Extração básica de skills"""
        basic_skills = ['python', 'javascript', 'java', 'react', 'sql', 'aws', 'docker']
        found_skills = []
        text_lower = text.lower()
        
        for skill in basic_skills:
            if skill in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def _normalize_region(self, location: str) -> str:
        """Normalização básica de região"""
        if not location:
            return 'Não especificado'
        
        location_lower = location.lower()
        if 'sp' in location_lower or 'são paulo' in location_lower:
            return 'São Paulo'
        elif 'rj' in location_lower or 'rio' in location_lower:
            return 'Rio de Janeiro'
        elif 'remoto' in location_lower or 'home office' in location_lower:
            return 'Remoto'
        else:
            return 'Outras'
    
    def detect_seasonal_patterns(self, metric_name: str, lookback_days: int = 180) -> Optional[SeasonalPattern]:
        """
        Detecta padrões sazonais em uma métrica
        
        Args:
            metric_name: Nome da métrica a analisar
            lookback_days: Dias para análise retrospectiva
            
        Returns:
            Padrão sazonal detectado ou None
        """
        if metric_name not in self.historical_data["time_series"]:
            return None
        
        time_series = self.historical_data["time_series"][metric_name]
        if len(time_series) < 30:  # Dados insuficientes
            return None
        
        try:
            # Agrupar dados por semana
            weekly_data = defaultdict(list)
            monthly_data = defaultdict(list)
            
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            for point in time_series:
                try:
                    timestamp = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
                    if timestamp >= cutoff_date:
                        week_of_year = timestamp.isocalendar()[1]
                        month = timestamp.month
                        value = point.get('value', 0)
                        
                        weekly_data[week_of_year].append(value)
                        monthly_data[month].append(value)
                except:
                    continue
            
            # Analisar padrão semanal
            if len(weekly_data) >= 4:
                weekly_pattern = self._analyze_pattern(weekly_data, 'weekly')
                if weekly_pattern:
                    return weekly_pattern
            
            # Analisar padrão mensal
            if len(monthly_data) >= 3:
                monthly_pattern = self._analyze_pattern(monthly_data, 'monthly')
                if monthly_pattern:
                    return monthly_pattern
            
        except Exception as e:
            print(f"Erro ao detectar padrões sazonais: {e}")
        
        return None
    
    def _analyze_pattern(self, grouped_data: Dict, frequency: str) -> Optional[SeasonalPattern]:
        """Analisa padrão em dados agrupados"""
        try:
            # Calcular médias por período
            period_averages = {}
            for period, values in grouped_data.items():
                if values:
                    period_averages[period] = statistics.mean(values)
            
            if len(period_averages) < 3:
                return None
            
            # Calcular estatísticas
            all_averages = list(period_averages.values())
            overall_mean = statistics.mean(all_averages)
            std_dev = statistics.stdev(all_averages) if len(all_averages) > 1 else 0
            
            if std_dev == 0:
                return None
            
            # Identificar picos e vales
            peak_periods = []
            low_periods = []
            
            for period, avg in period_averages.items():
                if avg > overall_mean + std_dev * 0.5:  # Acima de 0.5 desvios padrão
                    peak_periods.append(str(period))
                elif avg < overall_mean - std_dev * 0.5:  # Abaixo de 0.5 desvios padrão
                    low_periods.append(str(period))
            
            # Calcular amplitude (variação relativa)
            amplitude = (max(all_averages) - min(all_averages)) / overall_mean * 100
            
            # Calcular confiança baseada na consistência
            confidence = min(100, (std_dev / overall_mean * 100)) if overall_mean > 0 else 0
            
            # Só retornar padrão se houver variação significativa
            if amplitude < 10:  # Menos de 10% de variação
                return None
            
            return SeasonalPattern(
                pattern_type=f"{frequency}_seasonal",
                frequency=frequency,
                peak_periods=peak_periods,
                low_periods=low_periods,
                amplitude=amplitude,
                confidence=confidence
            )
            
        except Exception as e:
            print(f"Erro ao analisar padrão: {e}")
            return None
    
    def get_historical_benchmarks(self, metric_name: str) -> Dict:
        """
        Retorna benchmarks históricos para uma métrica
        
        Args:
            metric_name: Nome da métrica
            
        Returns:
            Benchmarks históricos (min, max, médio, mediana)
        """
        benchmarks = {
            'min': None,
            'max': None,
            'average': None,
            'median': None,
            'percentile_25': None,
            'percentile_75': None,
            'data_points': 0
        }
        
        if metric_name not in self.historical_data["time_series"]:
            return benchmarks
        
        time_series = self.historical_data["time_series"][metric_name]
        values = []
        
        for point in time_series:
            value = point.get('value')
            if value is not None:
                values.append(value)
        
        if not values:
            return benchmarks
        
        try:
            benchmarks.update({
                'min': min(values),
                'max': max(values),
                'average': statistics.mean(values),
                'median': statistics.median(values),
                'data_points': len(values)
            })
            
            # Percentis se há dados suficientes
            if len(values) >= 4:
                sorted_values = sorted(values)
                benchmarks['percentile_25'] = sorted_values[len(values) // 4]
                benchmarks['percentile_75'] = sorted_values[3 * len(values) // 4]
            
        except Exception as e:
            print(f"Erro ao calcular benchmarks: {e}")
        
        return benchmarks
    
    def generate_trend_projection(self, metric_name: str, periods_ahead: int = 4) -> Dict:
        """
        Gera projeção de tendência para uma métrica
        
        Args:
            metric_name: Nome da métrica
            periods_ahead: Número de períodos para projetar
            
        Returns:
            Projeção de tendência
        """
        projection = {
            'metric': metric_name,
            'projection_method': 'linear_trend',
            'periods_ahead': periods_ahead,
            'projected_values': [],
            'confidence': 'low',
            'trend_direction': 'stable'
        }
        
        if metric_name not in self.historical_data["time_series"]:
            return projection
        
        time_series = self.historical_data["time_series"][metric_name][-20:]  # Últimos 20 pontos
        
        if len(time_series) < 5:
            return projection
        
        try:
            # Extrair valores e calcular tendência simples
            values = []
            for point in time_series:
                value = point.get('value')
                if value is not None:
                    values.append(value)
            
            if len(values) < 3:
                return projection
            
            # Calcular tendência linear simples
            n = len(values)
            x_values = list(range(n))
            
            # Regressão linear simples
            sum_x = sum(x_values)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(x_values, values))
            sum_x2 = sum(x * x for x in x_values)
            
            # Coeficientes da linha de tendência
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
            
            # Projetar valores futuros
            last_x = n - 1
            projected_values = []
            
            for i in range(1, periods_ahead + 1):
                future_x = last_x + i
                projected_value = slope * future_x + intercept
                projected_values.append({
                    'period': i,
                    'projected_value': projected_value
                })
            
            # Determinar direção da tendência
            if abs(slope) < 0.1:
                trend_direction = 'stable'
            elif slope > 0:
                trend_direction = 'increasing'
            else:
                trend_direction = 'decreasing'
            
            # Calcular confiança baseada na variabilidade
            variance = statistics.variance(values) if len(values) > 1 else 0
            mean_value = statistics.mean(values)
            cv = (variance ** 0.5) / mean_value if mean_value > 0 else 1
            
            if cv < 0.1:
                confidence = 'high'
            elif cv < 0.3:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            projection.update({
                'projected_values': projected_values,
                'confidence': confidence,
                'trend_direction': trend_direction,
                'slope': slope,
                'data_points_used': len(values)
            })
            
        except Exception as e:
            print(f"Erro ao gerar projeção: {e}")
        
        return projection
    
    def print_historical_comparison_report(self, comparisons: Dict[str, HistoricalComparison]):
        """Imprime relatório de comparação histórica"""
        from ..utils.menu_system import Colors
        
        print(f"\n{Colors.CYAN}📈 ANÁLISE COMPARATIVA HISTÓRICA{Colors.RESET}")
        print("=" * 60)
        
        if not comparisons:
            print(f"{Colors.YELLOW}Nenhuma comparação disponível{Colors.RESET}")
            return
        
        for metric_name, comparison in comparisons.items():
            print(f"\n{Colors.BLUE}📊 {metric_name.replace('_', ' ').title()}:{Colors.RESET}")
            
            # Indicador de tendência
            trend_emoji = {
                'up': '📈',
                'down': '📉',
                'stable': '➡️'
            }.get(comparison.trend, '📊')
            
            # Indicador de significância
            significance_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(comparison.significance, '⚪')
            
            print(f"  Tendência: {comparison.trend.title()} {trend_emoji}")
            print(f"  Mudança: {comparison.change_percentage:+.1f}% {significance_emoji}")
            
            # Valores
            current_val = comparison.current_period.get('value', 0)
            previous_val = comparison.previous_period.get('value', 0)
            
            if metric_name == 'avg_salary':
                print(f"  Atual: R$ {current_val:,.2f}")
                print(f"  Anterior: R$ {previous_val:,.2f}")
            elif 'percentage' in metric_name:
                print(f"  Atual: {current_val:.1f}%")
                print(f"  Anterior: {previous_val:.1f}%")
            else:
                print(f"  Atual: {current_val:,.0f}")
                print(f"  Anterior: {previous_val:,.0f}")
        
        print("\n" + "=" * 60)


# Instância global do comparador histórico
historical_comparator = HistoricalDataComparator()