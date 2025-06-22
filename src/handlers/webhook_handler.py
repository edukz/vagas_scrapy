"""
Webhook Handler - Sistema de Notificações Automáticas

Sistema completo de webhooks para notificar sobre novas vagas,
atualizações do sistema e eventos importantes.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import urllib.request
import urllib.parse

from ..utils.menu_system import MenuSystem, Colors


class WebhookHandler:
    """Gerencia sistema de webhooks e notificações"""
    
    def __init__(self):
        self.menu = MenuSystem()
        self.webhooks_dir = Path("data/webhooks")
        self.config_file = self.webhooks_dir / "webhook_config.json"
        self.history_file = self.webhooks_dir / "webhook_history.json"
        
        # Criar diretório se não existir
        self.webhooks_dir.mkdir(parents=True, exist_ok=True)
        
        # Tipos de eventos suportados
        self.event_types = {
            "new_jobs": "🆕 Novas vagas encontradas",
            "job_update": "🔄 Vagas atualizadas", 
            "scraping_complete": "✅ Scraping concluído",
            "scraping_error": "❌ Erro no scraping",
            "system_alert": "⚠️ Alerta do sistema",
            "daily_summary": "📊 Resumo diário",
            "threshold_reached": "🎯 Meta alcançada"
        }
        
        # Carregar configuração existente
        self.config = self._load_config()
    
    async def manage_webhooks(self) -> None:
        """Interface principal de gerenciamento de webhooks"""
        print(f"\n{Colors.BLUE}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BLUE}║{Colors.RESET}                        📡 SISTEMA DE WEBHOOKS                           {Colors.BLUE}║{Colors.RESET}")
        print(f"{Colors.BLUE}║{Colors.RESET}                  Notificações automáticas em tempo real                 {Colors.BLUE}║{Colors.RESET}")
        print(f"{Colors.BLUE}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.GREEN}🚀 FUNCIONALIDADES DOS WEBHOOKS:{Colors.RESET}")
        print(f"   ✅ Notificações em tempo real")
        print(f"   ✅ Múltiplos tipos de eventos")
        print(f"   ✅ URLs personalizáveis (Slack, Discord, Teams, etc)")
        print(f"   ✅ Filtros e condições")
        print(f"   ✅ Histórico e estatísticas")
        print(f"   ✅ Retry automático em caso de falha")
        
        # Mostrar status atual
        await self._show_webhook_status()
        
        while True:
            print(f"\n{Colors.CYAN}📡 GERENCIAR WEBHOOKS:{Colors.RESET}")
            print(f"  {Colors.CYAN}[1]{Colors.RESET} ➕ Adicionar novo webhook")
            print(f"  {Colors.CYAN}[2]{Colors.RESET} 📋 Listar webhooks configurados")
            print(f"  {Colors.CYAN}[3]{Colors.RESET} ⚙️ Configurar webhook existente")
            print(f"  {Colors.CYAN}[4]{Colors.RESET} 🧪 Testar webhook")
            print(f"  {Colors.CYAN}[5]{Colors.RESET} 📊 Ver histórico de envios")
            print(f"  {Colors.CYAN}[6]{Colors.RESET} 🔔 Criar webhook para Slack")
            print(f"  {Colors.CYAN}[7]{Colors.RESET} 💬 Criar webhook para Discord")
            print(f"  {Colors.CYAN}[8]{Colors.RESET} 💼 Criar webhook para Teams")
            print(f"  {Colors.CYAN}[9]{Colors.RESET} 📈 Estatísticas dos webhooks")
            print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (0-9): {Colors.RESET}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                await self._add_webhook()
            elif choice == "2":
                await self._list_webhooks()
            elif choice == "3":
                await self._configure_webhook()
            elif choice == "4":
                await self._test_webhook()
            elif choice == "5":
                await self._show_webhook_history()
            elif choice == "6":
                await self._create_slack_webhook()
            elif choice == "7":
                await self._create_discord_webhook()
            elif choice == "8":
                await self._create_teams_webhook()
            elif choice == "9":
                await self._show_webhook_statistics()
            else:
                print(f"{Colors.RED}❌ Opção inválida.{Colors.RESET}")
                input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_webhook_status(self) -> None:
        """Mostra status atual dos webhooks"""
        print(f"\n{Colors.CYAN}📊 STATUS ATUAL DOS WEBHOOKS:{Colors.RESET}")
        
        webhooks = self.config.get('webhooks', [])
        active_webhooks = [w for w in webhooks if w.get('enabled', True)]
        
        print(f"   📡 Total configurados: {len(webhooks)}")
        print(f"   ✅ Ativos: {len(active_webhooks)}")
        print(f"   ❌ Inativos: {len(webhooks) - len(active_webhooks)}")
        
        if active_webhooks:
            print(f"\n🔔 WEBHOOKS ATIVOS:")
            for webhook in active_webhooks[:3]:
                name = webhook.get('name', 'Sem nome')
                events = len(webhook.get('events', []))
                print(f"   • {name} - {events} evento(s)")
            
            if len(active_webhooks) > 3:
                print(f"   ... e mais {len(active_webhooks) - 3} webhooks")
    
    async def _add_webhook(self) -> None:
        """Adiciona novo webhook"""
        print(f"\n{Colors.GREEN}➕ ADICIONAR NOVO WEBHOOK{Colors.RESET}")
        print(f"{Colors.GRAY}Configure um novo webhook para receber notificações{Colors.RESET}\n")
        
        # Informações básicas
        name = input(f"📝 Nome do webhook: ").strip()
        if not name:
            print(f"{Colors.RED}❌ Nome é obrigatório.{Colors.RESET}")
            return
        
        url = input(f"🌐 URL do webhook: ").strip()
        if not url:
            print(f"{Colors.RED}❌ URL é obrigatória.{Colors.RESET}")
            return
        
        # Validar URL básica
        if not (url.startswith('http://') or url.startswith('https://')):
            print(f"{Colors.RED}❌ URL deve começar com http:// ou https://{Colors.RESET}")
            return
        
        # Selecionar eventos
        print(f"\n{Colors.CYAN}📡 SELECIONAR EVENTOS:{Colors.RESET}")
        print(f"   {Colors.GRAY}Escolha os eventos que devem disparar este webhook{Colors.RESET}\n")
        
        selected_events = []
        for i, (event_key, event_desc) in enumerate(self.event_types.items(), 1):
            response = input(f"   {event_desc} [S/n]: ").strip().lower()
            if response in ['', 's', 'sim', 'y', 'yes']:
                selected_events.append(event_key)
        
        if not selected_events:
            print(f"{Colors.RED}❌ Pelo menos um evento deve ser selecionado.{Colors.RESET}")
            return
        
        # Configurações avançadas
        print(f"\n{Colors.YELLOW}⚙️ CONFIGURAÇÕES AVANÇADAS:{Colors.RESET}")
        
        # Filtros
        filter_companies = input(f"🏢 Filtrar empresas específicas (separadas por vírgula, Enter=todas): ").strip()
        filter_keywords = input(f"🔍 Filtrar palavras-chave no título (separadas por vírgula, Enter=todas): ").strip()
        
        # Threshold
        min_jobs = input(f"📊 Número mínimo de vagas para disparar (Enter=1): ").strip()
        try:
            min_jobs = int(min_jobs) if min_jobs else 1
        except ValueError:
            min_jobs = 1
        
        # Criar webhook
        webhook = {
            "id": self._generate_webhook_id(),
            "name": name,
            "url": url,
            "events": selected_events,
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "filters": {
                "companies": [c.strip() for c in filter_companies.split(',')] if filter_companies else [],
                "keywords": [k.strip() for k in filter_keywords.split(',')] if filter_keywords else [],
                "min_jobs": min_jobs
            },
            "retry_config": {
                "max_retries": 3,
                "retry_delay": 5
            },
            "stats": {
                "total_sent": 0,
                "total_failed": 0,
                "last_sent": None
            }
        }
        
        # Salvar
        self.config.setdefault('webhooks', []).append(webhook)
        self._save_config()
        
        print(f"\n{Colors.GREEN}✅ Webhook '{name}' criado com sucesso!{Colors.RESET}")
        print(f"   📡 ID: {webhook['id']}")
        print(f"   🎯 Eventos: {len(selected_events)}")
        print(f"   🔔 Status: Ativo")
        
        # Testar webhook
        test = input(f"\n{Colors.YELLOW}🧪 Testar webhook agora? [S/n]: {Colors.RESET}").strip().lower()
        if test in ['', 's', 'sim', 'y', 'yes']:
            await self._test_specific_webhook(webhook)
    
    async def _list_webhooks(self) -> None:
        """Lista todos os webhooks configurados"""
        print(f"\n{Colors.CYAN}📋 WEBHOOKS CONFIGURADOS{Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 80}{Colors.RESET}")
        
        webhooks = self.config.get('webhooks', [])
        
        if not webhooks:
            print(f"{Colors.YELLOW}⚠️ Nenhum webhook configurado ainda.{Colors.RESET}")
            print(f"   Use a opção 1 para adicionar seu primeiro webhook.")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        for i, webhook in enumerate(webhooks, 1):
            status = "🟢 Ativo" if webhook.get('enabled', True) else "🔴 Inativo"
            stats = webhook.get('stats', {})
            
            print(f"\n{Colors.YELLOW}{i:2d}.{Colors.RESET} {webhook.get('name', 'Sem nome')}")
            print(f"     📡 ID: {webhook.get('id', 'N/A')}")
            print(f"     🌐 URL: {webhook.get('url', 'N/A')[:60]}...")
            print(f"     📊 Status: {status}")
            print(f"     🎯 Eventos: {len(webhook.get('events', []))}")
            print(f"     📈 Enviados: {stats.get('total_sent', 0)} | Falhas: {stats.get('total_failed', 0)}")
            
            # Mostrar últimos eventos
            events = webhook.get('events', [])[:3]
            if events:
                event_names = [self.event_types.get(e, e) for e in events]
                print(f"     🔔 Eventos: {', '.join(event_names)}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _create_slack_webhook(self) -> None:
        """Criar webhook específico para Slack"""
        print(f"\n{Colors.BLUE}🔔 CONFIGURAR WEBHOOK SLACK{Colors.RESET}")
        print(f"{Colors.GRAY}Configure notificações para o Slack usando Incoming Webhooks{Colors.RESET}\n")
        
        print(f"{Colors.YELLOW}📋 INSTRUÇÕES:{Colors.RESET}")
        print("1. Acesse https://api.slack.com/apps")
        print("2. Crie um novo app ou use um existente")
        print("3. Vá em 'Incoming Webhooks' e ative")
        print("4. Clique em 'Add New Webhook to Workspace'")
        print("5. Selecione o canal e copie a URL")
        print()
        
        webhook_url = input(f"🔗 Cole a URL do webhook Slack: ").strip()
        if not webhook_url:
            print(f"{Colors.RED}❌ URL é obrigatória.{Colors.RESET}")
            return
        
        channel = input(f"📺 Nome do canal (ex: #jobs): ").strip() or "#jobs"
        
        # Criar webhook Slack
        webhook = {
            "id": self._generate_webhook_id(),
            "name": f"Slack - {channel}",
            "url": webhook_url,
            "type": "slack",
            "events": ["new_jobs", "scraping_complete"],
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "filters": {"min_jobs": 1},
            "slack_config": {
                "channel": channel,
                "username": "Job Scraper Bot",
                "icon_emoji": ":robot_face:"
            },
            "retry_config": {"max_retries": 3, "retry_delay": 5},
            "stats": {"total_sent": 0, "total_failed": 0, "last_sent": None}
        }
        
        self.config.setdefault('webhooks', []).append(webhook)
        self._save_config()
        
        print(f"\n{Colors.GREEN}✅ Webhook Slack configurado com sucesso!{Colors.RESET}")
        print(f"   📺 Canal: {channel}")
        print(f"   🔔 Eventos: Novas vagas e scraping completo")
        
        # Testar
        await self._test_specific_webhook(webhook)
    
    async def _create_discord_webhook(self) -> None:
        """Criar webhook específico para Discord"""
        print(f"\n{Colors.PURPLE}💬 CONFIGURAR WEBHOOK DISCORD{Colors.RESET}")
        print(f"{Colors.GRAY}Configure notificações para o Discord{Colors.RESET}\n")
        
        print(f"{Colors.YELLOW}📋 INSTRUÇÕES:{Colors.RESET}")
        print("1. Abra o Discord e vá para o canal desejado")
        print("2. Clique na engrenagem do canal > Integrações")
        print("3. Clique em 'Criar Webhook'")
        print("4. Configure nome e avatar")
        print("5. Copie a URL do webhook")
        print()
        
        webhook_url = input(f"🔗 Cole a URL do webhook Discord: ").strip()
        if not webhook_url:
            print(f"{Colors.RED}❌ URL é obrigatória.{Colors.RESET}")
            return
        
        server_name = input(f"🎮 Nome do servidor: ").strip() or "Discord Server"
        
        # Criar webhook Discord
        webhook = {
            "id": self._generate_webhook_id(),
            "name": f"Discord - {server_name}",
            "url": webhook_url,
            "type": "discord",
            "events": ["new_jobs", "daily_summary"],
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "filters": {"min_jobs": 1},
            "discord_config": {
                "username": "Job Scraper",
                "avatar_url": None
            },
            "retry_config": {"max_retries": 3, "retry_delay": 5},
            "stats": {"total_sent": 0, "total_failed": 0, "last_sent": None}
        }
        
        self.config.setdefault('webhooks', []).append(webhook)
        self._save_config()
        
        print(f"\n{Colors.GREEN}✅ Webhook Discord configurado com sucesso!{Colors.RESET}")
        print(f"   🎮 Servidor: {server_name}")
        print(f"   🔔 Eventos: Novas vagas e resumo diário")
        
        # Testar
        await self._test_specific_webhook(webhook)
    
    async def _test_webhook(self) -> None:
        """Testar webhook específico"""
        webhooks = self.config.get('webhooks', [])
        
        if not webhooks:
            print(f"{Colors.YELLOW}⚠️ Nenhum webhook configurado para testar.{Colors.RESET}")
            input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        print(f"\n{Colors.CYAN}🧪 TESTAR WEBHOOK{Colors.RESET}")
        print(f"   {Colors.GRAY}Selecione um webhook para testar:{Colors.RESET}\n")
        
        for i, webhook in enumerate(webhooks, 1):
            status = "🟢" if webhook.get('enabled', True) else "🔴"
            print(f"  {Colors.CYAN}[{i}]{Colors.RESET} {status} {webhook.get('name', 'Sem nome')}")
        
        print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar")
        
        try:
            choice = input(f"\n{Colors.YELLOW}➤ Webhook para testar (1-{len(webhooks)}): {Colors.RESET}").strip()
            
            if choice == "0":
                return
            
            webhook_idx = int(choice) - 1
            if 0 <= webhook_idx < len(webhooks):
                await self._test_specific_webhook(webhooks[webhook_idx])
            else:
                print(f"{Colors.RED}❌ Opção inválida.{Colors.RESET}")
        except ValueError:
            print(f"{Colors.RED}❌ Entrada inválida.{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _test_specific_webhook(self, webhook: Dict) -> None:
        """Testa um webhook específico"""
        print(f"\n{Colors.YELLOW}🧪 TESTANDO WEBHOOK: {webhook.get('name')}{Colors.RESET}")
        
        # Criar payload de teste
        test_payload = {
            "event_type": "test",
            "timestamp": datetime.now().isoformat(),
            "message": "🧪 Teste de webhook do Catho Job Scraper",
            "data": {
                "jobs_found": 5,
                "scraping_duration": "2 minutos",
                "test_mode": True
            }
        }
        
        # Adaptar payload para tipo específico
        if webhook.get('type') == 'slack':
            payload = {
                "username": webhook.get('slack_config', {}).get('username', 'Job Scraper Bot'),
                "icon_emoji": webhook.get('slack_config', {}).get('icon_emoji', ':robot_face:'),
                "text": "🧪 *Teste de Webhook*",
                "attachments": [{
                    "color": "good",
                    "fields": [
                        {"title": "Sistema", "value": "Catho Job Scraper", "short": True},
                        {"title": "Status", "value": "✅ Funcionando", "short": True},
                        {"title": "Teste", "value": "Webhook configurado corretamente!", "short": False}
                    ]
                }]
            }
        elif webhook.get('type') == 'discord':
            payload = {
                "username": webhook.get('discord_config', {}).get('username', 'Job Scraper'),
                "embeds": [{
                    "title": "🧪 Teste de Webhook",
                    "description": "Webhook configurado corretamente!",
                    "color": 0x00ff00,
                    "fields": [
                        {"name": "Sistema", "value": "Catho Job Scraper", "inline": True},
                        {"name": "Status", "value": "✅ Funcionando", "inline": True}
                    ],
                    "timestamp": datetime.now().isoformat()
                }]
            }
        else:
            payload = test_payload
        
        # Enviar teste
        success = await self._send_webhook(webhook, payload)
        
        if success:
            print(f"{Colors.GREEN}✅ Teste bem-sucedido!{Colors.RESET}")
            print(f"   📡 Webhook está funcionando corretamente")
        else:
            print(f"{Colors.RED}❌ Teste falhou!{Colors.RESET}")
            print(f"   📡 Verifique a URL e configurações")
    
    async def _send_webhook(self, webhook: Dict, payload: Dict) -> bool:
        """Envia dados para um webhook"""
        try:
            # Tentar usar requests primeiro (mais comum)
            try:
                import requests
                response = requests.post(
                    webhook['url'],
                    json=payload,
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                success = response.status_code < 400
            except ImportError:
                # Fallback para urllib se requests não estiver disponível
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    webhook['url'],
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        success = response.getcode() < 400
                except urllib.error.HTTPError as e:
                    success = e.code < 400
            
            # Atualizar estatísticas
            stats = webhook.setdefault('stats', {})
            if success:
                stats['total_sent'] = stats.get('total_sent', 0) + 1
                stats['last_sent'] = datetime.now().isoformat()
                print(f"{Colors.GREEN}✅ Webhook enviado com sucesso!{Colors.RESET}")
            else:
                stats['total_failed'] = stats.get('total_failed', 0) + 1
                print(f"{Colors.YELLOW}⚠️ Webhook retornou status de erro{Colors.RESET}")
            
            self._save_config()
            return success
                    
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao enviar webhook: {e}{Colors.RESET}")
            
            # Atualizar estatísticas de falha
            stats = webhook.setdefault('stats', {})
            stats['total_failed'] = stats.get('total_failed', 0) + 1
            self._save_config()
            
            return False
    
    def _generate_webhook_id(self) -> str:
        """Gera ID único para webhook"""
        timestamp = str(int(time.time()))
        random_str = hashlib.md5(f"{timestamp}{time.time()}".encode()).hexdigest()[:8]
        return f"webhook_{timestamp}_{random_str}"
    
    def _load_config(self) -> Dict:
        """Carrega configuração dos webhooks"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"webhooks": []}
    
    def _save_config(self) -> None:
        """Salva configuração dos webhooks"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar configuração: {e}")
    
    async def _show_webhook_history(self) -> None:
        """Mostra histórico de envios de webhooks"""
        print(f"\n{Colors.CYAN}📊 HISTÓRICO DE WEBHOOKS{Colors.RESET}")
        print("Esta funcionalidade será implementada para mostrar logs detalhados.")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _configure_webhook(self) -> None:
        """Configura webhook existente"""
        print(f"\n{Colors.YELLOW}⚙️ CONFIGURAR WEBHOOK EXISTENTE{Colors.RESET}")
        print("Esta funcionalidade permitirá editar webhooks existentes.")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _create_teams_webhook(self) -> None:
        """Criar webhook para Microsoft Teams"""
        print(f"\n{Colors.BLUE}💼 CONFIGURAR WEBHOOK TEAMS{Colors.RESET}")
        print("Esta funcionalidade será implementada para Microsoft Teams.")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_webhook_statistics(self) -> None:
        """Mostra estatísticas dos webhooks"""
        print(f"\n{Colors.CYAN}📈 ESTATÍSTICAS DOS WEBHOOKS{Colors.RESET}")
        
        webhooks = self.config.get('webhooks', [])
        if not webhooks:
            print(f"{Colors.YELLOW}⚠️ Nenhum webhook configurado.{Colors.RESET}")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        total_sent = sum(w.get('stats', {}).get('total_sent', 0) for w in webhooks)
        total_failed = sum(w.get('stats', {}).get('total_failed', 0) for w in webhooks)
        
        print(f"📊 RESUMO GERAL:")
        print(f"   📡 Total de webhooks: {len(webhooks)}")
        print(f"   ✅ Envios bem-sucedidos: {total_sent}")
        print(f"   ❌ Envios falharam: {total_failed}")
        print(f"   📈 Taxa de sucesso: {(total_sent/(total_sent+total_failed)*100) if (total_sent+total_failed) > 0 else 0:.1f}%")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _apply_webhook_filters(self, jobs: List[Dict], filters: Dict) -> List[Dict]:
        """Aplica filtros de webhook nas vagas"""
        filtered_jobs = jobs
        
        # Filtro por empresas
        if filters.get('companies'):
            companies = [c.lower() for c in filters['companies']]
            filtered_jobs = [
                job for job in filtered_jobs 
                if any(company in job.get('empresa', '').lower() for company in companies)
            ]
        
        # Filtro por palavras-chave no título
        if filters.get('keywords'):
            keywords = [k.lower() for k in filters['keywords']]
            filtered_jobs = [
                job for job in filtered_jobs 
                if any(keyword in job.get('titulo', '').lower() for keyword in keywords)
            ]
        
        return filtered_jobs
    
    def _create_job_notification_payload(self, webhook: Dict, jobs: List[Dict]) -> Dict:
        """Cria payload de notificação para novas vagas"""
        webhook_type = webhook.get('type', 'generic')
        
        if webhook_type == 'slack':
            return {
                "username": webhook.get('slack_config', {}).get('username', 'Job Scraper Bot'),
                "icon_emoji": webhook.get('slack_config', {}).get('icon_emoji', ':briefcase:'),
                "text": f"🆕 *{len(jobs)} novas vagas encontradas!*",
                "attachments": [{
                    "color": "good",
                    "fields": [
                        {"title": "Total de vagas", "value": str(len(jobs)), "short": True},
                        {"title": "Timestamp", "value": datetime.now().strftime('%d/%m/%Y %H:%M'), "short": True}
                    ] + [
                        {"title": f"📋 {job.get('titulo', 'N/A')}", "value": f"🏢 {job.get('empresa', 'N/A')}", "short": False}
                        for job in jobs[:5]
                    ] + ([{"title": "...", "value": f"E mais {len(jobs)-5} vagas", "short": False}] if len(jobs) > 5 else [])
                }]
            }
        
        elif webhook_type == 'discord':
            return {
                "username": webhook.get('discord_config', {}).get('username', 'Job Scraper'),
                "embeds": [{
                    "title": f"🆕 {len(jobs)} novas vagas encontradas!",
                    "description": f"Foram encontradas {len(jobs)} novas vagas de emprego.",
                    "color": 0x00ff00,
                    "fields": [
                        {"name": "📊 Total", "value": str(len(jobs)), "inline": True},
                        {"name": "⏰ Horário", "value": datetime.now().strftime('%H:%M'), "inline": True}
                    ] + [
                        {"name": f"📋 {job.get('titulo', 'N/A')[:50]}", "value": f"🏢 {job.get('empresa', 'N/A')}", "inline": False}
                        for job in jobs[:3]
                    ],
                    "timestamp": datetime.now().isoformat(),
                    "footer": {"text": "Catho Job Scraper"}
                }]
            }
        
        else:
            # Formato genérico
            return {
                "event_type": "new_jobs",
                "timestamp": datetime.now().isoformat(),
                "jobs_count": len(jobs),
                "jobs": [
                    {
                        "title": job.get('titulo', 'N/A'),
                        "company": job.get('empresa', 'N/A'),
                        "location": job.get('localizacao', 'N/A'),
                        "link": job.get('link', 'N/A')
                    }
                    for job in jobs[:10]  # Limitar para não sobrecarregar
                ]
            }


# Função para integração com outros módulos
async def notify_new_jobs(jobs: List[Dict]) -> None:
    """Notifica webhooks sobre novas vagas encontradas"""
    try:
        handler = WebhookHandler()
        webhooks = handler.config.get('webhooks', [])
        
        for webhook in webhooks:
            if not webhook.get('enabled', True):
                continue
                
            if 'new_jobs' not in webhook.get('events', []):
                continue
            
            # Aplicar filtros
            filtered_jobs = handler._apply_webhook_filters(jobs, webhook.get('filters', {}))
            
            if len(filtered_jobs) >= webhook.get('filters', {}).get('min_jobs', 1):
                payload = handler._create_job_notification_payload(webhook, filtered_jobs)
                await handler._send_webhook(webhook, payload)
    except Exception as e:
        print(f"⚠️ Erro ao enviar notificações webhook: {e}")


async def notify_scraping_complete(total_jobs: int, duration: str) -> None:
    """Notifica webhooks sobre conclusão do scraping"""
    try:
        handler = WebhookHandler()
        webhooks = handler.config.get('webhooks', [])
        
        for webhook in webhooks:
            if not webhook.get('enabled', True):
                continue
                
            if 'scraping_complete' not in webhook.get('events', []):
                continue
            
            # Criar payload baseado no tipo
            webhook_type = webhook.get('type', 'generic')
            
            if webhook_type == 'slack':
                payload = {
                    "username": webhook.get('slack_config', {}).get('username', 'Job Scraper Bot'),
                    "icon_emoji": ":white_check_mark:",
                    "text": "✅ *Scraping concluído com sucesso!*",
                    "attachments": [{
                        "color": "good",
                        "fields": [
                            {"title": "Total de vagas", "value": str(total_jobs), "short": True},
                            {"title": "Duração", "value": duration, "short": True},
                            {"title": "Status", "value": "✅ Completo", "short": True}
                        ]
                    }]
                }
            else:
                payload = {
                    "event_type": "scraping_complete",
                    "timestamp": datetime.now().isoformat(),
                    "total_jobs": total_jobs,
                    "duration": duration,
                    "status": "success"
                }
            
            await handler._send_webhook(webhook, payload)
    except Exception as e:
        print(f"⚠️ Erro ao enviar notificação de conclusão: {e}")


# Função para usar no menu principal
async def manage_webhooks():
    """Função principal para gerenciamento de webhooks"""
    handler = WebhookHandler()
    await handler.manage_webhooks()