"""
Smart Scraping Handler - Interface Intuitiva de Busca de Vagas

Sistema redesenhado para uma experiência de usuário moderna e intuitiva,
com presets inteligentes e configuração automática.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Importações condicionais para evitar problemas de dependência
try:
    from ..core.scraper_optimized import scrape_catho_jobs_optimized
    OPTIMIZED_AVAILABLE = True
except ImportError as e:
    print(f"Aviso: Scraper otimizado não disponível (dependências ML): {e}")
    OPTIMIZED_AVAILABLE = False

try:
    from ..core.scraper_pooled import scrape_catho_jobs_pooled
    POOLED_AVAILABLE = True
except ImportError as e:
    print(f"Aviso: Scraper pooled não disponível (dependências ML): {e}")
    POOLED_AVAILABLE = False

# Fallback para scraper básico
from ..core.scraper import scrape_catho_jobs
from ..utils.utils import save_results
from ..utils.menu_system import MenuSystem, Colors
from ..utils.settings_manager import settings_manager


class SmartScrapingHandler:
    """Handler inteligente para busca de vagas com UX moderna"""
    
    def __init__(self):
        self.menu = MenuSystem()
        
        # Presets inteligentes baseados em uso comum
        self.job_presets = {
            "💻 Desenvolvimento": {
                "description": "Vagas de programação, desenvolvimento web, mobile e desktop",
                "keywords": ["desenvolvedor", "programador", "developer", "frontend", "backend", "fullstack"],
                "pages": 20,
                "concurrent": 10
            },
            "🎨 Design & UX": {
                "description": "Design gráfico, UX/UI, design de produtos",
                "keywords": ["designer", "ux", "ui", "grafico", "criativo"],
                "pages": 15,
                "concurrent": 8
            },
            "📊 Dados & Analytics": {
                "description": "Ciência de dados, análise, business intelligence",
                "keywords": ["dados", "analytics", "scientist", "analyst", "bi"],
                "pages": 15,
                "concurrent": 8
            },
            "🔧 DevOps & Infra": {
                "description": "DevOps, infraestrutura, cloud, SRE",
                "keywords": ["devops", "infrastructure", "cloud", "aws", "azure", "sre"],
                "pages": 15,
                "concurrent": 8
            },
            "🚀 Produto & Gestão": {
                "description": "Product manager, project manager, gestão de produtos",
                "keywords": ["product", "manager", "gestão", "projeto", "scrum"],
                "pages": 15,
                "concurrent": 8
            },
            "📱 Marketing Digital": {
                "description": "Marketing digital, social media, growth",
                "keywords": ["marketing", "digital", "social", "growth", "seo"],
                "pages": 12,
                "concurrent": 6
            },
            "💼 Vendas & Comercial": {
                "description": "Vendas, inside sales, account manager",
                "keywords": ["vendas", "sales", "comercial", "account", "sdr"],
                "pages": 25,
                "concurrent": 12
            },
            "🏢 Administrativo": {
                "description": "Recursos humanos, financeiro, administrativo",
                "keywords": ["administrativo", "rh", "financeiro", "contabil"],
                "pages": 15,
                "concurrent": 8
            },
            "🌟 Todas as Vagas": {
                "description": "Busca ampla por vagas home office (recomendado)",
                "keywords": [],
                "pages": 33,
                "concurrent": 15
            }
        }
        
        # Presets de velocidade
        self.speed_presets = {
            "🐌 Cuidadoso": {
                "description": "Mais lento, mas máxima qualidade e estabilidade",
                "concurrent_modifier": 0.5,
                "page_delay": 3.0,
                "incremental": True
            },
            "⚡ Balanceado": {
                "description": "Equilíbrio ideal entre velocidade e qualidade",
                "concurrent_modifier": 1.0,
                "page_delay": 1.5,
                "incremental": True
            },
            "🚀 Rápido": {
                "description": "Máxima velocidade (pode ser mais instável)",
                "concurrent_modifier": 1.5,
                "page_delay": 0.5,
                "incremental": True
            }
        }
    
    async def run_smart_search(self) -> None:
        """Interface principal - busca inteligente"""
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET}                     🎯 BUSCA INTELIGENTE DE VAGAS                         {Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET}                 Sistema moderno com presets automáticos                   {Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        
        # Passo 1: Escolher área de interesse
        job_config = await self._select_job_area()
        if not job_config:
            return
        
        # Passo 2: Escolher velocidade
        speed_config = await self._select_speed()
        if not speed_config:
            return
        
        # Passo 3: Confirmação e execução
        final_config = self._build_final_config(job_config, speed_config)
        
        if await self._confirm_execution(final_config):
            await self._execute_smart_search(final_config)
    
    async def _select_job_area(self) -> Optional[Dict]:
        """Seleção de área profissional"""
        print(f"\n{Colors.YELLOW}📋 PASSO 1: Escolha sua área de interesse{Colors.RESET}")
        print(f"   {Colors.GRAY}Selecione o tipo de vaga que você procura:{Colors.RESET}\n")
        
        options = list(self.job_presets.keys())
        
        for i, (name, config) in enumerate(self.job_presets.items(), 1):
            print(f"  {Colors.CYAN}[{i:2d}]{Colors.RESET} {name}")
            print(f"       {Colors.GRAY}{config['description']}{Colors.RESET}")
            if config['keywords']:
                keywords_display = ', '.join(config['keywords'][:3])
                if len(config['keywords']) > 3:
                    keywords_display += f" e mais {len(config['keywords'])-3}"
                print(f"       {Colors.GRAY}Palavras-chave: {keywords_display}{Colors.RESET}")
            print()
        
        print(f"  {Colors.CYAN}[0]{Colors.RESET}  ⬅️  Voltar ao menu principal\n")
        
        try:
            choice = input(f"{Colors.YELLOW}➤ Sua escolha (1-{len(options)}): {Colors.RESET}").strip()
            
            if choice == "0":
                return None
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                selected_key = options[choice_idx]
                config = self.job_presets[selected_key].copy()
                config['area_name'] = selected_key
                return config
            else:
                print(f"{Colors.RED}❌ Opção inválida. Tente novamente.{Colors.RESET}")
                return await self._select_job_area()
                
        except (ValueError, KeyboardInterrupt):
            print(f"{Colors.RED}❌ Entrada inválida.{Colors.RESET}")
            return await self._select_job_area()
    
    async def _select_speed(self) -> Optional[Dict]:
        """Seleção de velocidade de execução"""
        print(f"\n{Colors.YELLOW}⚡ PASSO 2: Escolha a velocidade de busca{Colors.RESET}")
        print(f"   {Colors.GRAY}Defina o compromisso entre velocidade e qualidade:{Colors.RESET}\n")
        
        options = list(self.speed_presets.keys())
        
        for i, (name, config) in enumerate(self.speed_presets.items(), 1):
            print(f"  {Colors.CYAN}[{i}]{Colors.RESET} {name}")
            print(f"     {Colors.GRAY}{config['description']}{Colors.RESET}\n")
        
        print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar à seleção de área\n")
        
        try:
            choice = input(f"{Colors.YELLOW}➤ Sua escolha (1-{len(options)}): {Colors.RESET}").strip()
            
            if choice == "0":
                return None
                
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                selected_key = options[choice_idx]
                config = self.speed_presets[selected_key].copy()
                config['speed_name'] = selected_key
                return config
            else:
                print(f"{Colors.RED}❌ Opção inválida. Tente novamente.{Colors.RESET}")
                return await self._select_speed()
                
        except (ValueError, KeyboardInterrupt):
            print(f"{Colors.RED}❌ Entrada inválida.{Colors.RESET}")
            return await self._select_speed()
    
    def _build_final_config(self, job_config: Dict, speed_config: Dict) -> Dict:
        """Constrói configuração final combinando área e velocidade"""
        # Calcular parâmetros finais
        base_concurrent = job_config['concurrent']
        final_concurrent = max(2, int(base_concurrent * speed_config['concurrent_modifier']))
        
        return {
            'area_name': job_config['area_name'],
            'speed_name': speed_config['speed_name'],
            'keywords': job_config['keywords'],
            'max_pages': job_config['pages'],
            'max_concurrent': final_concurrent,
            'incremental': speed_config['incremental'],
            'performance_mode': 3,  # Sempre usar o melhor scraper
            'enable_deduplication': True,
            'use_diversity': True,
            'page_delay': speed_config['page_delay']
        }
    
    async def _confirm_execution(self, config: Dict) -> bool:
        """Confirmação antes da execução"""
        print(f"\n{Colors.GREEN}✅ RESUMO DA CONFIGURAÇÃO{Colors.RESET}")
        print(f"{Colors.CYAN}══════════════════════════════════════════════════════════════════════════════{Colors.RESET}")
        print(f"🎯 Área: {config['area_name']}")
        print(f"⚡ Velocidade: {config['speed_name']}")
        print(f"📄 Páginas a processar: {config['max_pages']}")
        print(f"🔄 Jobs simultâneos: {config['max_concurrent']}")
        
        if config['keywords']:
            keywords_display = ', '.join(config['keywords'][:5])
            if len(config['keywords']) > 5:
                keywords_display += f" e mais {len(config['keywords'])-5}"
            print(f"🔍 Palavras-chave: {keywords_display}")
        else:
            print(f"🔍 Busca: Todas as vagas home office")
        
        print(f"⚡ Processamento incremental: {'Sim' if config['incremental'] else 'Não'}")
        print(f"🧹 Deduplicação automática: {'Sim' if config['enable_deduplication'] else 'Não'}")
        
        # Estimativa de tempo
        estimated_time = self._estimate_execution_time(config)
        print(f"⏱️  Tempo estimado: {estimated_time}")
        
        print(f"{Colors.CYAN}══════════════════════════════════════════════════════════════════════════════{Colors.RESET}")
        
        while True:
            print(f"\n{Colors.YELLOW}🚀 Iniciar busca com essas configurações?{Colors.RESET}")
            print(f"  {Colors.GREEN}[S]{Colors.RESET} Sim, iniciar busca")
            print(f"  {Colors.RED}[N]{Colors.RESET} Não, voltar ao menu")
            print(f"  {Colors.CYAN}[C]{Colors.RESET} Configuração personalizada")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (S/N/C): {Colors.RESET}").strip().upper()
            
            if choice in ['S', 'SIM', 'Y', 'YES']:
                return True
            elif choice in ['N', 'NAO', 'NÃO']:
                return False
            elif choice in ['C', 'CONFIG']:
                await self._custom_configuration(config)
                return True
            else:
                print(f"{Colors.RED}❌ Opção inválida. Digite S, N ou C.{Colors.RESET}")
    
    def _estimate_execution_time(self, config: Dict) -> str:
        """Estima tempo de execução baseado na configuração"""
        # Estimativas baseadas em experiência
        pages = config['max_pages']
        concurrent = config['max_concurrent']
        delay = config['page_delay']
        
        # Tempo base por página (em segundos)
        time_per_page = 2 + delay
        
        # Ajuste para paralelismo
        total_time = (pages * time_per_page) / max(1, concurrent * 0.7)
        
        # Ajuste para processamento incremental
        if config['incremental']:
            total_time *= 0.4  # 60% mais rápido com incremental
        
        if total_time < 60:
            return f"{int(total_time)} segundos"
        elif total_time < 3600:
            return f"{int(total_time // 60)} minutos"
        else:
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            return f"{hours}h {minutes}min"
    
    async def _custom_configuration(self, config: Dict) -> None:
        """Permite ajustes personalizados na configuração"""
        print(f"\n{Colors.CYAN}⚙️ CONFIGURAÇÃO PERSONALIZADA{Colors.RESET}")
        print(f"   {Colors.GRAY}Pressione Enter para manter o valor atual:{Colors.RESET}\n")
        
        # Páginas
        current_pages = config['max_pages']
        new_pages = input(f"📄 Páginas ({current_pages}): ").strip()
        if new_pages and new_pages.isdigit():
            config['max_pages'] = int(new_pages)
        
        # Concurrent jobs
        current_concurrent = config['max_concurrent']
        new_concurrent = input(f"🔄 Jobs simultâneos ({current_concurrent}): ").strip()
        if new_concurrent and new_concurrent.isdigit():
            config['max_concurrent'] = int(new_concurrent)
        
        # Incremental
        current_incremental = "Sim" if config['incremental'] else "Não"
        new_incremental = input(f"⚡ Processamento incremental ({current_incremental}) [S/N]: ").strip().upper()
        if new_incremental in ['S', 'N']:
            config['incremental'] = new_incremental == 'S'
        
        print(f"\n{Colors.GREEN}✅ Configuração personalizada salva!{Colors.RESET}")
    
    async def _execute_smart_search(self, config: Dict) -> None:
        """Executa a busca com a configuração definida"""
        print(f"\n{Colors.GREEN}🚀 INICIANDO BUSCA INTELIGENTE{Colors.RESET}")
        print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════════════════════{Colors.RESET}")
        
        start_time = datetime.now()
        
        try:
            # Determinar qual scraper usar baseado na disponibilidade
            if config['performance_mode'] == 3 and POOLED_AVAILABLE:
                print(f"{Colors.CYAN}🚀 Usando scraper pooled (máxima performance){Colors.RESET}")
                jobs = await scrape_catho_jobs_pooled(
                    max_concurrent_jobs=config['max_concurrent'],
                    max_pages=config['max_pages'],
                    incremental=config['incremental'],
                    show_compression_stats=True,
                    show_pool_stats=True,
                    pool_min_size=max(2, config['max_concurrent'] // 3),
                    pool_max_size=config['max_concurrent'] + 2,
                    enable_deduplication=config['enable_deduplication']
                )
            elif OPTIMIZED_AVAILABLE:
                print(f"{Colors.CYAN}⚡ Usando scraper otimizado{Colors.RESET}")
                jobs = await scrape_catho_jobs_optimized(
                    max_concurrent_jobs=config['max_concurrent'],
                    max_pages=config['max_pages'],
                    incremental=config['incremental'],
                    show_compression_stats=True,
                    enable_deduplication=config['enable_deduplication'],
                    use_url_diversity=config['use_diversity']
                )
            else:
                print(f"{Colors.YELLOW}🔧 Usando scraper básico (modo compatibilidade){Colors.RESET}")
                print(f"{Colors.GRAY}   Funcionalidades ML temporariamente indisponíveis{Colors.RESET}")
                jobs = await scrape_catho_jobs(
                    max_concurrent_jobs=config['max_concurrent'],
                    max_pages=config['max_pages']
                )
            
            # Calcular tempo de execução
            execution_time = datetime.now() - start_time
            
            if jobs:
                print(f"\n{Colors.GREEN}🎉 BUSCA CONCLUÍDA COM SUCESSO!{Colors.RESET}")
                print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════════════════════{Colors.RESET}")
                print(f"✅ Vagas encontradas: {len(jobs)}")
                print(f"⏱️  Tempo de execução: {execution_time}")
                print(f"🎯 Área pesquisada: {config['area_name']}")
                print(f"⚡ Modo: {config['speed_name']}")
                
                # Salvar resultados automaticamente
                print(f"\n{Colors.YELLOW}💾 Salvando resultados automaticamente...{Colors.RESET}")
                save_results(jobs, filters_applied={
                    'area': config['area_name'],
                    'keywords': config['keywords'],
                    'pages': config['max_pages']
                }, ask_user_preference=False)
                
                # Preview rápido dos resultados
                self._show_results_preview(jobs)
                
                # Opções pós-busca
                await self._post_search_options(jobs, config)
                
            else:
                print(f"\n{Colors.RED}❌ Nenhuma vaga nova foi encontrada{Colors.RESET}")
                print(f"   {Colors.GRAY}Isso pode significar que:{Colors.RESET}")
                print(f"   • Todas as vagas já estão no seu banco de dados")
                print(f"   • O site não tem vagas novas para sua busca")
                print(f"   • Os filtros foram muito restritivos")
                
                await self._suggest_alternatives(config)
        
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro durante a execução: {e}{Colors.RESET}")
            print(f"   {Colors.GRAY}Tente novamente com configurações mais conservadoras{Colors.RESET}")
    
    def _show_results_preview(self, jobs: List[Dict], limit: int = 5) -> None:
        """Mostra preview dos resultados encontrados"""
        print(f"\n{Colors.CYAN}👀 PREVIEW DOS RESULTADOS (primeiras {min(limit, len(jobs))} vagas):{Colors.RESET}")
        print(f"{Colors.GRAY}{'─' * 80}{Colors.RESET}")
        
        for i, job in enumerate(jobs[:limit], 1):
            title = job.get('titulo', 'Título não disponível')[:50]
            company = job.get('empresa', 'Empresa não identificada')[:30]
            location = job.get('localizacao', 'Local não informado')[:25]
            
            print(f"{Colors.YELLOW}{i:2d}.{Colors.RESET} {title}")
            print(f"    🏢 {company} | 📍 {location}")
            if job.get('tecnologias_detectadas'):
                techs = ', '.join(job['tecnologias_detectadas'][:3])
                if len(job['tecnologias_detectadas']) > 3:
                    techs += f" +{len(job['tecnologias_detectadas'])-3}"
                print(f"    💻 {techs}")
            print()
        
        if len(jobs) > limit:
            print(f"{Colors.GRAY}... e mais {len(jobs) - limit} vagas{Colors.RESET}")
    
    async def _post_search_options(self, jobs: List[Dict], config: Dict) -> None:
        """Opções disponíveis após a busca"""
        while True:
            print(f"\n{Colors.YELLOW}🎯 O que deseja fazer agora?{Colors.RESET}")
            print(f"  {Colors.CYAN}[1]{Colors.RESET} 📊 Ver estatísticas detalhadas")
            print(f"  {Colors.CYAN}[2]{Colors.RESET} 🔍 Ver todas as vagas encontradas")
            print(f"  {Colors.CYAN}[3]{Colors.RESET} 🤖 Analisar vagas com IA")
            print(f"  {Colors.CYAN}[4]{Colors.RESET} 📈 Buscar mais vagas (nova busca)")
            print(f"  {Colors.CYAN}[5]{Colors.RESET} 📁 Abrir pasta dos resultados")
            print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (0-5): {Colors.RESET}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self._show_detailed_stats(jobs, config)
            elif choice == "2":
                self._show_all_jobs(jobs)
            elif choice == "3":
                print(f"{Colors.YELLOW}🤖 Análise com IA será implementada em breve!{Colors.RESET}")
            elif choice == "4":
                await self.run_smart_search()
                break
            elif choice == "5":
                self._open_results_folder()
            else:
                print(f"{Colors.RED}❌ Opção inválida.{Colors.RESET}")
    
    def _show_detailed_stats(self, jobs: List[Dict], config: Dict) -> None:
        """Mostra estatísticas detalhadas dos resultados"""
        print(f"\n{Colors.CYAN}📊 ESTATÍSTICAS DETALHADAS{Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 60}{Colors.RESET}")
        
        # Estatísticas básicas
        print(f"📋 Total de vagas: {len(jobs)}")
        print(f"🎯 Área pesquisada: {config['area_name']}")
        print(f"📄 Páginas processadas: {config['max_pages']}")
        
        # Tecnologias mais comuns
        tech_count = {}
        for job in jobs:
            for tech in job.get('tecnologias_detectadas', []):
                tech_count[tech] = tech_count.get(tech, 0) + 1
        
        if tech_count:
            print(f"\n💻 TOP TECNOLOGIAS:")
            for tech, count in sorted(tech_count.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   • {tech}: {count} vagas")
        
        # Empresas mais ativas
        company_count = {}
        for job in jobs:
            company = job.get('empresa', 'Não identificada')
            if company != 'Empresa não identificada':
                company_count[company] = company_count.get(company, 0) + 1
        
        if company_count:
            print(f"\n🏢 TOP EMPRESAS:")
            for company, count in sorted(company_count.items(), key=lambda x: x[1], reverse=True)[:8]:
                print(f"   • {company}: {count} vagas")
        
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    def _show_all_jobs(self, jobs: List[Dict]) -> None:
        """Mostra todas as vagas encontradas"""
        print(f"\n{Colors.CYAN}📋 TODAS AS VAGAS ENCONTRADAS ({len(jobs)} total){Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 80}{Colors.RESET}")
        
        for i, job in enumerate(jobs, 1):
            title = job.get('titulo', 'Título não disponível')
            company = job.get('empresa', 'Empresa não identificada')
            location = job.get('localizacao', 'Local não informado')
            
            print(f"\n{Colors.YELLOW}{i:3d}.{Colors.RESET} {title}")
            print(f"     🏢 {company}")
            print(f"     📍 {location}")
            
            if job.get('salario') and job['salario'] != 'Não informado':
                print(f"     💰 {job['salario']}")
            
            if job.get('tecnologias_detectadas'):
                techs = ', '.join(job['tecnologias_detectadas'])
                print(f"     💻 {techs}")
            
            if job.get('link'):
                print(f"     🔗 {job['link']}")
            
            # Pausar a cada 10 vagas
            if i % 10 == 0 and i < len(jobs):
                response = input(f"\n{Colors.GRAY}[Enter] Continuar | [Q] Parar: {Colors.RESET}").strip().upper()
                if response == 'Q':
                    break
        
        print(f"\n{Colors.GREEN}✅ Exibição concluída!{Colors.RESET}")
        input(f"{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    def _open_results_folder(self) -> None:
        """Abre a pasta de resultados no explorador"""
        import os
        import subprocess
        import platform
        
        results_path = "data/resultados"
        
        try:
            if platform.system() == "Windows":
                os.startfile(results_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", results_path])
            else:  # Linux
                subprocess.run(["xdg-open", results_path])
            
            print(f"{Colors.GREEN}📁 Pasta de resultados aberta!{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao abrir pasta: {e}{Colors.RESET}")
            print(f"📁 Pasta manual: {os.path.abspath(results_path)}")
    
    async def _suggest_alternatives(self, config: Dict) -> None:
        """Sugere alternativas quando nenhuma vaga é encontrada"""
        print(f"\n{Colors.YELLOW}💡 SUGESTÕES:{Colors.RESET}")
        print(f"  • Tente uma área diferente (ex: 'Todas as Vagas')")
        print(f"  • Use modo 'Rápido' para busca mais ampla")
        print(f"  • Desative o processamento incremental")
        print(f"  • Aumente o número de páginas")
        
        retry = input(f"\n{Colors.YELLOW}Tentar nova busca? [S/N]: {Colors.RESET}").strip().upper()
        if retry in ['S', 'SIM']:
            await self.run_smart_search()


# Função de conveniência para usar no menu principal
async def smart_job_search():
    """Função principal para busca inteligente de vagas"""
    handler = SmartScrapingHandler()
    await handler.run_smart_search()