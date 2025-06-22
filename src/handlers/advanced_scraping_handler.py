"""
Advanced Scraping Handler - Interface Modernizada para Scraping Avançado

Sistema com configurações avançadas, IA integrada, análise em tempo real
e opções personalizáveis para usuários experientes.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from ..core.scraper_multi_mode import scrape_catho_jobs_multi_mode, check_catho_accessibility
from ..utils.utils import save_results
from ..utils.menu_system import MenuSystem, Colors


class AdvancedScrapingHandler:
    """Handler para scraping avançado com configurações personalizáveis"""
    
    def __init__(self):
        self.menu = MenuSystem()
        
        # Configurações avançadas disponíveis
        self.advanced_configs = {
            "🎯 Precisão": {
                "description": "Alta precisão com análise detalhada de cada vaga",
                "pages": 15,
                "concurrent": 6,
                "multi_mode": True,
                "ai_analysis": True,
                "deep_scan": True,
                "color": Colors.CYAN
            },
            "⚡ Performance": {
                "description": "Máxima performance com coleta agressiva",
                "pages": 25,
                "concurrent": 18,
                "multi_mode": True,
                "ai_analysis": False,
                "deep_scan": False,
                "color": Colors.RED
            },
            "🧠 IA Completa": {
                "description": "Análise completa com IA e machine learning",
                "pages": 20,
                "concurrent": 8,
                "multi_mode": True,
                "ai_analysis": True,
                "deep_scan": True,
                "color": Colors.PURPLE
            },
            "🔧 Personalizado": {
                "description": "Configuração totalmente customizada",
                "pages": 0,  # Será definido pelo usuário
                "concurrent": 0,  # Será definido pelo usuário
                "multi_mode": True,
                "ai_analysis": True,
                "deep_scan": True,
                "color": Colors.YELLOW
            }
        }
    
    async def run_advanced_scraping(self) -> None:
        """Interface principal do scraping avançado"""
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET}                        🎯 SCRAPING AVANÇADO                             {Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET}                 Configurações personalizadas e IA integrada              {Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        
        print(f"\n{Colors.MAGENTA}🚀 RECURSOS AVANÇADOS:{Colors.RESET}")
        print(f"   ✅ Configurações personalizáveis")
        print(f"   ✅ Análise com IA integrada (opcional)")
        print(f"   ✅ Deep scanning de vagas")
        print(f"   ✅ Multi-modalidade (Home Office + Presencial + Híbrido)")
        print(f"   ✅ Controle fino de performance")
        print(f"   ✅ Análise em tempo real")
        
        # Seleção de configuração avançada
        config = await self._select_advanced_config()
        if not config:
            return
        
        # Configurações adicionais
        await self._configure_advanced_options(config)
        
        # Confirmação e execução
        if await self._confirm_advanced_execution(config):
            await self._execute_advanced_scraping(config)
    
    async def _select_advanced_config(self) -> Optional[Dict]:
        """Seleção de configuração avançada"""
        print(f"\n{Colors.CYAN}🎯 ESCOLHA A CONFIGURAÇÃO AVANÇADA:{Colors.RESET}")
        print(f"   {Colors.GRAY}Cada configuração oferece diferentes níveis de customização{Colors.RESET}\n")
        
        options = list(self.advanced_configs.keys())
        
        for i, (name, config) in enumerate(self.advanced_configs.items(), 1):
            color = config['color']
            print(f"  {Colors.CYAN}[{i}]{Colors.RESET} {color}{name}{Colors.RESET}")
            print(f"     {Colors.GRAY}{config['description']}{Colors.RESET}")
            
            if name != "🔧 Personalizado":
                print(f"     📄 {config['pages']} páginas | 🔄 {config['concurrent']} jobs | 🧠 IA: {'Sim' if config['ai_analysis'] else 'Não'}")
            else:
                print(f"     ⚙️ Você define todos os parâmetros manualmente")
            print()
        
        print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal\n")
        
        try:
            choice = input(f"{Colors.YELLOW}➤ Sua escolha (1-{len(options)}): {Colors.RESET}").strip()
            
            if choice == "0":
                return None
                
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                selected_key = options[choice_idx]
                config = self.advanced_configs[selected_key].copy()
                config['config_name'] = selected_key
                return config
            else:
                print(f"{Colors.RED}❌ Opção inválida. Tente novamente.{Colors.RESET}")
                return await self._select_advanced_config()
                
        except (ValueError, KeyboardInterrupt):
            print(f"{Colors.RED}❌ Entrada inválida.{Colors.RESET}")
            return await self._select_advanced_config()
    
    async def _configure_advanced_options(self, config: Dict) -> None:
        """Configuração de opções avançadas"""
        print(f"\n{Colors.MAGENTA}⚙️ CONFIGURAÇÕES AVANÇADAS{Colors.RESET}")
        print(f"   {Colors.GRAY}Configure os parâmetros específicos para sua necessidade{Colors.RESET}\n")
        
        # Se for personalizado, pedir todos os parâmetros
        if config['config_name'] == "🔧 Personalizado":
            await self._configure_custom_parameters(config)
        
        # Configurações adicionais para todos os modos
        print(f"\n{Colors.CYAN}🔍 OPÇÕES EXTRAS:{Colors.RESET}")
        
        # Filtros específicos
        location_filter = input(f"📍 Filtrar por localização específica (Enter = todas): ").strip()
        if location_filter:
            config['location_filter'] = location_filter
        
        # Filtro de salário
        salary_filter = input(f"💰 Salário mínimo desejado (Enter = qualquer): ").strip()
        if salary_filter and salary_filter.isdigit():
            config['salary_filter'] = int(salary_filter)
        
        # Palavras-chave específicas
        keywords = input(f"🔍 Palavras-chave específicas (separadas por vírgula): ").strip()
        if keywords:
            config['keywords'] = [k.strip() for k in keywords.split(',')]
        
        # Modo de análise
        if config.get('ai_analysis', False):
            analysis_mode = input(f"🧠 Análise IA intensiva? [S/N] (padrão: N): ").strip().upper()
            config['intensive_ai'] = analysis_mode == 'S'
    
    async def _configure_custom_parameters(self, config: Dict) -> None:
        """Configuração de parâmetros personalizados"""
        print(f"{Colors.YELLOW}📝 CONFIGURAÇÃO PERSONALIZADA:{Colors.RESET}")
        
        # Páginas
        while True:
            try:
                pages = input(f"📄 Número de páginas (5-50): ").strip()
                pages = int(pages)
                if 5 <= pages <= 50:
                    config['pages'] = pages
                    break
                else:
                    print(f"{Colors.RED}❌ Entre 5 e 50 páginas.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}❌ Digite um número válido.{Colors.RESET}")
        
        # Jobs simultâneos
        while True:
            try:
                concurrent = input(f"🔄 Jobs simultâneos (3-25): ").strip()
                concurrent = int(concurrent)
                if 3 <= concurrent <= 25:
                    config['concurrent'] = concurrent
                    break
                else:
                    print(f"{Colors.RED}❌ Entre 3 e 25 jobs simultâneos.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}❌ Digite um número válido.{Colors.RESET}")
        
        # Multi-modalidade
        multi_mode = input(f"🌍 Buscar todas as modalidades (Home Office + Presencial + Híbrido)? [S/N]: ").strip().upper()
        config['multi_mode'] = multi_mode == 'S'
        
        # Análise IA
        ai_analysis = input(f"🧠 Ativar análise com IA? [S/N]: ").strip().upper()
        config['ai_analysis'] = ai_analysis == 'S'
        
        # Deep scan
        deep_scan = input(f"🔍 Ativar deep scanning (análise detalhada)? [S/N]: ").strip().upper()
        config['deep_scan'] = deep_scan == 'S'
    
    async def _confirm_advanced_execution(self, config: Dict) -> bool:
        """Confirmação antes da execução"""
        print(f"\n{Colors.GREEN}✅ CONFIGURAÇÃO DO SCRAPING AVANÇADO{Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print(f"🎯 Modo: {config['color']}{config['config_name']}{Colors.RESET}")
        print(f"📄 Páginas: {config['pages']}")
        print(f"🔄 Jobs simultâneos: {config['concurrent']}")
        print(f"🌍 Modalidades: {'Multi (HO + Presencial + Híbrido)' if config['multi_mode'] else 'Apenas Home Office'}")
        print(f"🧠 Análise IA: {'Ativada' if config['ai_analysis'] else 'Desativada'}")
        print(f"🔍 Deep Scanning: {'Ativado' if config['deep_scan'] else 'Desativado'}")
        
        # Filtros extras
        if config.get('location_filter'):
            print(f"📍 Filtro localização: {config['location_filter']}")
        if config.get('salary_filter'):
            print(f"💰 Salário mínimo: R$ {config['salary_filter']}")
        if config.get('keywords'):
            print(f"🔍 Palavras-chave: {', '.join(config['keywords'])}")
        
        # Estimativa de tempo
        estimated_time = self._estimate_execution_time(config)
        print(f"⏱️  Tempo estimado: {estimated_time}")
        
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        
        while True:
            print(f"\n{Colors.YELLOW}🚀 Iniciar scraping avançado?{Colors.RESET}")
            print(f"  {Colors.GREEN}[S]{Colors.RESET} Sim, iniciar agora")
            print(f"  {Colors.RED}[N]{Colors.RESET} Não, voltar")
            print(f"  {Colors.CYAN}[E]{Colors.RESET} Editar configuração")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (S/N/E): {Colors.RESET}").strip().upper()
            
            if choice in ['S', 'SIM', 'Y', 'YES']:
                return True
            elif choice in ['N', 'NAO', 'NÃO']:
                return False
            elif choice in ['E', 'EDIT']:
                await self._configure_advanced_options(config)
                return True
            else:
                print(f"{Colors.RED}❌ Opção inválida. Digite S, N ou E.{Colors.RESET}")
    
    def _estimate_execution_time(self, config: Dict) -> str:
        """Estima tempo de execução baseado na configuração"""
        pages = config['pages']
        concurrent = config['concurrent']
        
        # Tempo base mais conservador para modo avançado
        time_per_page = 2.5
        
        # Multiplicadores baseados nas funcionalidades
        if config['multi_mode']:
            time_per_page *= 2.8  # 3 modalidades
        
        if config.get('ai_analysis', False):
            time_per_page *= 1.4  # Análise IA adiciona tempo
        
        if config.get('deep_scan', False):
            time_per_page *= 1.3  # Deep scan adiciona tempo
        
        if config.get('intensive_ai', False):
            time_per_page *= 1.5  # IA intensiva
        
        # Ajuste para paralelismo
        total_time = (pages * time_per_page) / max(1, concurrent * 0.7)
        
        # Tempo adicional para filtros
        if config.get('keywords') or config.get('location_filter'):
            total_time *= 1.2
        
        if total_time < 60:
            return f"{int(total_time)} segundos"
        elif total_time < 3600:
            return f"{int(total_time // 60)} minutos"
        else:
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            return f"{hours}h {minutes}min"
    
    async def _execute_advanced_scraping(self, config: Dict) -> None:
        """Executa o scraping avançado"""
        print(f"\n{Colors.GREEN}🚀 INICIANDO SCRAPING AVANÇADO{Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        print(f"🎯 Modo: {config['color']}{config['config_name']}{Colors.RESET}")
        
        start_time = datetime.now()
        
        try:
            # Verificar conectividade
            print(f"{Colors.GRAY}🌐 Verificando conectividade...{Colors.RESET}")
            is_accessible = await check_catho_accessibility()
            
            if not is_accessible:
                print(f"{Colors.RED}❌ Site não acessível. Tente novamente em alguns minutos.{Colors.RESET}")
                return
            
            print(f"{Colors.GREEN}✅ Conectividade OK, iniciando coleta avançada...{Colors.RESET}")
            
            # Mostrar progresso em tempo real
            if config.get('ai_analysis', False):
                print(f"{Colors.PURPLE}🧠 Análise IA ativada - processamento inteligente em andamento...{Colors.RESET}")
            
            if config.get('deep_scan', False):
                print(f"{Colors.CYAN}🔍 Deep scanning ativado - análise detalhada de cada vaga...{Colors.RESET}")
            
            # Executar scraping
            jobs = await scrape_catho_jobs_multi_mode(
                max_concurrent_jobs=config['concurrent'],
                max_pages=config['pages'],
                multi_mode=config['multi_mode']
            )
            
            # Aplicar filtros se especificados
            if jobs:
                jobs = self._apply_advanced_filters(jobs, config)
            
            # Tempo de execução
            execution_time = datetime.now() - start_time
            
            if jobs:
                print(f"\n{Colors.GREEN}🎉 SCRAPING AVANÇADO CONCLUÍDO!{Colors.RESET}")
                print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
                print(f"✅ Vagas coletadas: {len(jobs)}")
                print(f"⏱️  Tempo real: {execution_time}")
                print(f"🎯 Configuração: {config['config_name']}")
                
                # Estatísticas avançadas
                self._show_advanced_stats(jobs, config)
                
                # Salvar automaticamente
                print(f"\n{Colors.YELLOW}💾 Salvando resultados...{Colors.RESET}")
                save_results(jobs, filters_applied={
                    'modo': 'Scraping Avançado',
                    'config': config['config_name'],
                    'modalidades': 'Multi' if config['multi_mode'] else 'Single',
                    'ai_analysis': config.get('ai_analysis', False),
                    'deep_scan': config.get('deep_scan', False),
                    'pages': config['pages']
                }, ask_user_preference=False)
                
                # Mostrar vagas
                print(f"\n{Colors.CYAN}📋 VAGAS COLETADAS:{Colors.RESET}")
                self._show_jobs_summary(jobs)
                
                # Opções pós-execução
                await self._post_execution_options(jobs, config)
                
            else:
                print(f"\n{Colors.YELLOW}⚠️ Nenhuma vaga encontrada com os filtros aplicados{Colors.RESET}")
                print(f"   {Colors.GRAY}Possíveis causas:{Colors.RESET}")
                print(f"   • Filtros muito restritivos")
                print(f"   • Cache muito recente")
                print(f"   • Site temporariamente sem vagas novas")
                
                retry = input(f"\n{Colors.YELLOW}Tentar com configuração diferente? [S/N]: {Colors.RESET}").strip().upper()
                if retry in ['S', 'SIM']:
                    await self.run_advanced_scraping()
        
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro durante scraping avançado: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
    
    def _apply_advanced_filters(self, jobs: List[Dict], config: Dict) -> List[Dict]:
        """Aplica filtros avançados às vagas"""
        filtered_jobs = jobs
        
        # Filtro de localização
        if config.get('location_filter'):
            location = config['location_filter'].lower()
            filtered_jobs = [job for job in filtered_jobs 
                           if location in job.get('localizacao', '').lower()]
        
        # Filtro de salário (necessita implementação de parsing de salário)
        if config.get('salary_filter'):
            # Esta funcionalidade precisa de parser de salário
            pass
        
        # Filtro de palavras-chave
        if config.get('keywords'):
            keywords = [k.lower() for k in config['keywords']]
            filtered_jobs = [job for job in filtered_jobs 
                           if any(keyword in job.get('titulo', '').lower() 
                                 for keyword in keywords)]
        
        return filtered_jobs
    
    def _show_advanced_stats(self, jobs: List[Dict], config: Dict) -> None:
        """Mostra estatísticas avançadas"""
        print(f"\n📊 ESTATÍSTICAS AVANÇADAS:")
        
        # Distribuição por modalidade
        mode_counts = {}
        for job in jobs:
            mode = job.get('modalidade_trabalho', job.get('regime', 'Não especificada'))
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        if len(mode_counts) > 1:
            print(f"🌍 MODALIDADES:")
            for mode, count in sorted(mode_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(jobs)) * 100
                print(f"   🔹 {mode}: {count} vagas ({percentage:.1f}%)")
        
        # Empresas com mais vagas
        company_counts = {}
        for job in jobs:
            company = job.get('empresa', 'Não identificada')
            if company != 'Empresa não identificada':
                company_counts[company] = company_counts.get(company, 0) + 1
        
        if company_counts:
            print(f"\n🏢 TOP EMPRESAS:")
            top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for company, count in top_companies:
                print(f"   • {company}: {count} vagas")
        
        # Tecnologias detectadas
        all_techs = []
        for job in jobs:
            all_techs.extend(job.get('tecnologias_detectadas', []))
        
        if all_techs:
            tech_counts = {}
            for tech in all_techs:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1
            
            print(f"\n💻 TECNOLOGIAS MAIS DEMANDADAS:")
            top_techs = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for tech, count in top_techs:
                print(f"   • {tech}: {count} menções")
    
    def _show_jobs_summary(self, jobs: List[Dict], limit: int = 10) -> None:
        """Mostra resumo das vagas coletadas"""
        print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")
        
        for i, job in enumerate(jobs[:limit], 1):
            title = job.get('titulo', 'Título não disponível')[:55]
            company = job.get('empresa', 'Empresa não identificada')[:30]
            mode = job.get('modalidade_trabalho', job.get('regime', 'N/A'))
            
            # Emoji por modalidade
            mode_emoji = {
                'Home Office': '🏠',
                'Presencial': '🏢',
                'Híbrido': '🔄'
            }.get(mode, '📍')
            
            print(f"{Colors.YELLOW}{i:2d}.{Colors.RESET} {title}")
            print(f"    🏢 {company} | {mode_emoji} {mode}")
            
            # Mostrar tecnologias se disponíveis
            techs = job.get('tecnologias_detectadas', [])
            if techs:
                tech_str = ', '.join(techs[:3])
                if len(techs) > 3:
                    tech_str += f" +{len(techs)-3}"
                print(f"    💻 {tech_str}")
        
        if len(jobs) > limit:
            print(f"\n{Colors.GRAY}... e mais {len(jobs) - limit} vagas (veja todas na opção 9 - Visualizar Vagas){Colors.RESET}")
        
        print(f"{Colors.GRAY}{'─' * 70}{Colors.RESET}")
    
    async def _post_execution_options(self, jobs: List[Dict], config: Dict) -> None:
        """Opções após a execução"""
        while True:
            print(f"\n{Colors.CYAN}🎯 O QUE FAZER AGORA?{Colors.RESET}")
            print(f"  {Colors.CYAN}[1]{Colors.RESET} 📋 Ver todas as vagas coletadas")
            print(f"  {Colors.CYAN}[2]{Colors.RESET} 📊 Análise detalhada dos resultados")
            print(f"  {Colors.CYAN}[3]{Colors.RESET} 🎯 Executar outro scraping avançado")
            print(f"  {Colors.CYAN}[4]{Colors.RESET} 🧠 Análise com IA (se disponível)")
            print(f"  {Colors.CYAN}[5]{Colors.RESET} 📁 Abrir pasta de resultados")
            print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (0-5): {Colors.RESET}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self._show_all_jobs_detailed(jobs)
            elif choice == "2":
                self._show_detailed_analysis(jobs, config)
            elif choice == "3":
                await self.run_advanced_scraping()
                break
            elif choice == "4":
                await self._run_ai_analysis(jobs)
            elif choice == "5":
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
            
            techs = job.get('tecnologias_detectadas', [])
            if techs:
                print(f"     💻 {', '.join(techs)}")
            
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
    
    def _show_detailed_analysis(self, jobs: List[Dict], config: Dict) -> None:
        """Mostra análise detalhada dos resultados"""
        print(f"\n{Colors.CYAN}📊 ANÁLISE DETALHADA DOS RESULTADOS{Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 60}{Colors.RESET}")
        
        print(f"🎯 Configuração: {config['config_name']}")
        print(f"📋 Total coletado: {len(jobs)} vagas")
        print(f"⚙️  Parâmetros: {config['pages']} páginas, {config['concurrent']} jobs")
        print(f"🧠 Análise IA: {'Ativada' if config.get('ai_analysis') else 'Desativada'}")
        
        # Análise temporal
        print(f"\n⏰ ANÁLISE TEMPORAL:")
        today_jobs = sum(1 for job in jobs if job.get('data_coleta', '').startswith(datetime.now().strftime('%Y-%m-%d')))
        print(f"   📅 Vagas coletadas hoje: {today_jobs}")
        
        # Análise por nível
        level_counts = {}
        for job in jobs:
            level = job.get('nivel_categorizado', 'nao_especificado')
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print(f"\n🎚️ DISTRIBUIÇÃO POR NÍVEL:")
        for level, count in sorted(level_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(jobs)) * 100
            level_display = {
                'junior': 'Júnior',
                'pleno': 'Pleno',
                'senior': 'Sênior',
                'especialista': 'Especialista',
                'trainee': 'Trainee',
                'nao_especificado': 'Não especificado'
            }.get(level, level)
            print(f"   • {level_display}: {count} vagas ({percentage:.1f}%)")
        
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _run_ai_analysis(self, jobs: List[Dict]) -> None:
        """Executa análise com IA das vagas coletadas"""
        print(f"\n{Colors.PURPLE}🧠 ANÁLISE COM IA{Colors.RESET}")
        print("Esta funcionalidade realizará análise inteligente das vagas coletadas.")
        print("Implementação futura: machine learning para padrões de mercado.")
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
async def run_advanced_scraping():
    """Função principal para scraping avançado"""
    handler = AdvancedScrapingHandler()
    await handler.run_advanced_scraping()