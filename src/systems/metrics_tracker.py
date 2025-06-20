"""
Sistema de Tracking Detalhado de Métricas

Este módulo implementa coleta, análise e exportação de métricas
avançadas para monitoramento em produção.

Funcionalidades:
- Coleta de métricas em tempo real
- Agregação e análise estatística
- Dashboard de métricas
- Alertas baseados em thresholds
- Exportação para sistemas externos
- Histórico de performance
"""

import asyncio
import json
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import threading
import csv

try:
    from .structured_logger import structured_logger, Component, LogLevel
except ImportError:
    structured_logger = None
    Component = None
    LogLevel = None


class MetricType(Enum):
    """Tipos de métricas"""
    COUNTER = "counter"          # Valores que sempre aumentam
    GAUGE = "gauge"              # Valores que podem subir/descer
    HISTOGRAM = "histogram"      # Distribuição de valores
    TIMER = "timer"              # Tempos de execução
    RATE = "rate"                # Taxa por segundo


class AlertSeverity(Enum):
    """Severidade dos alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    """Valor de uma métrica com timestamp"""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Resumo estatístico de uma métrica"""
    name: str
    metric_type: MetricType
    count: int
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    std_dev: float
    percentile_95: float
    percentile_99: float
    rate_per_second: float
    last_value: float
    last_update: float


@dataclass
class AlertRule:
    """Regra de alerta para métricas"""
    name: str
    metric_name: str
    condition: str              # "gt", "lt", "eq", "change"
    threshold: float
    severity: AlertSeverity
    duration: float = 0.0       # Duração mínima da condição
    callback: Optional[Callable] = None
    enabled: bool = True
    last_triggered: float = 0.0
    cooldown: float = 300.0     # 5 minutos entre alertas


@dataclass
class Alert:
    """Alerta gerado"""
    rule_name: str
    metric_name: str
    message: str
    severity: AlertSeverity
    value: float
    threshold: float
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None


class MetricCollector:
    """Coletor de métricas individuais"""
    
    def __init__(self, name: str, metric_type: MetricType, max_history: int = 1000):
        self.name = name
        self.metric_type = metric_type
        self.max_history = max_history
        self.values: deque = deque(maxlen=max_history)
        self.labels_index: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._lock = threading.Lock()
    
    def record(self, value: float, labels: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Registra um valor da métrica"""
        with self._lock:
            metric_value = MetricValue(
                value=value,
                timestamp=time.time(),
                labels=labels or {},
                metadata=metadata or {}
            )
            
            self.values.append(metric_value)
            
            # Indexar por labels para agregações
            if labels:
                for key, label_value in labels.items():
                    self.labels_index[f"{key}={label_value}"].append(metric_value)
    
    def get_values(self, since: Optional[float] = None) -> List[MetricValue]:
        """Obtém valores desde um timestamp"""
        with self._lock:
            if since is None:
                return list(self.values)
            
            return [v for v in self.values if v.timestamp >= since]
    
    def get_summary(self, since: Optional[float] = None) -> MetricSummary:
        """Calcula resumo estatístico"""
        values = self.get_values(since)
        
        if not values:
            return MetricSummary(
                name=self.name,
                metric_type=self.metric_type,
                count=0,
                min_value=0.0,
                max_value=0.0,
                avg_value=0.0,
                median_value=0.0,
                std_dev=0.0,
                percentile_95=0.0,
                percentile_99=0.0,
                rate_per_second=0.0,
                last_value=0.0,
                last_update=0.0
            )
        
        numeric_values = [v.value for v in values]
        time_span = values[-1].timestamp - values[0].timestamp if len(values) > 1 else 1.0
        
        return MetricSummary(
            name=self.name,
            metric_type=self.metric_type,
            count=len(values),
            min_value=min(numeric_values),
            max_value=max(numeric_values),
            avg_value=statistics.mean(numeric_values),
            median_value=statistics.median(numeric_values),
            std_dev=statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0.0,
            percentile_95=self._percentile(numeric_values, 0.95),
            percentile_99=self._percentile(numeric_values, 0.99),
            rate_per_second=len(values) / time_span if time_span > 0 else 0.0,
            last_value=values[-1].value,
            last_update=values[-1].timestamp
        )
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calcula percentil"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


class MetricsTracker:
    """Sistema principal de tracking de métricas"""
    
    def __init__(self, export_dir: str = "data/metrics"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        self.collectors: Dict[str, MetricCollector] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # Configurações
        self.alert_check_interval = 10.0  # segundos
        self.export_interval = 60.0       # segundos
        self.max_alert_history = 1000
        
        # Métricas internas do sistema
        self._init_system_metrics()
        
        # Background tasks
        self._running = False
        self._background_tasks = []
        
        # Cache de agregações
        self._aggregation_cache = {}
        self._cache_ttl = 30.0  # 30 segundos
    
    def _init_system_metrics(self):
        """Inicializa métricas do sistema"""
        system_metrics = [
            ("scraper.pages_processed", MetricType.COUNTER),
            ("scraper.jobs_found", MetricType.COUNTER),
            ("scraper.jobs_processed", MetricType.COUNTER),
            ("scraper.processing_time", MetricType.TIMER),
            ("scraper.success_rate", MetricType.GAUGE),
            ("scraper.error_rate", MetricType.GAUGE),
            
            ("retry.total_operations", MetricType.COUNTER),
            ("retry.failed_operations", MetricType.COUNTER),
            ("retry.retry_count", MetricType.COUNTER),
            ("retry.success_after_retry", MetricType.COUNTER),
            
            ("circuit_breaker.opens", MetricType.COUNTER),
            ("circuit_breaker.closes", MetricType.COUNTER),
            ("circuit_breaker.rejections", MetricType.COUNTER),
            ("circuit_breaker.current_state", MetricType.GAUGE),
            
            ("validation.jobs_validated", MetricType.COUNTER),
            ("validation.quality_score", MetricType.GAUGE),
            ("validation.corrections_applied", MetricType.COUNTER),
            ("validation.anomalies_detected", MetricType.COUNTER),
            
            ("cache.hits", MetricType.COUNTER),
            ("cache.misses", MetricType.COUNTER),
            ("cache.hit_rate", MetricType.GAUGE),
            
            ("fallback.selector_attempts", MetricType.COUNTER),
            ("fallback.selector_successes", MetricType.COUNTER),
            ("fallback.fallback_level", MetricType.HISTOGRAM),
            
            ("system.memory_usage", MetricType.GAUGE),
            ("system.cpu_usage", MetricType.GAUGE),
            ("system.response_time", MetricType.TIMER)
        ]
        
        for name, metric_type in system_metrics:
            self.register_metric(name, metric_type)
    
    def register_metric(self, name: str, metric_type: MetricType, max_history: int = 1000) -> MetricCollector:
        """Registra uma nova métrica"""
        if name in self.collectors:
            return self.collectors[name]
        
        collector = MetricCollector(name, metric_type, max_history)
        self.collectors[name] = collector
        
        if structured_logger:
            structured_logger.info(
                f"Metric registered: {name}",
                component=Component.SYSTEM,
                context={'metric_type': metric_type.value, 'max_history': max_history}
            )
        
        return collector
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Registra um valor de métrica"""
        if name not in self.collectors:
            # Auto-registrar como gauge
            self.register_metric(name, MetricType.GAUGE)
        
        self.collectors[name].record(value, labels, metadata)
        
        # Verificar alertas se necessário
        if name in self.alert_rules:
            self._check_alert(name, value)
    
    def increment_counter(self, name: str, amount: float = 1.0, labels: Dict[str, str] = None):
        """Incrementa um contador"""
        if name not in self.collectors:
            self.register_metric(name, MetricType.COUNTER)
        
        # Para contadores, acumular valor
        last_value = 0.0
        if self.collectors[name].values:
            last_value = self.collectors[name].values[-1].value
        
        self.record_metric(name, last_value + amount, labels)
    
    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None):
        """Registra tempo de execução"""
        if name not in self.collectors:
            self.register_metric(name, MetricType.TIMER)
        
        self.record_metric(name, duration, labels, {'unit': 'seconds'})
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Define valor de gauge"""
        if name not in self.collectors:
            self.register_metric(name, MetricType.GAUGE)
        
        self.record_metric(name, value, labels)
    
    def add_alert_rule(self, rule: AlertRule):
        """Adiciona regra de alerta"""
        self.alert_rules[rule.name] = rule
        
        if structured_logger:
            structured_logger.info(
                f"Alert rule added: {rule.name}",
                component=Component.SYSTEM,
                context={
                    'metric': rule.metric_name,
                    'condition': rule.condition,
                    'threshold': rule.threshold,
                    'severity': rule.severity.value
                }
            )
    
    def _check_alert(self, metric_name: str, current_value: float):
        """Verifica se deve disparar alerta"""
        for rule in self.alert_rules.values():
            if rule.metric_name != metric_name or not rule.enabled:
                continue
            
            # Verificar cooldown
            if time.time() - rule.last_triggered < rule.cooldown:
                continue
            
            # Avaliar condição
            triggered = False
            
            if rule.condition == "gt" and current_value > rule.threshold:
                triggered = True
            elif rule.condition == "lt" and current_value < rule.threshold:
                triggered = True
            elif rule.condition == "eq" and abs(current_value - rule.threshold) < 0.001:
                triggered = True
            
            if triggered:
                self._trigger_alert(rule, current_value)
    
    def _trigger_alert(self, rule: AlertRule, value: float):
        """Dispara um alerta"""
        alert = Alert(
            rule_name=rule.name,
            metric_name=rule.metric_name,
            message=f"Metric {rule.metric_name} is {value} (threshold: {rule.threshold})",
            severity=rule.severity,
            value=value,
            threshold=rule.threshold,
            timestamp=time.time()
        )
        
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        # Limitar histórico
        if len(self.alert_history) > self.max_alert_history:
            self.alert_history = self.alert_history[-self.max_alert_history:]
        
        rule.last_triggered = time.time()
        
        # Executar callback se definido
        if rule.callback:
            try:
                rule.callback(alert)
            except Exception as e:
                if structured_logger:
                    structured_logger.error(
                        f"Alert callback failed: {e}",
                        component=Component.SYSTEM,
                        error=str(e)
                    )
        
        # Log do alerta
        if structured_logger:
            log_level = {
                AlertSeverity.LOW: LogLevel.INFO,
                AlertSeverity.MEDIUM: LogLevel.WARN,
                AlertSeverity.HIGH: LogLevel.ERROR,
                AlertSeverity.CRITICAL: LogLevel.ERROR
            }.get(rule.severity, LogLevel.WARN)
            
            structured_logger.log(
                f"ALERT {rule.severity.value.upper()}: {alert.message}",
                log_level,
                component=Component.SYSTEM,
                context={
                    'alert_rule': rule.name,
                    'metric': rule.metric_name,
                    'value': value,
                    'threshold': rule.threshold
                }
            )
        
        print(f"🚨 ALERTA {rule.severity.value.upper()}: {alert.message}")
    
    def get_metric_summary(self, name: str, since: Optional[float] = None) -> Optional[MetricSummary]:
        """Obtém resumo de uma métrica"""
        if name not in self.collectors:
            return None
        
        return self.collectors[name].get_summary(since)
    
    def get_all_summaries(self, since: Optional[float] = None) -> Dict[str, MetricSummary]:
        """Obtém resumos de todas as métricas"""
        summaries = {}
        for name, collector in self.collectors.items():
            summaries[name] = collector.get_summary(since)
        return summaries
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtém dados para dashboard"""
        current_time = time.time()
        last_hour = current_time - 3600  # 1 hora
        last_5min = current_time - 300   # 5 minutos
        
        # Usar cache se disponível
        cache_key = f"dashboard_{int(current_time / self._cache_ttl)}"
        if cache_key in self._aggregation_cache:
            return self._aggregation_cache[cache_key]
        
        summaries_1h = self.get_all_summaries(last_hour)
        summaries_5m = self.get_all_summaries(last_5min)
        
        # Converter summaries para dict serializável
        def summary_to_dict(summary):
            data = asdict(summary)
            data['metric_type'] = summary.metric_type.value  # Converter enum para string
            return data
        
        # Converter alertas para dict serializável
        def alert_to_dict(alert):
            data = asdict(alert)
            data['severity'] = alert.severity.value  # Converter enum para string
            return data
        
        dashboard_data = {
            'timestamp': current_time,
            'summary_1h': {name: summary_to_dict(summary) for name, summary in summaries_1h.items()},
            'summary_5m': {name: summary_to_dict(summary) for name, summary in summaries_5m.items()},
            'active_alerts': [alert_to_dict(alert) for alert in self.active_alerts],
            'alert_count_by_severity': self._count_alerts_by_severity(),
            'top_metrics': self._get_top_metrics(),
            'system_health': self._calculate_system_health(),
            'trends': self._calculate_trends()
        }
        
        # Cachear resultado
        self._aggregation_cache[cache_key] = dashboard_data
        
        # Limpar cache antigo
        old_keys = [k for k in self._aggregation_cache.keys() if k < cache_key]
        for key in old_keys:
            del self._aggregation_cache[key]
        
        return dashboard_data
    
    def _count_alerts_by_severity(self) -> Dict[str, int]:
        """Conta alertas por severidade"""
        counts = {severity.value: 0 for severity in AlertSeverity}
        for alert in self.active_alerts:
            if not alert.resolved:
                counts[alert.severity.value] += 1
        return counts
    
    def _get_top_metrics(self) -> Dict[str, Any]:
        """Obtém métricas principais"""
        summaries = self.get_all_summaries(time.time() - 3600)  # 1 hora
        
        top_metrics = {
            'highest_values': [],
            'most_active': [],
            'slowest_operations': []
        }
        
        # Valores mais altos
        for name, summary in summaries.items():
            if summary.count > 0:
                top_metrics['highest_values'].append({
                    'name': name,
                    'value': summary.max_value,
                    'avg': summary.avg_value
                })
        
        top_metrics['highest_values'].sort(key=lambda x: x['value'], reverse=True)
        top_metrics['highest_values'] = top_metrics['highest_values'][:5]
        
        # Mais ativas (maior taxa)
        for name, summary in summaries.items():
            if summary.count > 0:
                top_metrics['most_active'].append({
                    'name': name,
                    'rate': summary.rate_per_second,
                    'count': summary.count
                })
        
        top_metrics['most_active'].sort(key=lambda x: x['rate'], reverse=True)
        top_metrics['most_active'] = top_metrics['most_active'][:5]
        
        # Operações mais lentas (timers)
        for name, summary in summaries.items():
            if summary.metric_type == MetricType.TIMER and summary.count > 0:
                top_metrics['slowest_operations'].append({
                    'name': name,
                    'avg_time': summary.avg_value,
                    'max_time': summary.max_value,
                    'p95': summary.percentile_95
                })
        
        top_metrics['slowest_operations'].sort(key=lambda x: x['avg_time'], reverse=True)
        top_metrics['slowest_operations'] = top_metrics['slowest_operations'][:5]
        
        return top_metrics
    
    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calcula saúde geral do sistema"""
        health = {
            'overall_score': 100.0,
            'status': 'healthy',
            'issues': []
        }
        
        # Verificar alertas críticos
        critical_alerts = [a for a in self.active_alerts if a.severity == AlertSeverity.CRITICAL and not a.resolved]
        if critical_alerts:
            health['overall_score'] -= len(critical_alerts) * 30
            health['status'] = 'critical'
            health['issues'].append(f"{len(critical_alerts)} critical alerts")
        
        # Verificar alertas high
        high_alerts = [a for a in self.active_alerts if a.severity == AlertSeverity.HIGH and not a.resolved]
        if high_alerts:
            health['overall_score'] -= len(high_alerts) * 15
            if health['status'] == 'healthy':
                health['status'] = 'degraded'
            health['issues'].append(f"{len(high_alerts)} high severity alerts")
        
        # Verificar taxa de erro
        error_rate_summary = self.get_metric_summary('scraper.error_rate')
        if error_rate_summary and error_rate_summary.last_value > 10.0:  # >10% erro
            health['overall_score'] -= error_rate_summary.last_value
            if health['status'] == 'healthy':
                health['status'] = 'degraded'
            health['issues'].append(f"High error rate: {error_rate_summary.last_value:.1f}%")
        
        # Verificar circuit breakers abertos
        cb_state_summary = self.get_metric_summary('circuit_breaker.current_state')
        if cb_state_summary and cb_state_summary.last_value > 0:  # Estado OPEN = 1
            health['overall_score'] -= 20
            if health['status'] == 'healthy':
                health['status'] = 'degraded'
            health['issues'].append("Circuit breakers open")
        
        health['overall_score'] = max(0.0, health['overall_score'])
        
        return health
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calcula tendências das métricas"""
        current_time = time.time()
        hour_ago = current_time - 3600
        half_hour_ago = current_time - 1800
        
        recent_summaries = self.get_all_summaries(half_hour_ago)
        older_summaries = self.get_all_summaries(hour_ago)
        
        trends = {}
        
        for name in recent_summaries:
            if name in older_summaries:
                recent_avg = recent_summaries[name].avg_value
                older_avg = older_summaries[name].avg_value
                
                if older_avg > 0:
                    change_percent = ((recent_avg - older_avg) / older_avg) * 100
                    
                    trends[name] = {
                        'change_percent': change_percent,
                        'direction': 'up' if change_percent > 5 else 'down' if change_percent < -5 else 'stable',
                        'recent_avg': recent_avg,
                        'older_avg': older_avg
                    }
        
        return trends
    
    def export_metrics(self, format: str = 'json') -> str:
        """Exporta métricas para arquivo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            filename = self.export_dir / f"metrics_{timestamp}.json"
            data = self.get_dashboard_data()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format == 'csv':
            filename = self.export_dir / f"metrics_{timestamp}.csv"
            summaries = self.get_all_summaries()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'metric_name', 'type', 'count', 'min', 'max', 'avg', 
                    'median', 'std_dev', 'p95', 'p99', 'rate_per_sec', 'last_value'
                ])
                
                # Data
                for name, summary in summaries.items():
                    writer.writerow([
                        summary.name, summary.metric_type.value, summary.count,
                        summary.min_value, summary.max_value, summary.avg_value,
                        summary.median_value, summary.std_dev, summary.percentile_95,
                        summary.percentile_99, summary.rate_per_second, summary.last_value
                    ])
        
        if structured_logger:
            structured_logger.info(
                f"Metrics exported to {filename}",
                component=Component.SYSTEM,
                context={'format': format, 'filename': str(filename)}
            )
        
        return str(filename)
    
    def print_dashboard(self):
        """Imprime dashboard no console"""
        dashboard = self.get_dashboard_data()
        
        print("\n" + "="*80)
        print("📊 DASHBOARD DE MÉTRICAS EM TEMPO REAL")
        print("="*80)
        print(f"🕐 Timestamp: {datetime.fromtimestamp(dashboard['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Saúde do sistema
        health = dashboard['system_health']
        status_icons = {
            'healthy': '🟢',
            'degraded': '🟡', 
            'critical': '🔴'
        }
        
        icon = status_icons.get(health['status'], '⚪')
        print(f"\n{icon} SAÚDE DO SISTEMA: {health['status'].upper()} ({health['overall_score']:.1f}/100)")
        
        if health['issues']:
            print("   ⚠️  Problemas detectados:")
            for issue in health['issues']:
                print(f"      • {issue}")
        
        # Alertas ativos
        alert_counts = dashboard['alert_count_by_severity']
        total_alerts = sum(alert_counts.values())
        
        if total_alerts > 0:
            print(f"\n🚨 ALERTAS ATIVOS: {total_alerts}")
            if alert_counts['critical'] > 0:
                print(f"   🔴 Críticos: {alert_counts['critical']}")
            if alert_counts['high'] > 0:
                print(f"   🟠 Altos: {alert_counts['high']}")
            if alert_counts['medium'] > 0:
                print(f"   🟡 Médios: {alert_counts['medium']}")
            if alert_counts['low'] > 0:
                print(f"   🔵 Baixos: {alert_counts['low']}")
        else:
            print(f"\n✅ ALERTAS: Nenhum alerta ativo")
        
        # Top métricas
        top_metrics = dashboard['top_metrics']
        
        if top_metrics['most_active']:
            print(f"\n📈 MÉTRICAS MAIS ATIVAS (última hora):")
            for metric in top_metrics['most_active']:
                print(f"   • {metric['name']}: {metric['rate']:.2f}/s ({metric['count']} eventos)")
        
        if top_metrics['slowest_operations']:
            print(f"\n⏱️  OPERAÇÕES MAIS LENTAS:")
            for metric in top_metrics['slowest_operations']:
                print(f"   • {metric['name']}: {metric['avg_time']:.3f}s avg (P95: {metric['p95']:.3f}s)")
        
        # Métricas chave (últimos 5 minutos)
        summaries_5m = dashboard['summary_5m']
        
        print(f"\n🔍 MÉTRICAS PRINCIPAIS (últimos 5 min):")
        
        key_metrics = [
            'scraper.jobs_processed',
            'scraper.success_rate', 
            'scraper.error_rate',
            'retry.total_operations',
            'validation.quality_score',
            'cache.hit_rate'
        ]
        
        for metric_name in key_metrics:
            if metric_name in summaries_5m:
                summary = summaries_5m[metric_name]
                if summary['count'] > 0:
                    if 'rate' in metric_name or 'score' in metric_name:
                        print(f"   • {metric_name}: {summary['last_value']:.1f}%")
                    elif 'time' in metric_name:
                        print(f"   • {metric_name}: {summary['avg_value']:.3f}s")
                    else:
                        print(f"   • {metric_name}: {summary['count']} ({summary['rate_per_second']:.2f}/s)")
        
        # Tendências
        trends = dashboard['trends']
        trending_up = [name for name, data in trends.items() if data['direction'] == 'up']
        trending_down = [name for name, data in trends.items() if data['direction'] == 'down']
        
        if trending_up or trending_down:
            print(f"\n📊 TENDÊNCIAS (última hora vs. anterior):")
            if trending_up:
                print(f"   📈 Subindo: {', '.join(trending_up[:3])}")
            if trending_down:
                print(f"   📉 Descendo: {', '.join(trending_down[:3])}")
        
        print("="*80)
    
    def start_background_monitoring(self):
        """Inicia monitoramento em background"""
        if self._running:
            return
        
        self._running = True
        
        # Task de verificação de alertas
        async def alert_checker():
            while self._running:
                try:
                    # Verificar alertas que podem ter sido resolvidos
                    current_time = time.time()
                    for alert in self.active_alerts[:]:  # Copy list
                        if not alert.resolved:
                            # Verificar se condição ainda existe
                            metric_summary = self.get_metric_summary(alert.metric_name)
                            if metric_summary and metric_summary.last_value != alert.value:
                                # Condição mudou, marcar como resolvido
                                alert.resolved = True
                                alert.resolved_at = current_time
                                self.active_alerts.remove(alert)
                    
                    await asyncio.sleep(self.alert_check_interval)
                except Exception as e:
                    if structured_logger:
                        structured_logger.error(f"Alert checker error: {e}", component=Component.SYSTEM)
                    await asyncio.sleep(self.alert_check_interval)
        
        # Task de exportação automática
        async def auto_exporter():
            while self._running:
                try:
                    await asyncio.sleep(self.export_interval)
                    if self._running:  # Check again after sleep
                        self.export_metrics('json')
                except Exception as e:
                    if structured_logger:
                        structured_logger.error(f"Auto export error: {e}", component=Component.SYSTEM)
        
        # Iniciar tasks
        self._background_tasks = [
            asyncio.create_task(alert_checker()),
            asyncio.create_task(auto_exporter())
        ]
    
    def stop_background_monitoring(self):
        """Para monitoramento em background"""
        self._running = False
        
        for task in self._background_tasks:
            task.cancel()
        
        self._background_tasks.clear()


# Instância global
metrics_tracker = MetricsTracker()


# Context manager para timing automático
class TimerContext:
    """Context manager para medir tempo automaticamente"""
    
    def __init__(self, metric_name: str, labels: Dict[str, str] = None):
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            metrics_tracker.record_timer(self.metric_name, duration, self.labels)


# Decorador para timing automático
def track_timing(metric_name: str = None, labels: Dict[str, str] = None):
    """Decorador para tracking automático de tempo"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = metric_name or f"function.{func.__name__}.duration"
            
            with TimerContext(name, labels):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Configuração de alertas padrão
def setup_default_alerts():
    """Configura alertas padrão do sistema"""
    default_rules = [
        AlertRule(
            name="high_error_rate",
            metric_name="scraper.error_rate",
            condition="gt",
            threshold=15.0,  # > 15% erro
            severity=AlertSeverity.HIGH,
            duration=60.0
        ),
        AlertRule(
            name="low_success_rate", 
            metric_name="scraper.success_rate",
            condition="lt",
            threshold=80.0,  # < 80% sucesso
            severity=AlertSeverity.MEDIUM,
            duration=120.0
        ),
        AlertRule(
            name="circuit_breaker_open",
            metric_name="circuit_breaker.current_state",
            condition="gt",
            threshold=0.5,  # Estado OPEN
            severity=AlertSeverity.HIGH,
            duration=30.0
        ),
        AlertRule(
            name="low_data_quality",
            metric_name="validation.quality_score",
            condition="lt", 
            threshold=70.0,  # < 70% qualidade
            severity=AlertSeverity.MEDIUM,
            duration=300.0
        ),
        AlertRule(
            name="high_response_time",
            metric_name="system.response_time",
            condition="gt",
            threshold=5.0,  # > 5 segundos
            severity=AlertSeverity.MEDIUM,
            duration=60.0
        )
    ]
    
    for rule in default_rules:
        metrics_tracker.add_alert_rule(rule)
    
    if structured_logger:
        structured_logger.info(
            f"Default alert rules configured: {len(default_rules)}",
            component=Component.SYSTEM
        )