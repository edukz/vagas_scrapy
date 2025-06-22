"""
Incremental Scraping Handler - Interface Modernizada para Scraping Incremental

Sistema inteligente que coleta apenas dados novos e atualizados,
otimizando recursos e evitando duplicação de dados.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

from ..core.scraper_multi_mode import scrape_catho_jobs_multi_mode, check_catho_accessibility
from ..utils.utils import save_results
from ..utils.menu_system import MenuSystem, Colors


class IncrementalScrapingHandler:
    """Handler para scraping incremental com otimização inteligente"""
    
    def __init__(self):
        self.menu = MenuSystem()
        
        # Estratégias incrementais disponíveis
        self.incremental_strategies = {
            "⚡ Smart Update": {
                "description": "Atualização inteligente baseada em timestamp",
                "interval_hours": 6,
                "concurrent": 8,
                "pages": 10,
                "deep_check": False,
                "color": Colors.CYAN
            },
            "🔄 Delta Sync": {
                "description": "Sincronização apenas das diferenças encontradas",
                "interval_hours": 12,
                "concurrent": 12,
                "pages": 15,
                "deep_check": True,
                "color": Colors.GREEN
            },
            "🎯 Targeted Refresh": {
                "description": "Refresh direcionado em áreas com mais atividade",
                "interval_hours": 4,
                "concurrent": 6,
                "pages": 8,
                "deep_check": False,
                "color": Colors.YELLOW
            },
            "🌊 Full Incremental": {
                "description": "Varredura completa com filtro incremental",
                "interval_hours": 24,
                "concurrent": 15,
                "pages": 25,
                "deep_check": True,
                "color": Colors.BLUE
            }
        }
        
        # Caminhos dos checkpoints
        self.checkpoint_dir = Path("data/checkpoints")
        self.checkpoint_file = self.checkpoint_dir / "incremental_checkpoint.json"
        self.stats_file = self.checkpoint_dir / "incremental_stats.json"
        
        # Criar diretório se não existir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    async def run_incremental_scraping(self) -> None:
        """Interface principal do scraping incremental"""
        print(f"\n{Colors.BLUE}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BLUE}║{Colors.RESET}                      🔄 SCRAPING INCREMENTAL                             {Colors.BLUE}║{Colors.RESET}")
        print(f"{Colors.BLUE}║{Colors.RESET}                Coleta apenas dados novos e atualizados                   {Colors.BLUE}║{Colors.RESET}")
        print(f"{Colors.BLUE}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.GREEN}🚀 VANTAGENS DO MODO INCREMENTAL:{Colors.RESET}")
        print(f"   ✅ Coleta apenas vagas novas ou atualizadas")
        print(f"   ✅ Evita duplicação desnecessária de dados")
        print(f"   ✅ Otimização inteligente de recursos")
        print(f"   ✅ Histórico de execuções para tracking")
        print(f"   ✅ Checkpoint automático para recuperação")
        
        # Mostrar status atual
        await self._show_incremental_status()
        
        # Seleção de estratégia
        strategy_config = await self._select_incremental_strategy()
        if not strategy_config:
            return
        
        # Configurações adicionais
        await self._configure_incremental_options(strategy_config)
        
        # Confirmação e execução
        if await self._confirm_incremental_execution(strategy_config):
            await self._execute_incremental_scraping(strategy_config)
    
    async def _show_incremental_status(self) -> None:
        """Mostra status atual do sistema incremental"""
        print(f"\n{Colors.CYAN}📊 STATUS INCREMENTAL ATUAL:{Colors.RESET}")
        
        # Carregar último checkpoint
        last_checkpoint = self._load_checkpoint()
        if last_checkpoint:
            last_run = datetime.fromisoformat(last_checkpoint['timestamp'])
            time_since = datetime.now() - last_run
            
            print(f"   ⏰ Última execução: {last_run.strftime('%d/%m/%Y %H:%M')}")
            print(f"   🕒 Tempo decorrido: {self._format_time_delta(time_since)}")
            print(f"   📈 Vagas na última coleta: {last_checkpoint.get('jobs_found', 0)}")
            print(f"   🆕 Vagas novas: {last_checkpoint.get('new_jobs', 0)}")
            print(f"   🔄 Vagas atualizadas: {last_checkpoint.get('updated_jobs', 0)}")
        else:
            print(f"   {Colors.YELLOW}⚠️ Nenhuma execução anterior encontrada (primeira vez){Colors.RESET}")
        
        # Carregar estatísticas
        stats = self._load_stats()
        if stats:
            print(f"\n📊 ESTATÍSTICAS GERAIS:")
            print(f"   🎯 Total de execuções: {stats.get('total_runs', 0)}")
            print(f"   📋 Total de vagas coletadas: {stats.get('total_jobs', 0)}")
            print(f"   ⚡ Média de eficiência: {stats.get('avg_efficiency', 0):.1f}%")
    
    def _format_time_delta(self, delta: timedelta) -> str:
        """Formata timedelta para exibição"""
        if delta.days > 0:
            return f"{delta.days} dia(s)"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hora(s)"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minuto(s)"
        else:
            return f"{delta.seconds} segundo(s)"
    
    async def _select_incremental_strategy(self) -> Optional[Dict]:
        """Seleção de estratégia incremental"""
        print(f"\n{Colors.BLUE}🔄 ESCOLHA A ESTRATÉGIA INCREMENTAL:{Colors.RESET}")
        print(f"   {Colors.GRAY}Cada estratégia é otimizada para diferentes cenários{Colors.RESET}\n")
        
        options = list(self.incremental_strategies.keys())
        
        for i, (name, config) in enumerate(self.incremental_strategies.items(), 1):
            color = config['color']
            print(f"  {Colors.CYAN}[{i}]{Colors.RESET} {color}{name}{Colors.RESET}")
            print(f"     {Colors.GRAY}{config['description']}{Colors.RESET}")
            print(f"     ⏰ Intervalo: {config['interval_hours']}h | 📄 {config['pages']} páginas | 🔄 {config['concurrent']} jobs")
            print(f"     🔍 Deep check: {'Sim' if config['deep_check'] else 'Não'}")
            print()
        
        print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal\n")
        
        try:
            choice = input(f"{Colors.YELLOW}➤ Sua escolha (1-{len(options)}): {Colors.RESET}").strip()
            
            if choice == "0":
                return None
                
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                selected_key = options[choice_idx]
                config = self.incremental_strategies[selected_key].copy()
                config['strategy_name'] = selected_key
                return config
            else:
                print(f"{Colors.RED}❌ Opção inválida. Tente novamente.{Colors.RESET}")
                return await self._select_incremental_strategy()
                
        except (ValueError, KeyboardInterrupt):
            print(f"{Colors.RED}❌ Entrada inválida.{Colors.RESET}")
            return await self._select_incremental_strategy()
    
    async def _configure_incremental_options(self, config: Dict) -> None:
        """Configuração de opções incrementais"""
        print(f"\n{Colors.BLUE}⚙️ CONFIGURAÇÕES INCREMENTAIS{Colors.RESET}")
        print(f"   {Colors.GRAY}Ajuste os parâmetros para sua necessidade{Colors.RESET}\n")
        
        # Verificar se deve forçar coleta completa
        force_full = input(f"🔄 Forçar coleta completa (ignorar incremental)? [S/N]: ").strip().upper()
        config['force_full'] = force_full == 'S'
        
        if config['force_full']:
            print(f"{Colors.YELLOW}⚠️ Modo completo ativado - todos os dados serão recoletados{Colors.RESET}")
        
        # Multi-modalidade
        multi_mode = input(f"🌍 Buscar todas as modalidades (HO + Presencial + Híbrido)? [S/N]: ").strip().upper()
        config['multi_mode'] = multi_mode == 'S'
        
        # Intervalo personalizado
        custom_interval = input(f"⏰ Intervalo personalizado em horas (Enter = {config['interval_hours']}): ").strip()
        if custom_interval and custom_interval.isdigit():
            config['interval_hours'] = int(custom_interval)
        
        # Limite de vagas novas
        max_new_jobs = input(f"📊 Limite máximo de vagas novas (Enter = sem limite): ").strip()
        if max_new_jobs and max_new_jobs.isdigit():
            config['max_new_jobs'] = int(max_new_jobs)
        
        # Notificação por email (futura implementação)
        email_notify = input(f"📧 Enviar notificação por email? [S/N]: ").strip().upper()
        config['email_notify'] = email_notify == 'S'
    
    async def _confirm_incremental_execution(self, config: Dict) -> bool:
        """Confirmação antes da execução"""
        print(f"\n{Colors.GREEN}✅ CONFIGURAÇÃO DO SCRAPING INCREMENTAL{Colors.RESET}")
        print(f"{Colors.BLUE}{'═' * 60}{Colors.RESET}")
        print(f"🔄 Estratégia: {config['color']}{config['strategy_name']}{Colors.RESET}")
        print(f"⏰ Intervalo: {config['interval_hours']} horas")
        print(f"📄 Páginas: {config['pages']}")
        print(f"🔄 Jobs simultâneos: {config['concurrent']}")
        print(f"🌍 Modalidades: {'Multi (HO + Presencial + Híbrido)' if config['multi_mode'] else 'Apenas Home Office'}")
        print(f"🔍 Deep check: {'Ativado' if config['deep_check'] else 'Desativado'}")
        print(f"🔄 Modo: {'Completo (forçado)' if config.get('force_full') else 'Incremental'}")
        
        if config.get('max_new_jobs'):
            print(f"📊 Limite: {config['max_new_jobs']} vagas novas")
        
        if config.get('email_notify'):
            print(f"📧 Notificação: Email ativado")
        
        # Estimativa baseada no histórico
        estimated_time, estimated_jobs = self._estimate_incremental_execution(config)
        print(f"⏱️  Tempo estimado: {estimated_time}")
        print(f"📈 Vagas estimadas: {estimated_jobs}")
        
        print(f"{Colors.BLUE}{'═' * 60}{Colors.RESET}")
        
        while True:
            print(f"\n{Colors.YELLOW}🚀 Iniciar scraping incremental?{Colors.RESET}")
            print(f"  {Colors.GREEN}[S]{Colors.RESET} Sim, iniciar agora")
            print(f"  {Colors.RED}[N]{Colors.RESET} Não, voltar")
            print(f"  {Colors.CYAN}[A]{Colors.RESET} Agendar execução automática")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (S/N/A): {Colors.RESET}").strip().upper()
            
            if choice in ['S', 'SIM', 'Y', 'YES']:
                return True
            elif choice in ['N', 'NAO', 'NÃO']:
                return False
            elif choice in ['A', 'AGENDAR']:
                await self._schedule_incremental(config)
                return False
            else:
                print(f"{Colors.RED}❌ Opção inválida. Digite S, N ou A.{Colors.RESET}")
    
    def _estimate_incremental_execution(self, config: Dict) -> tuple:
        """Estima tempo e quantidade de vagas baseado no histórico"""
        # Carregar histórico
        stats = self._load_stats()
        last_checkpoint = self._load_checkpoint()
        
        if config.get('force_full') or not last_checkpoint:
            # Modo completo ou primeira execução
            pages = config['pages']
            time_estimate = (pages * 2.0) / max(1, config['concurrent'] * 0.6)
            
            if config.get('multi_mode'):
                time_estimate *= 2.5
            
            jobs_estimate = pages * 12  # Estimativa conservadora
        else:
            # Modo incremental
            time_since_last = datetime.now() - datetime.fromisoformat(last_checkpoint['timestamp'])
            hours_since = time_since_last.total_seconds() / 3600
            
            # Estimar baseado na atividade do mercado
            activity_factor = min(hours_since / config['interval_hours'], 3.0)
            
            time_estimate = (config['pages'] * 1.5 * activity_factor) / max(1, config['concurrent'] * 0.8)
            jobs_estimate = int(config['pages'] * 5 * activity_factor)  # Menos vagas no incremental
        
        # Formatação do tempo
        if time_estimate < 60:
            time_str = f"{int(time_estimate)} segundos"
        elif time_estimate < 3600:
            time_str = f"{int(time_estimate // 60)} minutos"
        else:
            hours = int(time_estimate // 3600)
            minutes = int((time_estimate % 3600) // 60)
            time_str = f"{hours}h {minutes}min"
        
        return time_str, f"{jobs_estimate} vagas novas"
    
    async def _schedule_incremental(self, config: Dict) -> None:
        """Agenda execução automática (futura implementação)"""
        print(f"\n{Colors.CYAN}📅 AGENDAMENTO AUTOMÁTICO{Colors.RESET}")
        print("Esta funcionalidade permitirá agendar execuções automáticas.")
        print("Implementação futura: cron jobs e schedule automático.")
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_incremental_scraping(self, config: Dict) -> None:
        """Executa o scraping incremental"""
        print(f"\n{Colors.GREEN}🚀 INICIANDO SCRAPING INCREMENTAL{Colors.RESET}")
        print(f"{Colors.BLUE}{'═' * 60}{Colors.RESET}")
        print(f"🔄 Estratégia: {config['color']}{config['strategy_name']}{Colors.RESET}")
        
        start_time = datetime.now()
        
        try:
            # Verificar conectividade
            print(f"{Colors.GRAY}🌐 Verificando conectividade...{Colors.RESET}")
            is_accessible = await check_catho_accessibility()
            
            if not is_accessible:
                print(f"{Colors.RED}❌ Site não acessível. Tente novamente em alguns minutos.{Colors.RESET}")
                return
            
            print(f"{Colors.GREEN}✅ Conectividade OK, iniciando coleta incremental...{Colors.RESET}")
            
            # Carregar checkpoint anterior
            last_checkpoint = self._load_checkpoint() if not config.get('force_full') else None
            
            if last_checkpoint and not config.get('force_full'):
                print(f"{Colors.BLUE}🔄 Modo incremental ativo - coletando apenas dados novos...{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}📋 Modo completo - coletando todos os dados...{Colors.RESET}")
            
            # Executar scraping
            all_jobs = await scrape_catho_jobs_multi_mode(
                max_concurrent_jobs=config['concurrent'],
                max_pages=config['pages'],
                multi_mode=config.get('multi_mode', True)
            )
            
            # Processar incrementalmente
            new_jobs, updated_jobs = self._process_incremental_data(all_jobs, last_checkpoint)
            
            # Aplicar limite se especificado
            if config.get('max_new_jobs') and len(new_jobs) > config['max_new_jobs']:
                new_jobs = new_jobs[:config['max_new_jobs']]
                print(f"{Colors.YELLOW}⚠️ Limite atingido: {config['max_new_jobs']} vagas novas{Colors.RESET}")
            
            # Combinar vagas novas e atualizadas
            final_jobs = new_jobs + updated_jobs
            
            # Tempo de execução
            execution_time = datetime.now() - start_time
            
            # Salvar checkpoint
            self._save_checkpoint({
                'timestamp': start_time.isoformat(),
                'strategy': config['strategy_name'],
                'jobs_found': len(all_jobs),
                'new_jobs': len(new_jobs),
                'updated_jobs': len(updated_jobs),
                'execution_time': str(execution_time),
                'config': config
            })
            
            # Atualizar estatísticas
            self._update_stats(len(all_jobs), len(new_jobs), len(updated_jobs))
            
            if final_jobs:
                print(f"\n{Colors.GREEN}🎉 SCRAPING INCREMENTAL CONCLUÍDO!{Colors.RESET}")
                print(f"{Colors.BLUE}{'═' * 60}{Colors.RESET}")
                print(f"📊 Total analisado: {len(all_jobs)} vagas")
                print(f"🆕 Vagas novas: {len(new_jobs)}")
                print(f"🔄 Vagas atualizadas: {len(updated_jobs)}")
                print(f"📋 Total relevante: {len(final_jobs)} vagas")
                print(f"⏱️  Tempo de execução: {execution_time}")
                
                # Calcular eficiência
                efficiency = ((len(new_jobs) + len(updated_jobs)) / len(all_jobs)) * 100 if all_jobs else 0
                print(f"⚡ Eficiência incremental: {efficiency:.1f}%")
                
                # Estatísticas detalhadas
                self._show_incremental_stats(final_jobs, config)
                
                # Salvar automaticamente
                print(f"\n{Colors.YELLOW}💾 Salvando resultados incrementais...{Colors.RESET}")
                save_results(final_jobs, filters_applied={
                    'modo': 'Scraping Incremental',
                    'estrategia': config['strategy_name'],
                    'modalidades': 'Multi' if config.get('multi_mode') else 'Single',
                    'new_jobs': len(new_jobs),
                    'updated_jobs': len(updated_jobs),
                    'efficiency': f"{efficiency:.1f}%"
                }, ask_user_preference=False)
                
                # Mostrar vagas
                print(f"\n{Colors.CYAN}📋 VAGAS INCREMENTAIS:{Colors.RESET}")
                self._show_incremental_jobs_summary(new_jobs, updated_jobs)
                
                # Notificação por email (se configurado)
                if config.get('email_notify'):
                    await self._send_email_notification(len(new_jobs), len(updated_jobs))
                
                # Opções pós-execução
                await self._post_execution_options(final_jobs, config)
                
            else:
                print(f"\n{Colors.YELLOW}ℹ️ NENHUMA NOVIDADE ENCONTRADA{Colors.RESET}")
                print(f"   📊 Total analisado: {len(all_jobs)} vagas")
                print(f"   🔄 Todas as vagas já estavam atualizadas")
                print(f"   ⏰ Última coleta muito recente ou sistema funcionando perfeitamente")
                
                efficiency = 100.0  # Sistema perfeito, nada para coletar
                print(f"   ⚡ Eficiência: {efficiency:.1f}% (sistema otimizado)")
                
                retry = input(f"\n{Colors.YELLOW}Executar coleta completa mesmo assim? [S/N]: {Colors.RESET}").strip().upper()
                if retry in ['S', 'SIM']:
                    config['force_full'] = True
                    await self._execute_incremental_scraping(config)
        
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro durante scraping incremental: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
    
    def _process_incremental_data(self, current_jobs: List[Dict], last_checkpoint: Optional[Dict]) -> tuple:
        """Processa dados incrementalmente, identificando novos e atualizados"""
        if not last_checkpoint:
            # Primeira execução, todas as vagas são novas
            return current_jobs, []
        
        # Carregar dados da última execução para comparação
        last_jobs_file = self._get_last_results_file()
        last_jobs = self._load_last_jobs(last_jobs_file) if last_jobs_file else []
        
        # Criar índice das vagas anteriores
        last_jobs_index = {job.get('link', ''): job for job in last_jobs if job.get('link')}
        
        new_jobs = []
        updated_jobs = []
        
        for job in current_jobs:
            job_link = job.get('link', '')
            
            if job_link not in last_jobs_index:
                # Vaga nova
                new_jobs.append(job)
            else:
                # Verificar se houve atualização
                last_job = last_jobs_index[job_link]
                if self._job_was_updated(job, last_job):
                    updated_jobs.append(job)
        
        return new_jobs, updated_jobs
    
    def _job_was_updated(self, current_job: Dict, last_job: Dict) -> bool:
        """Verifica se uma vaga foi atualizada comparando campos relevantes"""
        # Campos a comparar
        compare_fields = ['titulo', 'empresa', 'salario', 'localizacao', 'regime']
        
        for field in compare_fields:
            if current_job.get(field) != last_job.get(field):
                return True
        
        return False
    
    def _get_last_results_file(self) -> Optional[str]:
        """Encontra o arquivo de resultados mais recente"""
        results_dir = Path("data/resultados/json")
        if not results_dir.exists():
            return None
        
        json_files = list(results_dir.glob("*.json"))
        if not json_files:
            return None
        
        # Retorna o arquivo mais recente
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        return str(latest_file)
    
    def _load_last_jobs(self, file_path: str) -> List[Dict]:
        """Carrega vagas do último arquivo de resultados"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Suporta diferentes formatos de arquivo
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'vagas' in data:
                    return data['vagas']
                else:
                    return []
        except Exception as e:
            print(f"⚠️ Erro ao carregar arquivo anterior: {e}")
            return []
    
    def _load_checkpoint(self) -> Optional[Dict]:
        """Carrega último checkpoint"""
        try:
            if self.checkpoint_file.exists():
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def _save_checkpoint(self, checkpoint_data: Dict) -> None:
        """Salva checkpoint atual"""
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar checkpoint: {e}")
    
    def _load_stats(self) -> Optional[Dict]:
        """Carrega estatísticas históricas"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def _update_stats(self, total_jobs: int, new_jobs: int, updated_jobs: int) -> None:
        """Atualiza estatísticas históricas"""
        try:
            stats = self._load_stats() or {
                'total_runs': 0,
                'total_jobs': 0,
                'total_new_jobs': 0,
                'total_updated_jobs': 0,
                'efficiency_history': []
            }
            
            efficiency = ((new_jobs + updated_jobs) / total_jobs * 100) if total_jobs > 0 else 100
            
            stats['total_runs'] += 1
            stats['total_jobs'] += total_jobs
            stats['total_new_jobs'] += new_jobs
            stats['total_updated_jobs'] += updated_jobs
            stats['efficiency_history'].append(efficiency)
            
            # Manter apenas últimas 50 execuções
            if len(stats['efficiency_history']) > 50:
                stats['efficiency_history'] = stats['efficiency_history'][-50:]
            
            # Calcular média de eficiência
            stats['avg_efficiency'] = sum(stats['efficiency_history']) / len(stats['efficiency_history'])
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao atualizar estatísticas: {e}")
    
    def _show_incremental_stats(self, jobs: List[Dict], config: Dict) -> None:
        """Mostra estatísticas do scraping incremental"""
        print(f"\n📊 ANÁLISE INCREMENTAL:")
        
        # Distribuição por modalidade das vagas relevantes
        mode_counts = {}
        for job in jobs:
            mode = job.get('modalidade_trabalho', job.get('regime', 'Não especificada'))
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        if mode_counts:
            print(f"🌍 MODALIDADES (apenas vagas relevantes):")
            for mode, count in sorted(mode_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(jobs)) * 100
                print(f"   🔹 {mode}: {count} vagas ({percentage:.1f}%)")
        
        # Horário de atividade
        current_hour = datetime.now().hour
        activity_level = "Alta" if 8 <= current_hour <= 18 else "Baixa"
        print(f"\n⏰ ATIVIDADE DO MERCADO:")
        print(f"   🕐 Horário atual: {current_hour}:00")
        print(f"   📈 Nível de atividade: {activity_level}")
    
    def _show_incremental_jobs_summary(self, new_jobs: List[Dict], updated_jobs: List[Dict]) -> None:
        """Mostra resumo das vagas incrementais"""
        print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")
        
        # Mostrar vagas novas
        if new_jobs:
            print(f"\n{Colors.GREEN}🆕 VAGAS NOVAS ({len(new_jobs)}):{Colors.RESET}")
            for i, job in enumerate(new_jobs[:5], 1):
                title = job.get('titulo', 'Título não disponível')[:50]
                company = job.get('empresa', 'Empresa não identificada')[:25]
                mode = job.get('modalidade_trabalho', job.get('regime', 'N/A'))
                
                mode_emoji = {'Home Office': '🏠', 'Presencial': '🏢', 'Híbrido': '🔄'}.get(mode, '📍')
                
                print(f"  {Colors.GREEN}{i:2d}.{Colors.RESET} {title}")
                print(f"      🏢 {company} | {mode_emoji} {mode}")
            
            if len(new_jobs) > 5:
                print(f"      {Colors.GRAY}... e mais {len(new_jobs) - 5} vagas novas{Colors.RESET}")
        
        # Mostrar vagas atualizadas
        if updated_jobs:
            print(f"\n{Colors.BLUE}🔄 VAGAS ATUALIZADAS ({len(updated_jobs)}):{Colors.RESET}")
            for i, job in enumerate(updated_jobs[:3], 1):
                title = job.get('titulo', 'Título não disponível')[:50]
                company = job.get('empresa', 'Empresa não identificada')[:25]
                
                print(f"  {Colors.BLUE}{i:2d}.{Colors.RESET} {title}")
                print(f"      🏢 {company} (dados atualizados)")
            
            if len(updated_jobs) > 3:
                print(f"      {Colors.GRAY}... e mais {len(updated_jobs) - 3} vagas atualizadas{Colors.RESET}")
        
        print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")
    
    async def _send_email_notification(self, new_jobs: int, updated_jobs: int) -> None:
        """Envia notificação por email (futura implementação)"""
        print(f"\n{Colors.BLUE}📧 Enviando notificação por email...{Colors.RESET}")
        print("Implementação futura: integração com SMTP para notificações automáticas.")
    
    async def _post_execution_options(self, jobs: List[Dict], config: Dict) -> None:
        """Opções após a execução"""
        while True:
            print(f"\n{Colors.BLUE}🔄 O QUE FAZER AGORA?{Colors.RESET}")
            print(f"  {Colors.CYAN}[1]{Colors.RESET} 📋 Ver todas as vagas incrementais")
            print(f"  {Colors.CYAN}[2]{Colors.RESET} 📊 Relatório de eficiência incremental")
            print(f"  {Colors.CYAN}[3]{Colors.RESET} 🔄 Executar novo scraping incremental")
            print(f"  {Colors.CYAN}[4]{Colors.RESET} 📅 Agendar execução automática")
            print(f"  {Colors.CYAN}[5]{Colors.RESET} 📁 Abrir pasta de resultados")
            print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (0-5): {Colors.RESET}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self._show_all_incremental_jobs(jobs)
            elif choice == "2":
                self._show_efficiency_report()
            elif choice == "3":
                await self.run_incremental_scraping()
                break
            elif choice == "4":
                await self._schedule_incremental(config)
            elif choice == "5":
                self._open_results_folder()
            else:
                print(f"{Colors.RED}❌ Opção inválida.{Colors.RESET}")
    
    def _show_all_incremental_jobs(self, jobs: List[Dict]) -> None:
        """Mostra todas as vagas incrementais"""
        print(f"\n{Colors.CYAN}📋 TODAS AS VAGAS INCREMENTAIS ({len(jobs)} total){Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 80}{Colors.RESET}")
        
        for i, job in enumerate(jobs, 1):
            title = job.get('titulo', 'Título não disponível')
            company = job.get('empresa', 'Empresa não identificada')
            mode = job.get('modalidade_trabalho', job.get('regime', 'N/A'))
            location = job.get('localizacao', 'Não informada')
            
            print(f"\n{Colors.YELLOW}{i:3d}.{Colors.RESET} {title}")
            print(f"     🏢 {company}")
            print(f"     📍 {mode} - {location}")
            
            if job.get('salario') and job['salario'] != 'Não informado':
                print(f"     💰 {job['salario']}")
            
            if job.get('link'):
                print(f"     🔗 {job['link']}")
            
            # Pausar a cada 5 vagas
            if i % 5 == 0 and i < len(jobs):
                try:
                    response = input(f"\n{Colors.GRAY}[Enter] Continuar | [Q] Parar: {Colors.RESET}").strip().upper()
                    if response == 'Q':
                        break
                except (KeyboardInterrupt, EOFError):
                    break
        
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    def _show_efficiency_report(self) -> None:
        """Mostra relatório de eficiência do sistema incremental"""
        print(f"\n{Colors.CYAN}📊 RELATÓRIO DE EFICIÊNCIA INCREMENTAL{Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 60}{Colors.RESET}")
        
        stats = self._load_stats()
        if stats:
            print(f"🎯 Total de execuções: {stats.get('total_runs', 0)}")
            print(f"📋 Vagas analisadas: {stats.get('total_jobs', 0):,}")
            print(f"🆕 Vagas novas encontradas: {stats.get('total_new_jobs', 0):,}")
            print(f"🔄 Vagas atualizadas: {stats.get('total_updated_jobs', 0):,}")
            print(f"⚡ Eficiência média: {stats.get('avg_efficiency', 0):.1f}%")
            
            # Histórico de eficiência
            if stats.get('efficiency_history'):
                recent_efficiency = stats['efficiency_history'][-5:]
                print(f"\n📈 ÚLTIMAS 5 EXECUÇÕES:")
                for i, eff in enumerate(recent_efficiency, 1):
                    print(f"   {i}. {eff:.1f}%")
        else:
            print("📊 Nenhuma estatística disponível ainda.")
        
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    def _open_results_folder(self) -> None:
        """Abre pasta de resultados"""
        import subprocess
        import platform
        
        results_path = "data/resultados"
        
        try:
            if platform.system() == "Windows":
                os.startfile(results_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", results_path])
            else:
                subprocess.run(["xdg-open", results_path])
            
            print(f"{Colors.GREEN}📁 Pasta de resultados aberta!{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao abrir pasta: {e}{Colors.RESET}")
            print(f"📁 Caminho: {os.path.abspath(results_path)}")


# Função para usar no menu principal
async def run_incremental_scraping():
    """Função principal para scraping incremental"""
    handler = IncrementalScrapingHandler()
    await handler.run_incremental_scraping()