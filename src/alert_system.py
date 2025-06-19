"""
Sistema de Alertas Automáticos

Este módulo implementa um sistema completo de alertas para
monitoramento proativo e notificações automáticas de problemas.

Funcionalidades:
- Múltiplos canais de notificação (email, webhook, Slack, etc.)
- Alertas escalonados por severidade
- Agrupamento de alertas similares
- Throttling e cooldown para evitar spam
- Templates customizáveis
- Dashboard de status de alertas
- Integração com métricas e logs
"""

import asyncio
import json
import time
import smtplib
import requests
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import hashlib

try:
    from .structured_logger import structured_logger, Component, LogLevel
    from .metrics_tracker import metrics_tracker, Alert, AlertSeverity
except ImportError:
    structured_logger = None
    Component = None
    LogLevel = None
    metrics_tracker = None
    Alert = None
    AlertSeverity = None


class NotificationChannel(Enum):
    """Canais de notificação disponíveis"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    CONSOLE = "console"
    FILE = "file"


class AlertStatus(Enum):
    """Status de um alerta"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class NotificationConfig:
    """Configuração de um canal de notificação"""
    channel: NotificationChannel
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    min_severity: AlertSeverity = AlertSeverity.LOW
    max_alerts_per_hour: int = 60
    template: Optional[str] = None


@dataclass
class AlertRule:
    """Regra de alerta melhorada"""
    name: str
    description: str
    condition: str
    threshold: float
    severity: AlertSeverity
    channels: List[NotificationChannel] = field(default_factory=list)
    enabled: bool = True
    cooldown_minutes: int = 15
    escalation_after_minutes: int = 60
    escalation_severity: Optional[AlertSeverity] = None
    suppression_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertInstance:
    """Instância de um alerta ativo"""
    id: str
    rule_name: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    created_at: float
    last_triggered: float
    trigger_count: int = 1
    acknowledged_at: Optional[float] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[float] = None
    escalated: bool = False
    context: Dict[str, Any] = field(default_factory=dict)
    notifications_sent: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NotificationTemplate:
    """Template para formatação de notificações"""
    title: str
    body: str
    variables: Dict[str, str] = field(default_factory=dict)


class NotificationSender:
    """Classe base para envio de notificações"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.send_count = defaultdict(int)
        self.last_reset = time.time()
    
    async def send(self, alert: AlertInstance, template: NotificationTemplate) -> bool:
        """Envia notificação"""
        # Verificar rate limiting
        if not self._check_rate_limit():
            if structured_logger:
                structured_logger.warn(
                    f"Rate limit exceeded for {self.config.channel.value}",
                    component=Component.SYSTEM
                )
            return False
        
        try:
            success = await self._send_notification(alert, template)
            if success:
                self.send_count[self.config.channel.value] += 1
            return success
        except Exception as e:
            if structured_logger:
                structured_logger.error(
                    f"Failed to send notification via {self.config.channel.value}: {e}",
                    component=Component.SYSTEM,
                    error=str(e)
                )
            return False
    
    def _check_rate_limit(self) -> bool:
        """Verifica se não excedeu rate limit"""
        current_time = time.time()
        
        # Reset contador a cada hora
        if current_time - self.last_reset > 3600:
            self.send_count.clear()
            self.last_reset = current_time
        
        return self.send_count[self.config.channel.value] < self.config.max_alerts_per_hour
    
    async def _send_notification(self, alert: AlertInstance, template: NotificationTemplate) -> bool:
        """Implementação específica do envio (override em subclasses)"""
        raise NotImplementedError


class EmailSender(NotificationSender):
    """Envio de notificações por email"""
    
    async def _send_notification(self, alert: AlertInstance, template: NotificationTemplate) -> bool:
        config = self.config.config
        
        if not all(k in config for k in ['smtp_server', 'smtp_port', 'username', 'password', 'to_emails']):
            return False
        
        try:
            # Formatear template
            formatted_title = self._format_template(template.title, alert)
            formatted_body = self._format_template(template.body, alert)
            
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = config['username']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = formatted_title
            
            # Adicionar corpo do email
            msg.attach(MIMEText(formatted_body, 'html' if '<' in formatted_body else 'plain'))
            
            # Enviar email
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                server.login(config['username'], config['password'])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            if structured_logger:
                structured_logger.error(f"Email send failed: {e}", component=Component.SYSTEM)
            return False
    
    def _format_template(self, template: str, alert: AlertInstance) -> str:
        """Formatar template com dados do alerta"""
        variables = {
            'alert_id': alert.id,
            'title': alert.title,
            'description': alert.description,
            'severity': alert.severity.value.upper(),
            'status': alert.status.value.upper(),
            'created_at': datetime.fromtimestamp(alert.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'trigger_count': str(alert.trigger_count),
            'context': json.dumps(alert.context, indent=2)
        }
        
        # Substituir variáveis no template
        for key, value in variables.items():
            template = template.replace(f'{{{key}}}', str(value))
        
        return template


class WebhookSender(NotificationSender):
    """Envio de notificações via webhook"""
    
    async def _send_notification(self, alert: AlertInstance, template: NotificationTemplate) -> bool:
        config = self.config.config
        
        if 'url' not in config:
            return False
        
        try:
            # Preparar payload
            payload = {
                'alert_id': alert.id,
                'title': self._format_template(template.title, alert),
                'description': self._format_template(template.body, alert),
                'severity': alert.severity.value,
                'status': alert.status.value,
                'created_at': alert.created_at,
                'trigger_count': alert.trigger_count,
                'context': alert.context
            }
            
            # Adicionar headers customizados
            headers = {'Content-Type': 'application/json'}
            if 'headers' in config:
                headers.update(config['headers'])
            
            # Enviar webhook
            response = requests.post(
                config['url'],
                json=payload,
                headers=headers,
                timeout=config.get('timeout', 10)
            )
            
            return response.status_code < 400
            
        except Exception as e:
            if structured_logger:
                structured_logger.error(f"Webhook send failed: {e}", component=Component.SYSTEM)
            return False
    
    def _format_template(self, template: str, alert: AlertInstance) -> str:
        """Mesmo método de formatação do EmailSender"""
        variables = {
            'alert_id': alert.id,
            'title': alert.title,
            'description': alert.description,
            'severity': alert.severity.value.upper(),
            'status': alert.status.value.upper(),
            'created_at': datetime.fromtimestamp(alert.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'trigger_count': str(alert.trigger_count)
        }
        
        for key, value in variables.items():
            template = template.replace(f'{{{key}}}', str(value))
        
        return template


class SlackSender(NotificationSender):
    """Envio de notificações para Slack"""
    
    async def _send_notification(self, alert: AlertInstance, template: NotificationTemplate) -> bool:
        config = self.config.config
        
        if 'webhook_url' not in config:
            return False
        
        try:
            # Mapear severidade para cor
            color_map = {
                AlertSeverity.LOW: '#36a64f',        # Verde
                AlertSeverity.MEDIUM: '#ff9900',     # Laranja
                AlertSeverity.HIGH: '#ff0000',       # Vermelho
                AlertSeverity.CRITICAL: '#8b0000'    # Vermelho escuro
            }
            
            # Criar attachment do Slack
            attachment = {
                'color': color_map.get(alert.severity, '#36a64f'),
                'title': self._format_template(template.title, alert),
                'text': self._format_template(template.body, alert),
                'fields': [
                    {
                        'title': 'Severidade',
                        'value': alert.severity.value.upper(),
                        'short': True
                    },
                    {
                        'title': 'Status',
                        'value': alert.status.value.upper(),
                        'short': True
                    },
                    {
                        'title': 'Ocorrências',
                        'value': str(alert.trigger_count),
                        'short': True
                    },
                    {
                        'title': 'Criado em',
                        'value': datetime.fromtimestamp(alert.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                        'short': True
                    }
                ],
                'footer': 'Sistema de Alertas Web Scraper',
                'ts': int(alert.created_at)
            }
            
            payload = {
                'attachments': [attachment]
            }
            
            # Enviar para Slack
            response = requests.post(
                config['webhook_url'],
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            if structured_logger:
                structured_logger.error(f"Slack send failed: {e}", component=Component.SYSTEM)
            return False
    
    def _format_template(self, template: str, alert: AlertInstance) -> str:
        """Formatação específica para Slack com markdown"""
        variables = {
            'alert_id': alert.id,
            'title': alert.title,
            'description': alert.description,
            'severity': f"*{alert.severity.value.upper()}*",
            'status': f"*{alert.status.value.upper()}*",
            'created_at': datetime.fromtimestamp(alert.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'trigger_count': str(alert.trigger_count)
        }
        
        for key, value in variables.items():
            template = template.replace(f'{{{key}}}', str(value))
        
        return template


class ConsoleSender(NotificationSender):
    """Envio de notificações para console"""
    
    async def _send_notification(self, alert: AlertInstance, template: NotificationTemplate) -> bool:
        try:
            # Mapear severidade para ícones
            severity_icons = {
                AlertSeverity.LOW: '🔵',
                AlertSeverity.MEDIUM: '🟡',
                AlertSeverity.HIGH: '🔴',
                AlertSeverity.CRITICAL: '💀'
            }
            
            icon = severity_icons.get(alert.severity, '⚪')
            
            print(f"\n{icon} ALERTA {alert.severity.value.upper()}")
            print("=" * 60)
            print(f"ID: {alert.id}")
            print(f"Título: {alert.title}")
            print(f"Descrição: {alert.description}")
            print(f"Status: {alert.status.value.upper()}")
            print(f"Criado em: {datetime.fromtimestamp(alert.created_at).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Ocorrências: {alert.trigger_count}")
            
            if alert.context:
                print(f"Contexto: {json.dumps(alert.context, indent=2)}")
            
            print("=" * 60)
            
            return True
            
        except Exception as e:
            if structured_logger:
                structured_logger.error(f"Console send failed: {e}", component=Component.SYSTEM)
            return False


class FileSender(NotificationSender):
    """Envio de notificações para arquivo"""
    
    async def _send_notification(self, alert: AlertInstance, template: NotificationTemplate) -> bool:
        try:
            config = self.config.config
            file_path = Path(config.get('file_path', 'data/alerts/alerts.log'))
            
            # Criar diretório se não existir
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Preparar entrada do log
            log_entry = {
                'timestamp': datetime.fromtimestamp(alert.created_at).isoformat(),
                'alert_id': alert.id,
                'title': alert.title,
                'description': alert.description,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'trigger_count': alert.trigger_count,
                'context': alert.context
            }
            
            # Escrever no arquivo
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            return True
            
        except Exception as e:
            if structured_logger:
                structured_logger.error(f"File send failed: {e}", component=Component.SYSTEM)
            return False


class AlertSystem:
    """Sistema principal de alertas"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Estado do sistema
        self.active_alerts: Dict[str, AlertInstance] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_configs: Dict[NotificationChannel, NotificationConfig] = {}
        self.notification_senders: Dict[NotificationChannel, NotificationSender] = {}
        self.templates: Dict[str, NotificationTemplate] = {}
        
        # Histórico e estatísticas
        self.alert_history: deque = deque(maxlen=10000)
        self.notification_stats = defaultdict(int)
        
        # Background tasks
        self._running = False
        self._background_tasks = []
        
        # Lock para thread safety
        self._lock = threading.Lock()
        
        # Inicializar configurações padrão
        self._load_default_configs()
        self._load_default_templates()
    
    def _load_default_configs(self):
        """Carrega configurações padrão"""
        # Console (sempre habilitado para debug)
        self.notification_configs[NotificationChannel.CONSOLE] = NotificationConfig(
            channel=NotificationChannel.CONSOLE,
            enabled=True,
            min_severity=AlertSeverity.MEDIUM
        )
        
        # Arquivo de log (sempre habilitado)
        self.notification_configs[NotificationChannel.FILE] = NotificationConfig(
            channel=NotificationChannel.FILE,
            enabled=True,
            min_severity=AlertSeverity.LOW,
            config={'file_path': 'data/alerts/alerts.log'}
        )
        
        # Inicializar senders
        self._init_senders()
    
    def _init_senders(self):
        """Inicializa senders de notificação"""
        sender_classes = {
            NotificationChannel.EMAIL: EmailSender,
            NotificationChannel.WEBHOOK: WebhookSender,
            NotificationChannel.SLACK: SlackSender,
            NotificationChannel.CONSOLE: ConsoleSender,
            NotificationChannel.FILE: FileSender
        }
        
        for channel, config in self.notification_configs.items():
            if channel in sender_classes:
                self.notification_senders[channel] = sender_classes[channel](config)
    
    def _load_default_templates(self):
        """Carrega templates padrão"""
        self.templates['default'] = NotificationTemplate(
            title="🚨 Alerta: {title}",
            body="""
Alerta ID: {alert_id}
Severidade: {severity}
Status: {status}
Descrição: {description}
Criado em: {created_at}
Ocorrências: {trigger_count}

Contexto:
{context}
            """.strip()
        )
        
        self.templates['critical'] = NotificationTemplate(
            title="💀 ALERTA CRÍTICO: {title}",
            body="""
🚨 ATENÇÃO: ALERTA CRÍTICO DETECTADO 🚨

ID do Alerta: {alert_id}
Severidade: {severity}
Descrição: {description}
Ocorrências: {trigger_count}
Primeira ocorrência: {created_at}

Este alerta requer ação imediata!

Contexto detalhado:
{context}
            """.strip()
        )
        
        self.templates['slack'] = NotificationTemplate(
            title="🚨 {title}",
            body="{description}\n\n*Severidade:* {severity}\n*Ocorrências:* {trigger_count}"
        )
    
    def add_notification_config(self, config: NotificationConfig):
        """Adiciona configuração de notificação"""
        self.notification_configs[config.channel] = config
        self._init_senders()
        
        if structured_logger:
            structured_logger.info(
                f"Notification channel configured: {config.channel.value}",
                component=Component.SYSTEM,
                context={'enabled': config.enabled, 'min_severity': config.min_severity.value}
            )
    
    def add_alert_rule(self, rule: AlertRule):
        """Adiciona regra de alerta"""
        with self._lock:
            self.alert_rules[rule.name] = rule
        
        if structured_logger:
            structured_logger.info(
                f"Alert rule added: {rule.name}",
                component=Component.SYSTEM,
                context={
                    'severity': rule.severity.value,
                    'channels': [c.value for c in rule.channels],
                    'cooldown_minutes': rule.cooldown_minutes
                }
            )
    
    async def trigger_alert(
        self,
        rule_name: str,
        title: str,
        description: str,
        context: Dict[str, Any] = None,
        force: bool = False
    ) -> Optional[str]:
        """Dispara um alerta"""
        if rule_name not in self.alert_rules:
            if structured_logger:
                structured_logger.error(f"Unknown alert rule: {rule_name}", component=Component.SYSTEM)
            return None
        
        rule = self.alert_rules[rule_name]
        
        if not rule.enabled and not force:
            return None
        
        # Gerar ID único para o alerta
        alert_id = self._generate_alert_id(rule_name, title, description)
        
        with self._lock:
            # Verificar se alerta já existe
            if alert_id in self.active_alerts:
                # Atualizar alerta existente
                existing_alert = self.active_alerts[alert_id]
                existing_alert.last_triggered = time.time()
                existing_alert.trigger_count += 1
                
                # Verificar cooldown
                time_since_last = time.time() - existing_alert.last_triggered
                if time_since_last < (rule.cooldown_minutes * 60) and not force:
                    return alert_id  # Ainda em cooldown
                
                alert = existing_alert
            else:
                # Criar novo alerta
                alert = AlertInstance(
                    id=alert_id,
                    rule_name=rule_name,
                    title=title,
                    description=description,
                    severity=rule.severity,
                    status=AlertStatus.ACTIVE,
                    created_at=time.time(),
                    last_triggered=time.time(),
                    context=context or {}
                )
                
                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)
            
            # Verificar escalação
            if not alert.escalated and rule.escalation_after_minutes:
                time_since_created = (time.time() - alert.created_at) / 60
                if time_since_created >= rule.escalation_after_minutes:
                    if rule.escalation_severity:
                        alert.severity = rule.escalation_severity
                    alert.escalated = True
        
        # Enviar notificações
        await self._send_notifications(alert, rule)
        
        # Registrar métricas
        if metrics_tracker:
            metrics_tracker.increment_counter("alerts.triggered")
            metrics_tracker.increment_counter(f"alerts.{rule.severity.value}")
        
        return alert_id
    
    def _generate_alert_id(self, rule_name: str, title: str, description: str) -> str:
        """Gera ID único para o alerta"""
        content = f"{rule_name}:{title}:{description}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def _send_notifications(self, alert: AlertInstance, rule: AlertRule):
        """Envia notificações para todos os canais configurados"""
        channels_to_use = rule.channels if rule.channels else list(self.notification_configs.keys())
        
        for channel in channels_to_use:
            if channel not in self.notification_configs:
                continue
            
            config = self.notification_configs[channel]
            
            # Verificar se canal está habilitado
            if not config.enabled:
                continue
            
            # Verificar severidade mínima
            severity_levels = {
                AlertSeverity.LOW: 1,
                AlertSeverity.MEDIUM: 2,
                AlertSeverity.HIGH: 3,
                AlertSeverity.CRITICAL: 4
            }
            
            if severity_levels.get(alert.severity, 1) < severity_levels.get(config.min_severity, 1):
                continue
            
            # Selecionar template
            template_name = config.template or self._select_template(alert, channel)
            template = self.templates.get(template_name, self.templates['default'])
            
            # Enviar notificação
            if channel in self.notification_senders:
                try:
                    success = await self.notification_senders[channel].send(alert, template)
                    
                    # Registrar resultado
                    notification_record = {
                        'channel': channel.value,
                        'timestamp': time.time(),
                        'success': success,
                        'template': template_name
                    }
                    
                    alert.notifications_sent.append(notification_record)
                    self.notification_stats[f"{channel.value}_{'success' if success else 'failed'}"] += 1
                    
                    if structured_logger:
                        level = LogLevel.INFO if success else LogLevel.ERROR
                        structured_logger.log(
                            f"Notification sent via {channel.value}: {'success' if success else 'failed'}",
                            level,
                            component=Component.SYSTEM,
                            context={
                                'alert_id': alert.id,
                                'channel': channel.value,
                                'success': success
                            }
                        )
                
                except Exception as e:
                    if structured_logger:
                        structured_logger.error(
                            f"Failed to send notification via {channel.value}: {e}",
                            component=Component.SYSTEM,
                            error=str(e)
                        )
    
    def _select_template(self, alert: AlertInstance, channel: NotificationChannel) -> str:
        """Seleciona template apropriado"""
        if alert.severity == AlertSeverity.CRITICAL:
            return 'critical'
        elif channel == NotificationChannel.SLACK:
            return 'slack'
        else:
            return 'default'
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Reconhece um alerta"""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = time.time()
                alert.acknowledged_by = acknowledged_by
                
                if structured_logger:
                    structured_logger.info(
                        f"Alert acknowledged: {alert_id}",
                        component=Component.SYSTEM,
                        context={'acknowledged_by': acknowledged_by}
                    )
                
                return True
        
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve um alerta"""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = time.time()
                
                # Remover dos alertas ativos
                del self.active_alerts[alert_id]
                
                if structured_logger:
                    structured_logger.info(
                        f"Alert resolved: {alert_id}",
                        component=Component.SYSTEM
                    )
                
                # Registrar métrica
                if metrics_tracker:
                    metrics_tracker.increment_counter("alerts.resolved")
                
                return True
        
        return False
    
    def get_active_alerts(self) -> List[AlertInstance]:
        """Retorna alertas ativos"""
        with self._lock:
            return list(self.active_alerts.values())
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de alertas"""
        with self._lock:
            active_by_severity = defaultdict(int)
            for alert in self.active_alerts.values():
                active_by_severity[alert.severity.value] += 1
            
            return {
                'active_alerts': len(self.active_alerts),
                'total_in_history': len(self.alert_history),
                'active_by_severity': dict(active_by_severity),
                'notification_stats': dict(self.notification_stats),
                'configured_channels': [c.value for c in self.notification_configs.keys()],
                'configured_rules': len(self.alert_rules)
            }
    
    def print_alert_dashboard(self):
        """Imprime dashboard de alertas"""
        stats = self.get_alert_stats()
        active_alerts = self.get_active_alerts()
        
        print("\n" + "="*80)
        print("🚨 DASHBOARD DE ALERTAS")
        print("="*80)
        
        # Estatísticas gerais
        print(f"📊 ESTATÍSTICAS GERAIS:")
        print(f"   • Alertas ativos: {stats['active_alerts']}")
        print(f"   • Total no histórico: {stats['total_in_history']}")
        print(f"   • Regras configuradas: {stats['configured_rules']}")
        print(f"   • Canais configurados: {len(stats['configured_channels'])}")
        
        # Alertas por severidade
        if stats['active_by_severity']:
            print(f"\n🔍 ALERTAS ATIVOS POR SEVERIDADE:")
            severity_icons = {
                'low': '🔵',
                'medium': '🟡',
                'high': '🔴',
                'critical': '💀'
            }
            
            for severity, count in stats['active_by_severity'].items():
                icon = severity_icons.get(severity, '⚪')
                print(f"   {icon} {severity.upper()}: {count}")
        
        # Alertas ativos
        if active_alerts:
            print(f"\n🚨 ALERTAS ATIVOS:")
            for alert in sorted(active_alerts, key=lambda x: x.created_at, reverse=True)[:10]:
                age_minutes = (time.time() - alert.created_at) / 60
                status_icon = {
                    AlertStatus.ACTIVE: "🔴",
                    AlertStatus.ACKNOWLEDGED: "🟡",
                    AlertStatus.RESOLVED: "🟢",
                    AlertStatus.SUPPRESSED: "⚫"
                }.get(alert.status, "⚪")
                
                print(f"   {status_icon} {alert.title[:50]}...")
                print(f"      ID: {alert.id} | Severidade: {alert.severity.value.upper()}")
                print(f"      Idade: {age_minutes:.0f}min | Ocorrências: {alert.trigger_count}")
        
        # Estatísticas de notificações
        if stats['notification_stats']:
            print(f"\n📨 ESTATÍSTICAS DE NOTIFICAÇÕES:")
            for stat_name, count in stats['notification_stats'].items():
                print(f"   • {stat_name}: {count}")
        
        # Canais configurados
        print(f"\n📢 CANAIS CONFIGURADOS:")
        for channel_name in stats['configured_channels']:
            config = self.notification_configs.get(NotificationChannel(channel_name))
            if config:
                status = "🟢 ATIVO" if config.enabled else "🔴 INATIVO"
                print(f"   • {channel_name.upper()}: {status} (min: {config.min_severity.value})")
        
        print("="*80)
    
    def start_background_monitoring(self):
        """Inicia monitoramento em background"""
        if self._running:
            return
        
        self._running = True
        
        async def alert_monitor():
            """Monitor de alertas em background"""
            while self._running:
                try:
                    current_time = time.time()
                    
                    # Auto-resolver alertas antigos
                    alerts_to_resolve = []
                    
                    with self._lock:
                        for alert_id, alert in self.active_alerts.items():
                            # Auto-resolver após 24 horas sem nova ocorrência
                            if current_time - alert.last_triggered > 86400:
                                alerts_to_resolve.append(alert_id)
                    
                    # Resolver alertas antigos
                    for alert_id in alerts_to_resolve:
                        self.resolve_alert(alert_id)
                        if structured_logger:
                            structured_logger.info(
                                f"Auto-resolved stale alert: {alert_id}",
                                component=Component.SYSTEM
                            )
                    
                    # Verificar escalações pendentes
                    with self._lock:
                        for alert in self.active_alerts.values():
                            if not alert.escalated:
                                rule = self.alert_rules.get(alert.rule_name)
                                if rule and rule.escalation_after_minutes:
                                    age_minutes = (current_time - alert.created_at) / 60
                                    if age_minutes >= rule.escalation_after_minutes:
                                        if rule.escalation_severity:
                                            alert.severity = rule.escalation_severity
                                        alert.escalated = True
                                        
                                        # Re-enviar notificações com severidade escalada
                                        await self._send_notifications(alert, rule)
                    
                    await asyncio.sleep(60)  # Verificar a cada minuto
                    
                except Exception as e:
                    if structured_logger:
                        structured_logger.error(f"Alert monitor error: {e}", component=Component.SYSTEM)
                    await asyncio.sleep(60)
        
        # Iniciar task de monitoramento
        self._background_tasks = [asyncio.create_task(alert_monitor())]
    
    def stop_background_monitoring(self):
        """Para monitoramento em background"""
        self._running = False
        
        for task in self._background_tasks:
            task.cancel()
        
        self._background_tasks.clear()
    
    def export_alerts(self, format: str = 'json') -> str:
        """Exporta alertas para arquivo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_dir = Path("data/alerts/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            filename = export_dir / f"alerts_export_{timestamp}.json"
            
            export_data = {
                'timestamp': timestamp,
                'active_alerts': [asdict(alert) for alert in self.active_alerts.values()],
                'alert_history': [asdict(alert) for alert in list(self.alert_history)[-100:]],  # Últimos 100
                'statistics': self.get_alert_stats(),
                'rules': {name: asdict(rule) for name, rule in self.alert_rules.items()}
            }
            
            # Converter enums para strings
            def convert_enums(obj):
                if isinstance(obj, dict):
                    return {k: convert_enums(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_enums(item) for item in obj]
                elif isinstance(obj, Enum):
                    return obj.value
                else:
                    return obj
            
            export_data = convert_enums(export_data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        if structured_logger:
            structured_logger.info(
                f"Alerts exported to {filename}",
                component=Component.SYSTEM,
                context={'format': format, 'filename': str(filename)}
            )
        
        return str(filename)


# Instância global
alert_system = AlertSystem()


# Configurações padrão para integração
def setup_default_alert_rules():
    """Configura regras de alerta padrão"""
    default_rules = [
        AlertRule(
            name="scraper_high_error_rate",
            description="Taxa de erro do scraper muito alta",
            condition="error_rate > 20%",
            threshold=20.0,
            severity=AlertSeverity.HIGH,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
            cooldown_minutes=30,
            escalation_after_minutes=120,
            escalation_severity=AlertSeverity.CRITICAL
        ),
        AlertRule(
            name="circuit_breaker_open",
            description="Circuit breaker aberto - sistema sobrecarregado",
            condition="circuit_breaker_state = OPEN",
            threshold=1.0,
            severity=AlertSeverity.HIGH,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
            cooldown_minutes=15
        ),
        AlertRule(
            name="data_quality_degraded",
            description="Qualidade dos dados degradada",
            condition="quality_score < 70%",
            threshold=70.0,
            severity=AlertSeverity.MEDIUM,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
            cooldown_minutes=60
        ),
        AlertRule(
            name="system_performance_slow",
            description="Performance do sistema degradada",
            condition="avg_response_time > 10s",
            threshold=10.0,
            severity=AlertSeverity.MEDIUM,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
            cooldown_minutes=45
        ),
        AlertRule(
            name="critical_system_failure",
            description="Falha crítica do sistema",
            condition="multiple_systems_down",
            threshold=1.0,
            severity=AlertSeverity.CRITICAL,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
            cooldown_minutes=5,
            escalation_after_minutes=30
        )
    ]
    
    for rule in default_rules:
        alert_system.add_alert_rule(rule)
    
    if structured_logger:
        structured_logger.info(
            f"Default alert rules configured: {len(default_rules)}",
            component=Component.SYSTEM
        )


# Função de conveniência para disparar alertas
async def trigger_alert(
    rule_name: str,
    title: str,
    description: str,
    context: Dict[str, Any] = None
) -> Optional[str]:
    """Função de conveniência para disparar alertas"""
    return await alert_system.trigger_alert(rule_name, title, description, context)


# Integração com sistema de métricas
def integrate_with_metrics():
    """Integra sistema de alertas com métricas"""
    if not metrics_tracker:
        return
    
    # Adicionar callback para métricas que devem gerar alertas
    def metrics_alert_callback(alert):
        """Callback para alertas baseados em métricas"""
        asyncio.create_task(
            alert_system.trigger_alert(
                rule_name=f"metric_{alert.metric_name}",
                title=f"Métrica {alert.metric_name} fora do normal",
                description=f"Valor: {alert.value}, Threshold: {alert.threshold}",
                context={
                    'metric_name': alert.metric_name,
                    'current_value': alert.value,
                    'threshold': alert.threshold,
                    'severity': alert.severity.value
                }
            )
        )
    
    # Configurar alertas baseados em métricas existentes
    from .metrics_tracker import AlertRule as MetricAlertRule
    
    metric_rules = [
        MetricAlertRule(
            name="high_error_rate_metric",
            metric_name="scraper.error_rate",
            condition="gt",
            threshold=20.0,
            severity=AlertSeverity.HIGH,
            callback=metrics_alert_callback
        ),
        MetricAlertRule(
            name="circuit_breaker_open_metric",
            metric_name="circuit_breaker.current_state", 
            condition="gt",
            threshold=0.5,
            severity=AlertSeverity.HIGH,
            callback=metrics_alert_callback
        ),
        MetricAlertRule(
            name="low_data_quality_metric",
            metric_name="validation.quality_score",
            condition="lt",
            threshold=70.0,
            severity=AlertSeverity.MEDIUM,
            callback=metrics_alert_callback
        )
    ]
    
    for rule in metric_rules:
        metrics_tracker.add_alert_rule(rule)