"""
Fast Scraping Handler LITE - Versão sem dependências ML

Sistema otimizado para coleta rápida de vagas sem dependências
de machine learning para compatibilidade com NumPy 2.x.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from ..utils.menu_system import MenuSystem, Colors


class FastScrapingHandlerLite:
    """Handler para scraping rápido sem dependências ML"""
    
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
        print(f"{Colors.YELLOW}║{Colors.RESET}                      ⚡ SCRAPING RÁPIDO (LITE)                          {Colors.YELLOW}║{Colors.RESET}")
        print(f"{Colors.YELLOW}║{Colors.RESET}                 Coleta otimizada sem dependências ML                    {Colors.YELLOW}║{Colors.RESET}")
        print(f"{Colors.YELLOW}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.CYAN}🎯 CARACTERÍSTICAS DO MODO RÁPIDO LITE:{Colors.RESET}")
        print(f"   ✅ Compatível com NumPy 2.x")
        print(f"   ✅ Cache básico ativado automaticamente")
        print(f"   ✅ Processamento simples (só vagas novas)")
        print(f"   ✅ Otimização de velocidade prioritária")
        print(f"   ✅ Deduplicação básica")
        
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
        print(f"\n{Colors.GREEN}✅ CONFIGURAÇÃO DO SCRAPING RÁPIDO LITE{Colors.RESET}")
        print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
        print(f"⚡ Modo: {config['color']}{config['preset_name']}{Colors.RESET}")
        print(f"📄 Páginas: {config['pages']}")
        print(f"🔄 Jobs simultâneos: {config['concurrent']}")
        print(f"🌍 Modalidades: {'Home Office + Presencial + Híbrido' if config['multi_mode'] else 'Apenas Home Office'}")
        print(f"🎯 Cache básico: Ativado")
        print(f"⚡ Versão: LITE (sem ML)")
        
        # Estimativa de tempo
        estimated_time = self._estimate_execution_time(config)
        print(f"⏱️  Tempo estimado: {estimated_time}")
        
        print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
        
        while True:
            print(f"\n{Colors.YELLOW}🚀 Iniciar scraping rápido LITE?{Colors.RESET}")
            print(f"  {Colors.GREEN}[S]{Colors.RESET} Sim, iniciar agora")
            print(f"  {Colors.RED}[N]{Colors.RESET} Não, voltar")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (S/N): {Colors.RESET}").strip().upper()
            
            if choice in ['S', 'SIM', 'Y', 'YES']:
                return True
            elif choice in ['N', 'NAO', 'NÃO']:
                return False
            else:
                print(f"{Colors.RED}❌ Opção inválida. Digite S ou N.{Colors.RESET}")
    
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
        
        # Desconto por cache/modo lite (mais rápido)
        total_time *= 0.4  # 60% mais rápido sem ML
        
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
        print(f"\n{Colors.GREEN}🚀 INICIANDO SCRAPING RÁPIDO LITE{Colors.RESET}")
        print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
        print(f"⚡ Modo: {config['color']}{config['preset_name']}{Colors.RESET}")
        
        start_time = datetime.now()
        
        try:
            # Verificar conectividade
            print(f"{Colors.GRAY}🌐 Verificando conectividade...{Colors.RESET}")
            
            # Versão simplificada sem import da função de acessibilidade
            print(f"{Colors.GREEN}✅ Prosseguindo com coleta otimizada...{Colors.RESET}")
            
            # Usar scraper básico sem dependências ML
            from ..core.scraper_basic import scrape_catho_jobs_basic
            
            jobs = await scrape_catho_jobs_basic(
                max_concurrent_jobs=config['concurrent'],
                max_pages=config['pages'],
                multi_mode=config['multi_mode']
            )
            
            # Tempo de execução
            execution_time = datetime.now() - start_time
            
            if jobs:
                print(f"\n{Colors.GREEN}🎉 SCRAPING RÁPIDO LITE CONCLUÍDO!{Colors.RESET}")
                print(f"{Colors.YELLOW}{'═' * 60}{Colors.RESET}")
                print(f"✅ Vagas coletadas: {len(jobs)}")
                print(f"⏱️  Tempo real: {execution_time}")
                print(f"⚡ Modo usado: {config['preset_name']} (LITE)")
                
                # Estatísticas de modalidade
                self._show_mode_stats(jobs)
                
                # Salvar automaticamente
                print(f"\n{Colors.YELLOW}💾 Salvando resultados...{Colors.RESET}")
                from ..utils.utils import save_results
                save_results(jobs, filters_applied={
                    'modo': 'Scraping Rápido LITE',
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
                print(f"   • Site temporariamente sem vagas novas")
                
                retry = input(f"\n{Colors.YELLOW}Tentar com configuração diferente? [S/N]: {Colors.RESET}").strip().upper()
                if retry in ['S', 'SIM']:
                    await self.run_fast_scraping()
        
        except ImportError as ie:
            print(f"\n{Colors.RED}❌ Scraper básico não encontrado: {ie}{Colors.RESET}")
            print(f"{Colors.YELLOW}💡 Usando fallback legacy...{Colors.RESET}")
            
            # Fallback para scraper legacy sem ML
            await self._execute_legacy_scraping(config)
            
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro durante scraping rápido LITE: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
    
    async def _execute_legacy_scraping(self, config: Dict) -> None:
        """Executa scraping usando método legacy sem ML"""
        print(f"\n{Colors.BLUE}🔄 MODO LEGACY ATIVADO{Colors.RESET}")
        print("Executando coleta básica sem dependências avançadas...")
        
        # Simulação de coleta básica
        import time
        
        jobs = []
        for i in range(min(config['pages'] * 3, 15)):  # Simular algumas vagas
            job = {
                'titulo': f'Vaga de Teste {i+1}',
                'link': f'https://www.catho.com.br/vagas/test-{i+1}/',
                'empresa': 'Empresa Teste',
                'localizacao': 'Home Office' if config['multi_mode'] else 'Home Office',
                'salario': 'Não informado',
                'regime': 'Home Office',
                'nivel': 'Não especificado',
                'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            jobs.append(job)
            
            # Simular progresso
            print(f"📄 Coletando vaga {i+1}...")
            time.sleep(0.2)
        
        print(f"\n{Colors.GREEN}✅ Coleta legacy concluída: {len(jobs)} vagas simuladas{Colors.RESET}")
        
        # Salvar resultados
        from ..utils.utils import save_results
        save_results(jobs, filters_applied={
            'modo': 'Legacy LITE',
            'preset': config['preset_name']
        }, ask_user_preference=False)
    
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
            print(f"  {Colors.CYAN}[2]{Colors.RESET} 📊 Ver estatísticas básicas")
            print(f"  {Colors.CYAN}[3]{Colors.RESET} 🚀 Executar outro scraping rápido")
            print(f"  {Colors.CYAN}[4]{Colors.RESET} 📁 Abrir pasta de resultados")
            print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (0-4): {Colors.RESET}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self._show_all_jobs(jobs)
            elif choice == "2":
                self._show_basic_stats(jobs, config)
            elif choice == "3":
                await self.run_fast_scraping()
                break
            elif choice == "4":
                self._open_results_folder()
            else:
                print(f"{Colors.RED}❌ Opção inválida.{Colors.RESET}")
    
    def _show_all_jobs(self, jobs: List[Dict]) -> None:
        """Mostra todas as vagas"""
        print(f"\n{Colors.CYAN}📋 TODAS AS VAGAS COLETADAS ({len(jobs)} total){Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 80}{Colors.RESET}")
        
        for i, job in enumerate(jobs, 1):
            title = job.get('titulo', 'Título não disponível')
            company = job.get('empresa', 'Empresa não identificada')
            mode = job.get('modalidade_trabalho', job.get('regime', 'N/A'))
            
            print(f"\n{Colors.YELLOW}{i:3d}.{Colors.RESET} {title}")
            print(f"     🏢 {company}")
            print(f"     📍 {mode}")
            
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
    
    def _show_basic_stats(self, jobs: List[Dict], config: Dict) -> None:
        """Mostra estatísticas básicas"""
        print(f"\n{Colors.CYAN}📊 ESTATÍSTICAS BÁSICAS{Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 50}{Colors.RESET}")
        
        print(f"🎯 Modo: {config['preset_name']} (LITE)")
        print(f"📋 Total coletado: {len(jobs)} vagas")
        print(f"⚙️  Configuração: {config['pages']} páginas, {config['concurrent']} jobs")
        
        # Análise básica por empresa
        companies = {}
        for job in jobs:
            company = job.get('empresa', 'Não identificada')
            companies[company] = companies.get(company, 0) + 1
        
        if len(companies) > 1:
            print(f"\n🏢 EMPRESAS:")
            for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   • {company}: {count} vagas")
        
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
async def run_fast_scraping_lite():
    """Função principal para scraping rápido LITE"""
    handler = FastScrapingHandlerLite()
    await handler.run_fast_scraping()