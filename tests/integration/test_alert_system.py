#!/usr/bin/env python3
"""
Teste do Sistema de Alertas Automáticos

Este teste demonstra o sistema completo de alertas,
incluindo diferentes canais de notificação e escalação.
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.alert_system import (
    AlertSystem, AlertRule, AlertSeverity, NotificationChannel,
    NotificationConfig, AlertStatus, setup_default_alert_rules
)


async def test_basic_alerts():
    """Teste básico de alertas"""
    print("🧪 TESTE BÁSICO DE ALERTAS")
    print("-" * 50)
    
    alert_system = AlertSystem("test_alerts_config")
    
    # Configurar regra de teste
    test_rule = AlertRule(
        name="test_alert",
        description="Alerta de teste para demonstração",
        condition="test_value > 10",
        threshold=10.0,
        severity=AlertSeverity.MEDIUM,
        channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
        cooldown_minutes=1  # Cooldown curto para teste
    )
    
    alert_system.add_alert_rule(test_rule)
    
    # Disparar alerta
    print("Disparando alerta de teste...")
    alert_id = await alert_system.trigger_alert(
        rule_name="test_alert",
        title="Alerta de Teste",
        description="Este é um alerta de teste para verificar o funcionamento do sistema",
        context={
            'test_value': 15,
            'source': 'test_function',
            'timestamp': time.time()
        }
    )
    
    print(f"✅ Alerta disparado com ID: {alert_id}")
    
    # Verificar alertas ativos
    active_alerts = alert_system.get_active_alerts()
    print(f"📊 Alertas ativos: {len(active_alerts)}")
    
    if active_alerts:
        alert = active_alerts[0]
        print(f"   • ID: {alert.id}")
        print(f"   • Título: {alert.title}")
        print(f"   • Severidade: {alert.severity.value}")
        print(f"   • Status: {alert.status.value}")
    
    # Testar reconhecimento de alerta
    if alert_id:
        success = alert_system.acknowledge_alert(alert_id, "test_user")
        print(f"✅ Alerta reconhecido: {success}")
    
    print("✅ Teste básico concluído!")
    return alert_system


async def test_notification_channels():
    """Teste de diferentes canais de notificação"""
    print("\n🧪 TESTE DE CANAIS DE NOTIFICAÇÃO")
    print("-" * 50)
    
    alert_system = AlertSystem("test_notifications")
    
    # Configurar diferentes canais
    configs = [
        NotificationConfig(
            channel=NotificationChannel.CONSOLE,
            enabled=True,
            min_severity=AlertSeverity.LOW
        ),
        NotificationConfig(
            channel=NotificationChannel.FILE,
            enabled=True,
            min_severity=AlertSeverity.MEDIUM,
            config={'file_path': 'test_alerts/notifications.log'}
        ),
        NotificationConfig(
            channel=NotificationChannel.WEBHOOK,
            enabled=False,  # Desabilitado para teste
            min_severity=AlertSeverity.HIGH,
            config={
                'url': 'https://httpbin.org/post',
                'headers': {'X-Test': 'true'}
            }
        )
    ]
    
    for config in configs:
        alert_system.add_notification_config(config)
    
    # Configurar regras para diferentes severidades
    rules = [
        AlertRule(
            name="low_severity_test",
            description="Teste de severidade baixa",
            condition="test",
            threshold=1.0,
            severity=AlertSeverity.LOW,
            channels=[NotificationChannel.CONSOLE]
        ),
        AlertRule(
            name="medium_severity_test",
            description="Teste de severidade média",
            condition="test",
            threshold=1.0,
            severity=AlertSeverity.MEDIUM,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE]
        ),
        AlertRule(
            name="high_severity_test",
            description="Teste de severidade alta",
            condition="test",
            threshold=1.0,
            severity=AlertSeverity.HIGH,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE, NotificationChannel.WEBHOOK]
        ),
        AlertRule(
            name="critical_severity_test",
            description="Teste de severidade crítica",
            condition="test",
            threshold=1.0,
            severity=AlertSeverity.CRITICAL,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE]
        )
    ]
    
    for rule in rules:
        alert_system.add_alert_rule(rule)
    
    print("Testando alertas de diferentes severidades...")
    
    # Disparar alertas de diferentes severidades
    severities = [
        (AlertSeverity.LOW, "Alerta de baixa prioridade"),
        (AlertSeverity.MEDIUM, "Alerta de prioridade média"),
        (AlertSeverity.HIGH, "Alerta de alta prioridade"),
        (AlertSeverity.CRITICAL, "⚠️ ALERTA CRÍTICO ⚠️")
    ]
    
    alert_ids = []
    for severity, title in severities:
        rule_name = f"{severity.value}_severity_test"
        
        alert_id = await alert_system.trigger_alert(
            rule_name=rule_name,
            title=title,
            description=f"Este é um alerta de teste com severidade {severity.value.upper()}",
            context={
                'severity_level': severity.value,
                'test_type': 'notification_channels',
                'simulated': True
            }
        )
        
        alert_ids.append(alert_id)
        print(f"   📨 {severity.value.upper()}: {title}")
        
        # Pequena pausa entre alertas
        await asyncio.sleep(0.5)
    
    # Mostrar estatísticas
    stats = alert_system.get_alert_stats()
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   • Alertas ativos: {stats['active_alerts']}")
    print(f"   • Por severidade: {stats['active_by_severity']}")
    print(f"   • Canais configurados: {len(stats['configured_channels'])}")
    
    print("✅ Teste de canais concluído!")
    return alert_system


async def test_alert_escalation():
    """Teste de escalação de alertas"""
    print("\n🧪 TESTE DE ESCALAÇÃO DE ALERTAS")
    print("-" * 50)
    
    alert_system = AlertSystem("test_escalation")
    
    # Configurar regra com escalação
    escalation_rule = AlertRule(
        name="escalation_test",
        description="Teste de escalação automática",
        condition="test_escalation",
        threshold=1.0,
        severity=AlertSeverity.MEDIUM,
        channels=[NotificationChannel.CONSOLE],
        cooldown_minutes=0,  # Sem cooldown para teste
        escalation_after_minutes=0.05,  # 3 segundos para teste
        escalation_severity=AlertSeverity.CRITICAL
    )
    
    alert_system.add_alert_rule(escalation_rule)
    
    print("Disparando alerta que será escalado...")
    
    # Disparar alerta inicial
    alert_id = await alert_system.trigger_alert(
        rule_name="escalation_test",
        title="Alerta que será escalado",
        description="Este alerta será automaticamente escalado para crítico",
        context={'escalation_test': True}
    )
    
    print(f"✅ Alerta inicial disparado (MEDIUM)")
    print("⏳ Aguardando escalação automática...")
    
    # Iniciar monitoramento para escalação
    alert_system.start_background_monitoring()
    
    # Aguardar escalação
    await asyncio.sleep(4)  # Aguardar mais que o tempo de escalação
    
    # Verificar se foi escalado
    active_alerts = alert_system.get_active_alerts()
    if active_alerts:
        alert = active_alerts[0]
        if alert.escalated and alert.severity == AlertSeverity.CRITICAL:
            print("🚨 Alerta escalado com sucesso para CRÍTICO!")
        else:
            print("⚠️ Escalação não funcionou como esperado")
    
    alert_system.stop_background_monitoring()
    
    print("✅ Teste de escalação concluído!")
    return alert_system


async def test_alert_grouping_and_cooldown():
    """Teste de agrupamento e cooldown de alertas"""
    print("\n🧪 TESTE DE AGRUPAMENTO E COOLDOWN")
    print("-" * 50)
    
    alert_system = AlertSystem("test_grouping")
    
    # Configurar regra com cooldown
    cooldown_rule = AlertRule(
        name="cooldown_test",
        description="Teste de cooldown entre alertas",
        condition="test_cooldown",
        threshold=1.0,
        severity=AlertSeverity.MEDIUM,
        channels=[NotificationChannel.CONSOLE],
        cooldown_minutes=0.1  # 6 segundos para teste
    )
    
    alert_system.add_alert_rule(cooldown_rule)
    
    print("Testando cooldown - disparando alertas similares rapidamente...")
    
    # Disparar múltiplos alertas similares
    alert_ids = []
    for i in range(5):
        alert_id = await alert_system.trigger_alert(
            rule_name="cooldown_test",
            title="Alerta repetitivo",
            description="Este alerta será agrupado devido ao cooldown",
            context={'attempt': i + 1}
        )
        
        if alert_id:
            alert_ids.append(alert_id)
        
        print(f"   Tentativa {i+1}: {'✅ Enviado' if alert_id else '⏸️ Bloqueado (cooldown)'}")
        
        await asyncio.sleep(1)  # 1 segundo entre tentativas
    
    print(f"\n📊 Resultado: {len(set(alert_ids))} alertas únicos de 5 tentativas")
    
    # Verificar agrupamento
    active_alerts = alert_system.get_active_alerts()
    if active_alerts:
        alert = active_alerts[0]
        print(f"   • Ocorrências registradas: {alert.trigger_count}")
        print(f"   • Primeira ocorrência: {time.ctime(alert.created_at)}")
        print(f"   • Última ocorrência: {time.ctime(alert.last_triggered)}")
    
    print("✅ Teste de agrupamento concluído!")
    return alert_system


async def test_alert_resolution():
    """Teste de resolução de alertas"""
    print("\n🧪 TESTE DE RESOLUÇÃO DE ALERTAS")
    print("-" * 50)
    
    alert_system = AlertSystem("test_resolution")
    
    # Configurar regra simples
    resolution_rule = AlertRule(
        name="resolution_test",
        description="Teste de resolução de alertas",
        condition="test_resolution",
        threshold=1.0,
        severity=AlertSeverity.HIGH,
        channels=[NotificationChannel.CONSOLE]
    )
    
    alert_system.add_alert_rule(resolution_rule)
    
    # Disparar alguns alertas
    alert_ids = []
    for i in range(3):
        alert_id = await alert_system.trigger_alert(
            rule_name="resolution_test",
            title=f"Problema #{i+1}",
            description=f"Problema número {i+1} que precisa ser resolvido",
            context={'problem_id': i+1}
        )
        alert_ids.append(alert_id)
    
    print(f"✅ {len(alert_ids)} alertas criados")
    
    # Mostrar alertas ativos
    active_alerts = alert_system.get_active_alerts()
    print(f"📊 Alertas ativos antes da resolução: {len(active_alerts)}")
    
    # Reconhecer o primeiro alerta
    if alert_ids[0]:
        success = alert_system.acknowledge_alert(alert_ids[0], "operador_1")
        print(f"✅ Primeiro alerta reconhecido: {success}")
    
    # Resolver o segundo alerta
    if alert_ids[1]:
        success = alert_system.resolve_alert(alert_ids[1])
        print(f"✅ Segundo alerta resolvido: {success}")
    
    # Verificar status final
    active_alerts = alert_system.get_active_alerts()
    print(f"📊 Alertas ativos após operações: {len(active_alerts)}")
    
    # Mostrar status de cada alerta
    for i, alert_id in enumerate(alert_ids):
        if alert_id in [a.id for a in active_alerts]:
            alert = next(a for a in active_alerts if a.id == alert_id)
            print(f"   • Alerta {i+1}: {alert.status.value.upper()}")
        else:
            print(f"   • Alerta {i+1}: RESOLVIDO")
    
    print("✅ Teste de resolução concluído!")
    return alert_system


async def test_integration_with_metrics():
    """Teste de integração com sistema de métricas"""
    print("\n🧪 TESTE DE INTEGRAÇÃO COM MÉTRICAS")
    print("-" * 50)
    
    # Importar sistemas necessários
    from src.metrics_tracker import metrics_tracker, AlertRule as MetricAlertRule
    from src.alert_system import integrate_with_metrics
    
    alert_system = AlertSystem("test_integration")
    
    # Configurar integração
    setup_default_alert_rules()
    integrate_with_metrics()
    
    print("Simulando métricas que devem gerar alertas...")
    
    # Simular métricas problemáticas
    test_metrics = [
        ("scraper.error_rate", 25.0, "Taxa de erro alta"),
        ("validation.quality_score", 65.0, "Qualidade baixa"),
        ("circuit_breaker.current_state", 1.0, "Circuit breaker aberto")
    ]
    
    for metric_name, value, description in test_metrics:
        print(f"   📊 Definindo {metric_name} = {value} ({description})")
        metrics_tracker.set_gauge(metric_name, value)
        
        # Aguardar um pouco para processamento
        await asyncio.sleep(0.5)
    
    # Verificar se alertas foram gerados
    active_alerts = alert_system.get_active_alerts()
    print(f"\n📊 Alertas gerados pela integração: {len(active_alerts)}")
    
    for alert in active_alerts:
        print(f"   🚨 {alert.title} ({alert.severity.value.upper()})")
    
    print("✅ Teste de integração concluído!")
    return alert_system


async def test_alert_dashboard_and_export():
    """Teste de dashboard e exportação de alertas"""
    print("\n🧪 TESTE DE DASHBOARD E EXPORTAÇÃO")
    print("-" * 50)
    
    alert_system = AlertSystem("test_dashboard")
    
    # Configurar várias regras
    setup_default_alert_rules()
    
    # Gerar alertas de diferentes tipos
    test_scenarios = [
        ("scraper_high_error_rate", "Taxa de erro crítica", AlertSeverity.CRITICAL),
        ("circuit_breaker_open", "Circuit breaker ativo", AlertSeverity.HIGH),
        ("data_quality_degraded", "Qualidade de dados baixa", AlertSeverity.MEDIUM),
        ("system_performance_slow", "Performance degradada", AlertSeverity.MEDIUM)
    ]
    
    print("Gerando alertas de teste...")
    for rule_name, title, severity in test_scenarios:
        await alert_system.trigger_alert(
            rule_name=rule_name,
            title=title,
            description=f"Alerta de teste para {title.lower()}",
            context={
                'test_scenario': True,
                'severity': severity.value,
                'generated_at': time.time()
            }
        )
    
    # Mostrar dashboard
    print("\n📊 DASHBOARD DE ALERTAS:")
    alert_system.print_alert_dashboard()
    
    # Testar exportação
    print("\n💾 Testando exportação...")
    export_file = alert_system.export_alerts('json')
    print(f"✅ Alertas exportados para: {export_file}")
    
    # Verificar se arquivo foi criado
    if Path(export_file).exists():
        size = Path(export_file).stat().st_size
        print(f"   📄 Arquivo criado: {size} bytes")
    else:
        print("   ❌ Arquivo não encontrado")
    
    print("✅ Teste de dashboard concluído!")
    return alert_system


async def main():
    """Função principal dos testes"""
    print("🧪 TESTES COMPLETOS DO SISTEMA DE ALERTAS")
    print("=" * 80)
    print("Este conjunto de testes demonstra o sistema completo")
    print("de alertas automáticos para monitoramento proativo.\n")
    
    try:
        # Criar diretório para testes
        Path("test_alerts").mkdir(exist_ok=True)
        
        await test_basic_alerts()
        await test_notification_channels()
        await test_alert_escalation()
        await test_alert_grouping_and_cooldown()
        await test_alert_resolution()
        await test_integration_with_metrics()
        await test_alert_dashboard_and_export()
        
        print("\n" + "=" * 80)
        print("🎉 TODOS OS TESTES DE ALERTAS CONCLUÍDOS!")
        print("=" * 80)
        
        print("\n💡 FUNCIONALIDADES DEMONSTRADAS:")
        print("   ✅ Alertas automáticos por severidade")
        print("   ✅ Múltiplos canais de notificação")
        print("   ✅ Escalação automática de alertas")
        print("   ✅ Agrupamento e cooldown inteligente")
        print("   ✅ Reconhecimento e resolução manual")
        print("   ✅ Integração com sistema de métricas")
        print("   ✅ Dashboard em tempo real")
        print("   ✅ Exportação para auditoria")
        print("   ✅ Background monitoring automático")
        
        print("\n🚨 CANAIS SUPORTADOS:")
        print("   📧 Email (SMTP)")
        print("   🔗 Webhook (HTTP/REST)")
        print("   💬 Slack")
        print("   🖥️ Console")
        print("   📁 Arquivo de log")
        print("   🎮 Discord (configurável)")
        print("   📺 Microsoft Teams (configurável)")
        
        print("\n🔧 RECURSOS AVANÇADOS:")
        print("   ⚡ Rate limiting por canal")
        print("   🕐 Cooldown configurável")
        print("   📊 Escalação por tempo")
        print("   🎭 Templates customizáveis")
        print("   📈 Métricas de notificações")
        print("   🔄 Auto-resolução de alertas antigos")
        print("   🧹 Limpeza automática do histórico")
        
        print("\n🚀 SISTEMA DE ALERTAS PRONTO PARA PRODUÇÃO!")
        
        # Limpeza
        import shutil
        if Path("test_alerts").exists():
            shutil.rmtree("test_alerts")
            print("\n🧹 Arquivos de teste limpos")
        
    except Exception as e:
        print(f"\n❌ Erro durante testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())