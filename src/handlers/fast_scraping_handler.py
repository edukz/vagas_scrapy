"""
Fast Scraping Handler - Interface Modernizada para Scraping Rápido

Sistema otimizado para coleta rápida de vagas com cache inteligente
e processamento incremental ativado por padrão.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from ..core.scraper_multi_mode import scrape_catho_jobs_multi_mode, check_catho_accessibility
from ..utils.utils import save_results
from ..utils.menu_system import MenuSystem, Colors


class FastScrapingHandler:
    """Handler para scraping rápido com interface modernizada"""
    
    def __init__(self):
        self.menu = MenuSystem()
        
        # Presets otimizados para velocidade
        self.speed_presets = {
            "🚀 Turbo": {
                "description": "Máxima velocidade - ideal para atualizações rápidas",
                "pages": 10,
                "concurrent": 15,
                "multi_mode": False,
                "color": Colors.RED
            },
            "⚡ Express": {
                "description": "Velocidade alta com boa cobertura",
                "pages": 20,
                "concurrent": 12,
                "multi_mode": True,
                "color": Colors.YELLOW
            },
            "🎯 Focado": {
                "description": "Velocidade otimizada para áreas específicas",
                "pages": 15,
                "concurrent": 10,
                "multi_mode": False,
                "color": Colors.CYAN
            },
            "🌐 Completo": {
                "description": "Cobertura total em todas as modalidades",
                "pages": 30,
                "concurrent": 8,
                "multi_mode": True,
                "color": Colors.GREEN
            }
        }
    
    async def run_fast_scraping(self) -> None:
        """Interface principal do scraping rápido"""
        print(f"\n{Colors.YELLOW}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.YELLOW}║{Colors.RESET}                        ⚡ SCRAPING RÁPIDO                              {Colors.YELLOW}║{Colors.RESET}")
        print(f"{Colors.YELLOW}║{Colors.RESET}                 Coleta otimizada com cache inteligente                   {Colors.YELLOW}║{Colors.RESET}")
        print(f"{Colors.YELLOW}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.CYAN}🎯 CARACTERÍSTICAS DO MODO RÁPIDO:{Colors.RESET}")
        print(f"   ✅ Cache inteligente ativado automaticamente")
        print(f"   ✅ Processamento incremental (só vagas novas)")
        print(f"   ✅ Otimização de velocidade prioritária")
        print(f"   ✅ Deduplicação automática")
        
        # Seleção de preset
        preset_config = await self._select_speed_preset()
        if not preset_config:
            return
        
        # Confirmação
        if await self._confirm_fast_execution(preset_config):
            await self._execute_fast_scraping(preset_config)
    
    async def _select_speed_preset(self) -> Optional[Dict]:
        """Seleção de preset de velocidade"""
        print(f"\n{Colors.YELLOW}⚡ ESCOLHA O MODO DE VELOCIDADE:{Colors.RESET}")
        print(f"   {Colors.GRAY}Cada modo é otimizado para diferentes necessidades{Colors.RESET}\n")
        
        options = list(self.speed_presets.keys())
        
        for i, (name, config) in enumerate(self.speed_presets.items(), 1):
            color = config['color']
            print(f"  {Colors.CYAN}[{i}]{Colors.RESET} {color}{name}{Colors.RESET}")
            print(f"     {Colors.GRAY}{config['description']}{Colors.RESET}")
            print(f"     📄 {config['pages']} páginas | 🔄 {config['concurrent']} jobs | 🌍 {'Multi' if config['multi_mode'] else 'Single'} modalidade")
            print()
        
        print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal\n")
        
        try:
            choice = input(f"{Colors.YELLOW}➤ Sua escolha (1-{len(options)}): {Colors.RESET}").strip()
            
            if choice == "0":
                return None
                
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                selected_key = options[choice_idx]
                config = self.speed_presets[selected_key].copy()
                config['preset_name'] = selected_key
                return config
            else:
                print(f"{Colors.RED}❌ Opção inválida. Tente novamente.{Colors.RESET}")
                return await self._select_speed_preset()
                
        except (ValueError, KeyboardInterrupt):
            print(f"{Colors.RED}❌ Entrada inválida.{Colors.RESET}")
            return await self._select_speed_preset()
    
    async def _confirm_fast_execution(self, config: Dict) -> bool:
        """Confirmação antes da execução"""
        print(f"\n{Colors.GREEN}✅ CONFIGURAÇÃO DO SCRAPING RÁPIDO{Colors.RESET}")
        print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
        print(f"⚡ Modo: {config['color']}{config['preset_name']}{Colors.RESET}")
        print(f"📄 Páginas: {config['pages']}")
        print(f"🔄 Jobs simultâneos: {config['concurrent']}")
        print(f"🌍 Modalidades: {'Home Office + Presencial + Híbrido' if config['multi_mode'] else 'Apenas Home Office'}")
        print(f"🎯 Cache inteligente: Ativado")
        print(f"⚡ Processamento incremental: Ativado")
        print(f"🧹 Deduplicação: Ativada")
        
        # Estimativa de tempo
        estimated_time = self._estimate_execution_time(config)
        print(f"⏱️  Tempo estimado: {estimated_time}")
        
        print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
        
        while True:
            print(f"\n{Colors.YELLOW}🚀 Iniciar scraping rápido?{Colors.RESET}")
            print(f"  {Colors.GREEN}[S]{Colors.RESET} Sim, iniciar agora")
            print(f"  {Colors.RED}[N]{Colors.RESET} Não, voltar")
            print(f"  {Colors.CYAN}[C]{Colors.RESET} Configuração personalizada")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (S/N/C): {Colors.RESET}").strip().upper()
            
            if choice in ['S', 'SIM', 'Y', 'YES']:
                return True
            elif choice in ['N', 'NAO', 'NÃO']:
                return False
            elif choice in ['C', 'CONFIG']:
                await self._customize_config(config)
                return True
            else:
                print(f"{Colors.RED}❌ Opção inválida. Digite S, N ou C.{Colors.RESET}")
    
    async def _customize_config(self, config: Dict) -> None:
        """Permite personalização da configuração"""
        print(f"\n{Colors.CYAN}⚙️ CONFIGURAÇÃO PERSONALIZADA{Colors.RESET}")
        print(f"   {Colors.GRAY}Pressione Enter para manter o valor atual:{Colors.RESET}\n")
        
        # Páginas
        current_pages = config['pages']
        new_pages = input(f"📄 Páginas ({current_pages}): ").strip()
        if new_pages and new_pages.isdigit():
            config['pages'] = int(new_pages)
        
        # Jobs simultâneos
        current_concurrent = config['concurrent']
        new_concurrent = input(f"🔄 Jobs simultâneos ({current_concurrent}): ").strip()
        if new_concurrent and new_concurrent.isdigit():
            config['concurrent'] = int(new_concurrent)
        
        # Multi-modalidade
        current_multi = "Sim" if config['multi_mode'] else "Não"
        new_multi = input(f"🌍 Buscar todas as modalidades ({current_multi}) [S/N]: ").strip().upper()
        if new_multi in ['S', 'N']:
            config['multi_mode'] = new_multi == 'S'
        
        print(f"\n{Colors.GREEN}✅ Configuração personalizada aplicada!{Colors.RESET}")
    
    def _estimate_execution_time(self, config: Dict) -> str:
        """Estima tempo de execução"""
        pages = config['pages']
        concurrent = config['concurrent']
        
        # Tempo base (modo rápido = mais agressivo)
        time_per_page = 1.5  # Mais rápido que o modo normal
        
        # Multiplicador para multi-modalidade
        if config['multi_mode']:
            time_per_page *= 2.5  # 3 modalidades, mas com paralelismo
        
        # Ajuste para paralelismo
        total_time = (pages * time_per_page) / max(1, concurrent * 0.8)
        
        # Desconto por cache/incremental (modo rápido)
        total_time *= 0.3  # 70% mais rápido com otimizações
        
        if total_time < 60:
            return f"{int(total_time)} segundos"
        elif total_time < 3600:
            return f"{int(total_time // 60)} minutos"
        else:
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            return f"{hours}h {minutes}min"
    
    async def _execute_fast_scraping(self, config: Dict) -> None:
        """Executa o scraping rápido"""
        print(f"\n{Colors.GREEN}🚀 INICIANDO SCRAPING RÁPIDO{Colors.RESET}")
        print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
        print(f"⚡ Modo: {config['color']}{config['preset_name']}{Colors.RESET}")
        
        start_time = datetime.now()
        
        try:
            # Verificar conectividade
            print(f"{Colors.GRAY}🌐 Verificando conectividade...{Colors.RESET}")
            is_accessible = await check_catho_accessibility()
            
            if not is_accessible:
                print(f"{Colors.RED}❌ Site não acessível. Tente novamente em alguns minutos.{Colors.RESET}")
                return
            
            print(f"{Colors.GREEN}✅ Conectividade OK, iniciando coleta otimizada...{Colors.RESET}")
            
            # Executar scraping
            try:
                jobs = await scrape_catho_jobs_multi_mode(
                    max_concurrent_jobs=config['concurrent'],
                    max_pages=config['pages'],
                    multi_mode=config['multi_mode']
                )
            except Exception as scraping_error:
                print(f"{Colors.YELLOW}⚠️ Erro no scraper principal: {scraping_error}{Colors.RESET}")
                print(f"{Colors.BLUE}🔄 Tentando scraper alternativo...{Colors.RESET}")
                
                # Fallback para versão LITE
                from .fast_scraping_handler_lite import FastScrapingHandlerLite
                lite_handler = FastScrapingHandlerLite()
                await lite_handler._execute_legacy_scraping(config)
                return
            
            # Tempo de execução
            execution_time = datetime.now() - start_time
            
            if jobs:
                print(f"\n{Colors.GREEN}🎉 SCRAPING RÁPIDO CONCLUÍDO!{Colors.RESET}")
                print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
                print(f"✅ Vagas coletadas: {len(jobs)}")
                print(f"⏱️  Tempo real: {execution_time}")
                print(f"⚡ Modo usado: {config['preset_name']}")
                
                # Estatísticas de modalidade
                self._show_mode_stats(jobs)
                
                # Salvar automaticamente
                print(f"\n{Colors.YELLOW}💾 Salvando resultados...{Colors.RESET}")
                save_results(jobs, filters_applied={
                    'modo': 'Scraping Rápido',
                    'preset': config['preset_name'],
                    'modalidades': 'Multi' if config['multi_mode'] else 'Single',
                    'pages': config['pages']
                }, ask_user_preference=False)
                
                # Mostrar vagas
                print(f"\n{Colors.CYAN}📋 VAGAS COLETADAS:{Colors.RESET}")
                self._show_jobs_summary(jobs)
                
                # Opções pós-execução
                await self._post_execution_options(jobs, config)
                
            else:
                print(f"\n{Colors.YELLOW}⚠️ Nenhuma vaga nova encontrada{Colors.RESET}")
                print(f"   {Colors.GRAY}Possíveis causas:{Colors.RESET}")
                print(f"   • Cache muito recente (todas as vagas já coletadas)")
                print(f"   • Processamento incremental funcionando perfeitamente")
                print(f"   • Site temporariamente sem vagas novas")
                
                retry = input(f"\n{Colors.YELLOW}Tentar com configuração diferente? [S/N]: {Colors.RESET}").strip().upper()
                if retry in ['S', 'SIM']:
                    await self.run_fast_scraping()
        
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro durante scraping rápido: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
    
    def _show_mode_stats(self, jobs: List[Dict]) -> None:
        """Mostra estatísticas por modalidade"""
        mode_counts = {}
        for job in jobs:
            mode = job.get('modalidade_trabalho', job.get('regime', 'Não especificada'))
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        if len(mode_counts) > 1:
            print(f"\n📊 DISTRIBUIÇÃO POR MODALIDADE:")
            for mode, count in sorted(mode_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(jobs)) * 100
                print(f"   🔹 {mode}: {count} vagas ({percentage:.1f}%)")
    
    def _show_jobs_summary(self, jobs: List[Dict], limit: int = 10) -> None:
        """Mostra resumo das vagas coletadas"""
        print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")
        
        for i, job in enumerate(jobs[:limit], 1):
            title = job.get('titulo', 'Título não disponível')[:50]
            company = job.get('empresa', 'Empresa não identificada')[:25]
            mode = job.get('modalidade_trabalho', job.get('regime', 'N/A'))
            
            # Emoji por modalidade
            mode_emoji = {
                'Home Office': '🏠',
                'Presencial': '🏢',
                'Híbrido': '🔄'
            }.get(mode, '📍')
            
            print(f"{Colors.YELLOW}{i:2d}.{Colors.RESET} {title}")
            print(f"    🏢 {company} | {mode_emoji} {mode}")
        
        if len(jobs) > limit:
            print(f"\n{Colors.GRAY}... e mais {len(jobs) - limit} vagas (veja todas na opção 9 - Visualizar Vagas){Colors.RESET}")
        
        print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")
    
    async def _post_execution_options(self, jobs: List[Dict], config: Dict) -> None:
        """Opções após a execução"""
        while True:
            print(f"\n{Colors.YELLOW}⚡ O QUE FAZER AGORA?{Colors.RESET}")
            print(f"  {Colors.CYAN}[1]{Colors.RESET} 📋 Ver todas as vagas coletadas")
            print(f"  {Colors.CYAN}[2]{Colors.RESET} 📊 Ver estatísticas detalhadas")
            print(f"  {Colors.CYAN}[3]{Colors.RESET} 🚀 Executar outro scraping rápido")
            print(f"  {Colors.CYAN}[4]{Colors.RESET} 📁 Abrir pasta de resultados")
            print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (0-4): {Colors.RESET}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self._show_all_jobs_detailed(jobs)
            elif choice == "2":
                self._show_detailed_statistics(jobs, config)
            elif choice == "3":
                await self.run_fast_scraping()
                break
            elif choice == "4":
                self._open_results_folder()
            else:
                print(f"{Colors.RED}❌ Opção inválida.{Colors.RESET}")
    
    def _show_all_jobs_detailed(self, jobs: List[Dict]) -> None:
        """Mostra todas as vagas de forma detalhada"""
        print(f"\n{Colors.CYAN}📋 TODAS AS VAGAS COLETADAS ({len(jobs)} total){Colors.RESET}")
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
    
    def _show_detailed_statistics(self, jobs: List[Dict], config: Dict) -> None:
        """Mostra estatísticas detalhadas"""
        print(f"\n{Colors.CYAN}📊 ESTATÍSTICAS DETALHADAS{Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 50}{Colors.RESET}")
        
        print(f"🎯 Modo: {config['preset_name']}")
        print(f"📋 Total coletado: {len(jobs)} vagas")
        print(f"⚙️  Configuração: {config['pages']} páginas, {config['concurrent']} jobs")
        
        # Análise por empresa
        companies = {}
        for job in jobs:
            company = job.get('empresa', 'Não identificada')
            companies[company] = companies.get(company, 0) + 1
        
        print(f"\n🏢 TOP EMPRESAS:")
        for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   • {company}: {count} vagas")
        
        # Análise por modalidade
        modes = {}
        for job in jobs:
            mode = job.get('modalidade_trabalho', job.get('regime', 'N/A'))
            modes[mode] = modes.get(mode, 0) + 1
        
        print(f"\n🌍 MODALIDADES:")
        for mode, count in modes.items():
            percentage = (count / len(jobs)) * 100
            print(f"   • {mode}: {count} vagas ({percentage:.1f}%)")
        
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    def _open_results_folder(self) -> None:
        """Abre pasta de resultados"""
        import os
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
async def run_fast_scraping():
    """Função principal para scraping rápido"""
    handler = FastScrapingHandler()
    await handler.run_fast_scraping()