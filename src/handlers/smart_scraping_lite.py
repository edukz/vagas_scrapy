"""
Smart Scraping Handler LITE - Versão Simplificada Sem Dependências ML

Sistema redesenhado para uma experiência de usuário moderna e intuitiva,
funcionando perfeitamente sem dependências de Machine Learning.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Importar scrapers (com fallback para versão robusta)
try:
    from ..core.scraper import scrape_catho_jobs
    BASIC_SCRAPER_AVAILABLE = True
except ImportError:
    BASIC_SCRAPER_AVAILABLE = False

from ..core.scraper_robust import scrape_catho_jobs_robust, check_catho_accessibility
from ..core.scraper_multi_mode import scrape_catho_jobs_multi_mode
from ..utils.utils import save_results
from ..utils.menu_system import MenuSystem, Colors


class SmartScrapingLiteHandler:
    """Handler inteligente para busca de vagas - versão LITE sem ML"""
    
    def __init__(self):
        self.menu = MenuSystem()
        
        # Presets inteligentes baseados em uso comum (sem ML)
        self.job_presets = {
            "💻 Desenvolvimento": {
                "description": "Vagas de programação, desenvolvimento web, mobile e desktop",
                "filter_keywords": ["desenvolvedor", "programador", "developer", "frontend", "backend", "fullstack"],
                "pages": 20,
                "concurrent": 8
            },
            "🎨 Design & UX": {
                "description": "Design gráfico, UX/UI, design de produtos",
                "filter_keywords": ["designer", "ux", "ui", "grafico", "criativo"],
                "pages": 15,
                "concurrent": 6
            },
            "📊 Dados & Analytics": {
                "description": "Ciência de dados, análise, business intelligence",
                "filter_keywords": ["dados", "analytics", "scientist", "analyst", "bi"],
                "pages": 15,
                "concurrent": 6
            },
            "🔧 DevOps & Infra": {
                "description": "DevOps, infraestrutura, cloud, SRE",
                "filter_keywords": ["devops", "infrastructure", "cloud", "aws", "azure", "sre"],
                "pages": 15,
                "concurrent": 6
            },
            "🚀 Produto & Gestão": {
                "description": "Product manager, project manager, gestão de produtos",
                "filter_keywords": ["product", "manager", "gestão", "projeto", "scrum"],
                "pages": 15,
                "concurrent": 6
            },
            "📱 Marketing Digital": {
                "description": "Marketing digital, social media, growth",
                "filter_keywords": ["marketing", "digital", "social", "growth", "seo"],
                "pages": 12,
                "concurrent": 5
            },
            "💼 Vendas & Comercial": {
                "description": "Vendas, inside sales, account manager",
                "filter_keywords": ["vendas", "sales", "comercial", "account", "sdr"],
                "pages": 25,
                "concurrent": 10
            },
            "🏢 Administrativo": {
                "description": "Recursos humanos, financeiro, administrativo",
                "filter_keywords": ["administrativo", "rh", "financeiro", "contabil"],
                "pages": 15,
                "concurrent": 6
            },
            "🌟 Todas as Modalidades": {
                "description": "Home office + Presencial + Híbrido (busca completa)",
                "filter_keywords": [],
                "pages": 50,
                "concurrent": 15,
                "multi_mode": True
            },
            "🏠 Apenas Home Office": {
                "description": "Somente vagas remotas/home office",
                "filter_keywords": [],
                "pages": 33,
                "concurrent": 12,
                "multi_mode": False
            }
        }
        
        # Presets de velocidade
        self.speed_presets = {
            "🐌 Cuidadoso": {
                "description": "Mais lento, mas máxima qualidade e estabilidade",
                "concurrent_modifier": 0.7,
                "pages_modifier": 1.0,
                "delay": "alto"
            },
            "⚡ Balanceado": {
                "description": "Equilíbrio ideal entre velocidade e qualidade",
                "concurrent_modifier": 1.0,
                "pages_modifier": 1.0,
                "delay": "medio"
            },
            "🚀 Rápido": {
                "description": "Máxima velocidade (pode ser mais instável)",
                "concurrent_modifier": 1.3,
                "pages_modifier": 0.8,
                "delay": "baixo"
            }
        }
    
    async def run_smart_search(self) -> None:
        """Interface principal - busca inteligente LITE"""
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET}                   🎯 BUSCA INTELIGENTE DE VAGAS LITE                      {Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET}               Sistema moderno com presets automáticos                     {Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.CYAN}║{Colors.RESET}                    {Colors.YELLOW}⚡ Modo compatibilidade ativado{Colors.RESET}                     {Colors.CYAN}║{Colors.RESET}")
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
            if config['filter_keywords']:
                keywords_display = ', '.join(config['filter_keywords'][:3])
                if len(config['filter_keywords']) > 3:
                    keywords_display += f" e mais {len(config['filter_keywords'])-3}"
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
        
        base_pages = job_config['pages']
        final_pages = max(5, int(base_pages * speed_config['pages_modifier']))
        
        return {
            'area_name': job_config['area_name'],
            'speed_name': speed_config['speed_name'],
            'filter_keywords': job_config['filter_keywords'],
            'max_pages': final_pages,
            'max_concurrent': final_concurrent,
            'delay_mode': speed_config['delay'],
            'multi_mode': job_config.get('multi_mode', False)
        }
    
    async def _confirm_execution(self, config: Dict) -> bool:
        """Confirmação antes da execução"""
        print(f"\n{Colors.GREEN}✅ RESUMO DA CONFIGURAÇÃO{Colors.RESET}")
        print(f"{Colors.CYAN}══════════════════════════════════════════════════════════════════════════════{Colors.RESET}")
        print(f"🎯 Área: {config['area_name']}")
        print(f"⚡ Velocidade: {config['speed_name']}")
        print(f"📄 Páginas a processar: {config['max_pages']}")
        print(f"🔄 Jobs simultâneos: {config['max_concurrent']}")
        
        if config['filter_keywords']:
            keywords_display = ', '.join(config['filter_keywords'][:5])
            if len(config['filter_keywords']) > 5:
                keywords_display += f" e mais {len(config['filter_keywords'])-5}"
            print(f"🔍 Filtros: {keywords_display}")
        else:
            if config.get('multi_mode'):
                print(f"🔍 Busca: Todas as modalidades (Home Office + Presencial + Híbrido)")
            else:
                print(f"🔍 Busca: Apenas vagas home office")
        
        print(f"⏱️  Modo de delay: {config['delay_mode']}")
        
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
        pages = config['max_pages']
        concurrent = config['max_concurrent']
        
        # Tempo base por página (em segundos) - versão simplificada
        if config['delay_mode'] == 'alto':
            time_per_page = 4
        elif config['delay_mode'] == 'medio':
            time_per_page = 2.5
        else:  # baixo
            time_per_page = 1.5
        
        # Ajuste para paralelismo
        total_time = (pages * time_per_page) / max(1, concurrent * 0.6)
        
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
        
        print(f"\n{Colors.GREEN}✅ Configuração personalizada salva!{Colors.RESET}")
    
    async def _execute_smart_search(self, config: Dict) -> None:
        """Executa a busca com a configuração definida"""
        print(f"\n{Colors.GREEN}🚀 INICIANDO BUSCA INTELIGENTE LITE{Colors.RESET}")
        print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════════════════════{Colors.RESET}")
        print(f"{Colors.YELLOW}⚡ Modo compatibilidade: Funcionalidades ML temporariamente indisponíveis{Colors.RESET}")
        
        start_time = datetime.now()
        
        try:
            # Verificar conectividade primeiro
            print(f"{Colors.GRAY}🌐 Verificando conectividade com o Catho...{Colors.RESET}")
            is_accessible = await check_catho_accessibility()
            
            if not is_accessible:
                print(f"{Colors.RED}❌ Site do Catho não está acessível no momento{Colors.RESET}")
                print(f"{Colors.YELLOW}💡 Tente novamente em alguns minutos{Colors.RESET}")
                return
            
            print(f"{Colors.GREEN}✅ Site acessível, iniciando coleta...{Colors.RESET}")
            
            # Usar scraper multi-modalidade sempre
            print(f"{Colors.CYAN}🌍 Usando scraper multi-modalidade...{Colors.RESET}")
            jobs = await scrape_catho_jobs_multi_mode(
                max_concurrent_jobs=config['max_concurrent'],
                max_pages=config['max_pages'],
                multi_mode=config.get('multi_mode', False)
            )
            
            # Aplicar filtros simples se especificados
            if config['filter_keywords'] and jobs:
                jobs = self._apply_simple_filters(jobs, config['filter_keywords'])
            
            # Calcular tempo de execução
            execution_time = datetime.now() - start_time
            
            if jobs:
                print(f"\n{Colors.GREEN}🎉 BUSCA CONCLUÍDA COM SUCESSO!{Colors.RESET}")
                print(f"{Colors.CYAN}═══════════════════════════════════════════════════════════════════════════════{Colors.RESET}")
                print(f"✅ Vagas encontradas: {len(jobs)}")
                print(f"⏱️  Tempo de execução: {execution_time}")
                print(f"🎯 Área pesquisada: {config['area_name']}")
                print(f"⚡ Modo: {config['speed_name']}")
                
                # Mostrar distribuição por modalidade
                self._show_mode_distribution(jobs)
                
                # Salvar resultados automaticamente
                print(f"\n{Colors.YELLOW}💾 Salvando resultados automaticamente...{Colors.RESET}")
                save_results(jobs, filters_applied={
                    'area': config['area_name'],
                    'keywords': config['filter_keywords'],
                    'pages': config['max_pages'],
                    'modalidades': self._get_modes_searched(config)
                }, ask_user_preference=False)
                
                # SEMPRE mostrar as vagas encontradas
                print(f"\n{Colors.CYAN}📋 VAGAS ENCONTRADAS:{Colors.RESET}")
                self._show_all_jobs_compact(jobs)
                
                # Opções pós-busca
                await self._post_search_options(jobs, config)
                
            else:
                print(f"\n{Colors.RED}❌ Nenhuma vaga foi encontrada{Colors.RESET}")
                print(f"   {Colors.GRAY}Isso pode significar que:{Colors.RESET}")
                print(f"   • O site não tem vagas novas para sua busca")
                print(f"   • Os filtros foram muito restritivos")
                print(f"   • Problema temporário de conectividade")
                
                await self._suggest_alternatives(config)
        
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro durante a execução: {e}{Colors.RESET}")
            print(f"   {Colors.GRAY}Tente novamente com configurações mais conservadoras{Colors.RESET}")
            import traceback
            traceback.print_exc()
    
    def _apply_simple_filters(self, jobs: List[Dict], keywords: List[str]) -> List[Dict]:
        """Aplica filtros simples baseado em palavras-chave"""
        if not keywords:
            return jobs
        
        filtered_jobs = []
        keywords_lower = [k.lower() for k in keywords]
        
        for job in jobs:
            title = job.get('titulo', '').lower()
            company = job.get('empresa', '').lower()
            description = job.get('descricao', '').lower()
            
            # Verificar se alguma palavra-chave está presente
            text_to_search = f"{title} {company} {description}"
            
            if any(keyword in text_to_search for keyword in keywords_lower):
                filtered_jobs.append(job)
        
        if len(filtered_jobs) != len(jobs):
            print(f"{Colors.YELLOW}🔍 Filtros aplicados: {len(jobs)} → {len(filtered_jobs)} vagas{Colors.RESET}")
        
        return filtered_jobs
    
    def _show_mode_distribution(self, jobs: List[Dict]) -> None:
        """Mostra distribuição de vagas por modalidade"""
        mode_counts = {}
        for job in jobs:
            mode = job.get('modalidade_trabalho', job.get('regime', 'Não especificada'))
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        if len(mode_counts) > 1:  # Só mostrar se houver múltiplas modalidades
            print(f"\n📊 DISTRIBUIÇÃO POR MODALIDADE:")
            for mode, count in sorted(mode_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(jobs)) * 100
                print(f"   🔹 {mode}: {count} vagas ({percentage:.1f}%)")
    
    def _get_modes_searched(self, config: Dict) -> List[str]:
        """Retorna lista de modalidades pesquisadas"""
        if config.get('multi_mode'):
            return ['Home Office', 'Presencial', 'Híbrido']
        else:
            return ['Home Office']
    
    def _show_all_jobs_compact(self, jobs: List[Dict]) -> None:
        """Mostra todas as vagas de forma compacta"""
        print(f"{Colors.GRAY}{'─' * 80}{Colors.RESET}")
        
        for i, job in enumerate(jobs, 1):
            title = job.get('titulo', 'Título não disponível')[:60]
            company = job.get('empresa', 'Empresa não identificada')[:25]
            mode = job.get('modalidade_trabalho', job.get('regime', 'N/A'))
            location = job.get('localizacao', 'Não informada')
            
            # Emojis por modalidade
            mode_emoji = {
                'Home Office': '🏠',
                'Presencial': '🏢', 
                'Híbrido': '🔄',
                'Não especificada': '❓'
            }.get(mode, '📍')
            
            print(f"{Colors.YELLOW}{i:3d}.{Colors.RESET} {title}")
            print(f"     🏢 {company} | {mode_emoji} {mode}")
            
            if location and location != 'Não informada' and location != 'Não especificada':
                print(f"     📍 {location}")
            
            if job.get('salario') and job['salario'] not in ['Não informado', 'Não especificado']:
                print(f"     💰 {job['salario']}")
            
            if job.get('tecnologias_detectadas'):
                techs = ', '.join(job['tecnologias_detectadas'][:3])
                if len(job['tecnologias_detectadas']) > 3:
                    techs += f" +{len(job['tecnologias_detectadas'])-3}"
                print(f"     💻 {techs}")
            
            # Link sempre visível
            if job.get('link'):
                link_display = job['link'][:70] + '...' if len(job['link']) > 70 else job['link']
                print(f"     🔗 {link_display}")
            
            print()
            
            # Pausar a cada 10 vagas
            if i % 10 == 0 and i < len(jobs):
                try:
                    response = input(f"{Colors.GRAY}[Enter] Continuar | [Q] Parar | [A] Ver todas: {Colors.RESET}").strip().upper()
                    if response == 'Q':
                        print(f"{Colors.GRAY}... e mais {len(jobs) - i} vagas (use opção 2 para ver todas){Colors.RESET}")
                        break
                    elif response == 'A':
                        continue  # Continuar sem mais pausas
                except (KeyboardInterrupt, EOFError):
                    print(f"{Colors.GRAY}... listagem interrompida{Colors.RESET}")
                    break
        
        if len(jobs) <= 10 or response != 'Q':
            print(f"{Colors.GREEN}✅ Exibidas todas as {len(jobs)} vagas encontradas!{Colors.RESET}")
        
        print(f"{Colors.GRAY}{'─' * 80}{Colors.RESET}")
    
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
            print(f"  {Colors.CYAN}[3]{Colors.RESET} 📈 Buscar mais vagas (nova busca)")
            print(f"  {Colors.CYAN}[4]{Colors.RESET} 📁 Abrir pasta dos resultados")
            print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (0-4): {Colors.RESET}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self._show_detailed_stats(jobs, config)
            elif choice == "2":
                self._show_all_jobs(jobs)
            elif choice == "3":
                await self.run_smart_search()
                break
            elif choice == "4":
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
        
        # Tipos de contrato
        regime_count = {}
        for job in jobs:
            regime = job.get('regime', 'Não especificado')
            regime_count[regime] = regime_count.get(regime, 0) + 1
        
        if regime_count:
            print(f"\n📋 TIPOS DE CONTRATO:")
            for regime, count in sorted(regime_count.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {regime}: {count} vagas")
        
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
        print(f"  • Aumente o número de páginas")
        print(f"  • Remova filtros muito específicos")
        
        retry = input(f"\n{Colors.YELLOW}Tentar nova busca? [S/N]: {Colors.RESET}").strip().upper()
        if retry in ['S', 'SIM']:
            await self.run_smart_search()


# Função de conveniência para usar no menu principal
async def smart_job_search_lite():
    """Função principal para busca inteligente de vagas - versão LITE"""
    handler = SmartScrapingLiteHandler()
    await handler.run_smart_search()