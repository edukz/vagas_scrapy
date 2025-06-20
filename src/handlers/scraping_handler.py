"""
Handler para operações de scraping
"""

import asyncio
from typing import Dict, Optional

from ..core.scraper import scrape_catho_jobs
from ..utils.filters import JobFilter
from ..utils.utils import save_results
from ..systems.structured_logger import structured_logger, Component
from ..utils.menu_system import MenuSystem, Colors


class ScrapingHandler:
    """Gerencia operações de scraping"""
    
    def __init__(self):
        self.menu = MenuSystem()
    
    async def run_scraping_with_config(self, config: Dict) -> None:
        """Executa scraping com configuração fornecida"""
        # Inicializar sistema de logs
        structured_logger.log_system_info()
        structured_logger.info(
            "Application started",
            component=Component.MAIN,
            context={'version': '4.0', 'config': config}
        )
        
        try:
            # Selecionar scraper baseado no modo de performance
            jobs = await self._execute_scraper(config)
            
            if jobs:
                self.menu.print_success_message(f"Coleta concluída! {len(jobs)} vagas encontradas")
                
                # Aplicar filtros se configurados
                jobs = self._apply_filters(jobs, config)
                
                if jobs:
                    # Salvar resultados
                    print(f"\n{Colors.GREEN}💾 Salvando resultados...{Colors.RESET}")
                    save_results(jobs, config.get('filters', {}))
                    
                    self.menu.print_success_message("Processamento concluído com sucesso!")
                    
                    # Preview dos resultados
                    self._print_results_preview(jobs)
                    
                else:
                    self.menu.print_warning_message("Nenhuma vaga atendeu aos critérios de filtro especificados.")
            else:
                self.menu.print_error_message("Nenhuma vaga foi encontrada no site.")
                
        except Exception as e:
            self.menu.print_error_message(f"Erro durante o processamento: {e}")
            import traceback
            traceback.print_exc()
    
    async def _execute_scraper(self, config: Dict):
        """Executa o scraper apropriado baseado na configuração"""
        performance_mode = config['performance_mode']
        
        if performance_mode == 1:
            # Básico
            self.menu.print_info_message("Iniciando scraper BÁSICO...")
            return await scrape_catho_jobs(
                max_concurrent_jobs=config['max_concurrent'], 
                max_pages=config['max_pages']
            )
            
        elif performance_mode == 2:
            # Otimizado
            self.menu.print_info_message("Iniciando scraper OTIMIZADO...")
            from ..core.scraper_optimized import scrape_catho_jobs_optimized
            return await scrape_catho_jobs_optimized(
                max_concurrent_jobs=config['max_concurrent'], 
                max_pages=config['max_pages'],
                incremental=config['incremental'],
                show_compression_stats=True,
                enable_deduplication=True
            )
            
        else:  # performance_mode == 3
            # Máximo
            self.menu.print_info_message("Iniciando scraper MÁXIMA PERFORMANCE...")
            from ..core.scraper_pooled import scrape_catho_jobs_pooled
            return await scrape_catho_jobs_pooled(
                max_concurrent_jobs=config['max_concurrent'], 
                max_pages=config['max_pages'],
                incremental=config['incremental'],
                show_compression_stats=True,
                show_pool_stats=True,
                pool_min_size=2,
                pool_max_size=config['max_concurrent'] + 2,
                enable_deduplication=True
            )
    
    def _apply_filters(self, jobs: list, config: Dict) -> list:
        """Aplica filtros às vagas"""
        if config.get('apply_filters') and config.get('filters'):
            print(f"\n{Colors.BLUE}🔍 Aplicando filtros personalizados...{Colors.RESET}")
            job_filter = JobFilter()
            filtered_jobs = job_filter.apply_filters(jobs, config['filters'])
            self.menu.print_info_message(f"Filtros aplicados: {len(filtered_jobs)} vagas selecionadas")
            return filtered_jobs
        else:
            # Aplicar apenas análise sem filtros
            job_filter = JobFilter()
            filtered_jobs = job_filter.apply_filters(jobs, {})
            self.menu.print_info_message(f"Análise aplicada a todas as {len(filtered_jobs)} vagas")
            return filtered_jobs
    
    def _print_results_preview(self, jobs: list) -> None:
        """Mostra preview dos resultados"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔥 PREVIEW DOS RESULTADOS:{Colors.RESET}")
        
        if jobs:
            # Tecnologias mais demandadas
            all_techs = {}
            for job in jobs:
                for tech in job.get('tecnologias_detectadas', []):
                    all_techs[tech] = all_techs.get(tech, 0) + 1
            
            if all_techs:
                print(f"   {Colors.BOLD}💻 Top 5 tecnologias:{Colors.RESET}")
                for tech, count in sorted(all_techs.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"      - {Colors.GREEN}{tech}{Colors.RESET}: {count} vagas")
            
            # Análise de níveis
            niveis = {}
            for job in jobs:
                nivel = job.get('nivel_categorizado', 'Não categorizado')
                niveis[nivel] = niveis.get(nivel, 0) + 1
            
            if niveis:
                print(f"   {Colors.BOLD}📊 Distribuição por nível:{Colors.RESET}")
                for nivel, count in sorted(niveis.items(), key=lambda x: x[1], reverse=True)[:3]:
                    print(f"      - {Colors.YELLOW}{nivel.replace('_', ' ').title()}{Colors.RESET}: {count} vagas")