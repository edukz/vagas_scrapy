"""
Sistema Catho Job Scraper - Interface Melhorada
Versão com menu interativo e visual
"""

import asyncio
import sys
import os

# Adicionar pasta src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), ''))

from src.core.scraper import scrape_catho_jobs
from src.utils.filters import JobFilter, get_filter_configuration
from src.utils.utils import save_results
from src.systems.structured_logger import structured_logger, Component
from src.utils.menu_system import MenuSystem, Colors
from src.utils.settings_ui import settings_ui


async def run_scraping_with_config(config):
    """Executa scraping com configuração fornecida"""
    menu = MenuSystem()
    
    # Inicializar sistema de logs
    structured_logger.log_system_info()
    structured_logger.info(
        "Application started",
        component=Component.MAIN,
        context={'version': '4.0', 'config': config}
    )
    
    try:
        # Selecionar scraper baseado no modo de performance
        performance_mode = config['performance_mode']
        
        if performance_mode == 1:
            # Básico
            menu.print_info_message("Iniciando scraper BÁSICO...")
            jobs = await scrape_catho_jobs(
                max_concurrent_jobs=config['max_concurrent'], 
                max_pages=config['max_pages']
            )
            
        elif performance_mode == 2:
            # Otimizado
            menu.print_info_message("Iniciando scraper OTIMIZADO...")
            from src.core.scraper_optimized import scrape_catho_jobs_optimized
            jobs = await scrape_catho_jobs_optimized(
                max_concurrent_jobs=config['max_concurrent'], 
                max_pages=config['max_pages'],
                incremental=config['incremental'],
                show_compression_stats=True,
                enable_deduplication=True
            )
            
        else:  # performance_mode == 3
            # Máximo
            menu.print_info_message("Iniciando scraper MÁXIMA PERFORMANCE...")
            from src.core.scraper_pooled import scrape_catho_jobs_pooled
            jobs = await scrape_catho_jobs_pooled(
                max_concurrent_jobs=config['max_concurrent'], 
                max_pages=config['max_pages'],
                incremental=config['incremental'],
                show_compression_stats=True,
                show_pool_stats=True,
                pool_min_size=2,
                pool_max_size=config['max_concurrent'] + 2,
                enable_deduplication=True
            )
        
        if jobs:
            menu.print_success_message(f"Coleta concluída! {len(jobs)} vagas encontradas")
            
            # Aplicar filtros se configurados
            if config.get('apply_filters') and config.get('filters'):
                print(f"\n{Colors.BLUE}🔍 Aplicando filtros personalizados...{Colors.RESET}")
                job_filter = JobFilter()
                filtered_jobs = job_filter.apply_filters(jobs, config['filters'])
                menu.print_info_message(f"Filtros aplicados: {len(filtered_jobs)} vagas selecionadas")
                jobs = filtered_jobs
            else:
                # Aplicar apenas análise sem filtros
                job_filter = JobFilter()
                jobs = job_filter.apply_filters(jobs, {})
                menu.print_info_message(f"Análise aplicada a todas as {len(jobs)} vagas")
            
            if jobs:
                # Salvar resultados
                print(f"\n{Colors.GREEN}💾 Salvando resultados...{Colors.RESET}")
                save_results(jobs, config.get('filters', {}))
                
                menu.print_success_message("Processamento concluído com sucesso!")
                
                # Preview dos resultados
                print_results_preview(jobs, menu)
                
            else:
                menu.print_warning_message("Nenhuma vaga atendeu aos critérios de filtro especificados.")
        else:
            menu.print_error_message("Nenhuma vaga foi encontrada no site.")
            
    except Exception as e:
        menu.print_error_message(f"Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()


def print_results_preview(jobs, menu):
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


async def handle_cache_operations(choice):
    """Manipula operações de cache"""
    menu = MenuSystem()
    
    try:
        from src.systems.compressed_cache import CompressedCache
        cache = CompressedCache()
        
        if choice == "1":  # Listar tudo
            results = cache.search_cache({})
            print(f"\n{Colors.BOLD}📋 TODAS AS ENTRADAS ({len(results)} encontradas):{Colors.RESET}")
            
            for i, entry in enumerate(results[:10], 1):  # Mostrar apenas 10 primeiros
                print(f"\n{Colors.BOLD}{i:2d}.{Colors.RESET} {entry.url[:60]}...")
                print(f"     📅 Data: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}")
                print(f"     💼 Vagas: {Colors.GREEN}{entry.job_count}{Colors.RESET}")
                print(f"     🏢 Empresas: {Colors.BLUE}{', '.join(entry.companies[:3])}{Colors.RESET}{'...' if len(entry.companies) > 3 else ''}")
            
            if len(results) > 10:
                print(f"\n{Colors.DIM}... e mais {len(results) - 10} entradas{Colors.RESET}")
        
        elif choice == "2":  # Por empresa
            company = input(f"{Colors.BOLD}Digite o nome da empresa: {Colors.RESET}").strip()
            if company:
                results = cache.search_cache({'companies': [company]})
                print(f"\n{Colors.BOLD}🏢 Vagas da empresa '{company}' ({len(results)} encontradas):{Colors.RESET}")
                
                for i, entry in enumerate(results[:5], 1):
                    print(f"  {i}. {entry.url[:50]}... ({entry.job_count} vagas)")
            
        elif choice == "3":  # Por tecnologia
            tech = input(f"{Colors.BOLD}Digite a tecnologia: {Colors.RESET}").strip()
            if tech:
                results = cache.search_cache({'technologies': [tech]})
                print(f"\n{Colors.BOLD}💻 Vagas com '{tech}' ({len(results)} encontradas):{Colors.RESET}")
                
                for i, entry in enumerate(results[:5], 1):
                    print(f"  {i}. {entry.url[:50]}... ({entry.job_count} vagas)")
        
        elif choice == "4":  # Por localização
            location = input(f"{Colors.BOLD}Digite a localização: {Colors.RESET}").strip()
            if location:
                results = cache.search_cache({'locations': [location]})
                print(f"\n{Colors.BOLD}📍 Vagas em '{location}' ({len(results)} encontradas):{Colors.RESET}")
                
                for i, entry in enumerate(results[:5], 1):
                    print(f"  {i}. {entry.url[:50]}... ({entry.job_count} vagas)")
        
        elif choice == "5":  # Estatísticas
            cache.print_compression_report()
            cache.index.print_summary()
        
        elif choice == "6":  # Top rankings
            print(f"\n{Colors.BOLD}🏆 TOP RANKINGS:{Colors.RESET}")
            
            print(f"\n{Colors.BOLD}🏢 TOP 10 EMPRESAS:{Colors.RESET}")
            top_companies = cache.get_top_companies(10)
            for i, (company, count) in enumerate(top_companies, 1):
                print(f"   {i:2d}. {Colors.GREEN}{company}{Colors.RESET}: {count} vagas")
            
            print(f"\n{Colors.BOLD}💻 TOP 10 TECNOLOGIAS:{Colors.RESET}")
            top_techs = cache.get_top_technologies(10)
            for i, (tech, count) in enumerate(top_techs, 1):
                print(f"   {i:2d}. {Colors.BLUE}{tech}{Colors.RESET}: {count} vagas")
        
        print(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
        input()
        
    except Exception as e:
        menu.print_error_message(f"Erro ao acessar cache: {e}")
        input()


async def handle_clean_data():
    """Limpa dados do sistema"""
    menu = MenuSystem()
    
    menu.print_warning_message("ATENÇÃO: Isso removerá todos os dados armazenados!")
    
    if menu.get_user_bool("Tem certeza que deseja continuar?", False):
        import shutil
        
        # Remover diretórios de cache e checkpoint
        directories_to_clean = [
            "data/cache",
            "data/checkpoints"
        ]
        
        # Remover também arquivos de deduplicação
        files_to_clean = [
            "data/deduplication_stats.json",
            "data/known_jobs.json"
        ]
        
        cleaned = 0
        for directory in directories_to_clean:
            if os.path.exists(directory):
                try:
                    shutil.rmtree(directory)
                    print(f"✅ {directory} removido")
                    cleaned += 1
                except Exception as e:
                    print(f"❌ Erro ao remover {directory}: {e}")
        
        # Remover arquivos de deduplicação
        for file_path in files_to_clean:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"✅ {file_path} removido")
                    cleaned += 1
                except Exception as e:
                    print(f"❌ Erro ao remover {file_path}: {e}")
        
        if cleaned > 0:
            menu.print_success_message(f"Cache limpo! {cleaned} itens removidos")
            print("🔄 Agora o scraping processará todas as páginas do zero")
        else:
            menu.print_info_message("Nenhum cache encontrado para limpar")
    else:
        menu.print_info_message("Limpeza cancelada")
    
    print(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    input()


async def handle_deduplication():
    """Executa deduplicação de arquivos"""
    menu = MenuSystem()
    
    print(f"\n{Colors.BOLD}🧹 SISTEMA DE DEDUPLICAÇÃO{Colors.RESET}")
    print("Esta operação irá:")
    print("  • Escanear todos os arquivos JSON em data/")
    print("  • Remover vagas duplicadas")
    print("  • Criar backup dos arquivos originais (.bak)")
    print("  • Exibir relatório detalhado")
    
    if menu.get_user_bool("Deseja continuar?", True):
        try:
            from src.systems.deduplicator import JobDeduplicator
            
            deduplicator = JobDeduplicator()
            removed_count = deduplicator.clean_existing_files("data")
            
            if removed_count > 0:
                menu.print_success_message(f"Deduplicação concluída: {removed_count} duplicatas removidas!")
                deduplicator.print_stats()
            else:
                menu.print_info_message("Nenhuma duplicata encontrada ou nenhum arquivo para processar")
        except Exception as e:
            menu.print_error_message(f"Erro durante deduplicação: {e}")
    else:
        menu.print_info_message("Deduplicação cancelada")
    
    print(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    input()


async def start_api_server():
    """Inicia servidor da API"""
    menu = MenuSystem()
    
    menu.print_info_message("Iniciando servidor da API REST...")
    print(f"\n{Colors.BOLD}🌐 SERVIDOR API{Colors.RESET}")
    print("  • FastAPI com documentação automática")
    print("  • Autenticação JWT")
    print("  • Background tasks para scraping")
    print("  • Rate limiting e monitoramento")
    print()
    
    try:
        import uvicorn
        from api.main import app
        
        print(f"{Colors.GREEN}🚀 Iniciando API em http://localhost:8000{Colors.RESET}")
        print(f"{Colors.BLUE}📚 Documentação: http://localhost:8000/docs{Colors.RESET}")
        print(f"{Colors.CYAN}📖 ReDoc: http://localhost:8000/redoc{Colors.RESET}")
        print()
        print(f"{Colors.DIM}Pressione Ctrl+C para parar o servidor{Colors.RESET}")
        
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError:
        menu.print_error_message("Dependências da API não encontradas")
        menu.print_info_message("Execute: pip install uvicorn fastapi")
    except Exception as e:
        menu.print_error_message(f"Erro ao iniciar API: {e}")
    
    print(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    input()


async def handle_cv_analysis():
    """Gerencia o menu de análise de CV"""
    try:
        from src.utils.cv_interface import run_cv_interface
        run_cv_interface()
    except Exception as e:
        menu = MenuSystem()
        menu.print_error_message(f"Erro no sistema de análise de CV: {e}")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def handle_settings_menu():
    """Gerencia o menu de configurações avançadas"""
    try:
        settings_ui.show_main_settings_menu()
    except Exception as e:
        menu = MenuSystem()
        menu.print_error_message(f"Erro no sistema de configurações: {e}")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def handle_statistics_dashboard():
    """Exibe dashboard completo de estatísticas"""
    menu = MenuSystem()
    
    while True:
        try:
            choice = await show_statistics_menu(menu)
            
            if choice == "0":  # Voltar
                break
            elif choice == "1":  # Visão Geral
                await show_general_overview(menu)
            elif choice == "2":  # Análise de Vagas
                await show_job_analysis(menu)
            elif choice == "3":  # Tecnologias
                await show_technology_stats(menu)
            elif choice == "4":  # Empresas
                await show_company_stats(menu)
            elif choice == "5":  # Localização
                await show_location_stats(menu)
            elif choice == "6":  # Salários
                await show_salary_stats(menu)
            elif choice == "7":  # Cache e Performance
                await show_performance_stats(menu)
            elif choice == "8":  # Histórico
                await show_historical_data(menu)
                
        except Exception as e:
            menu.print_error_message(f"Erro no dashboard: {e}")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def show_statistics_menu(menu):
    """Mostra menu principal de estatísticas"""
    menu.clear_screen()
    
    print(f"{Colors.BOLD}{Colors.BLUE}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}║{Colors.RESET}                    {Colors.BOLD}{Colors.WHITE}📊 DASHBOARD DE ESTATÍSTICAS - v4.0.0{Colors.RESET}                    {Colors.BOLD}{Colors.BLUE}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}║{Colors.RESET}                {Colors.GREEN}Sistema Completo de Análise e Métricas{Colors.RESET}                 {Colors.BOLD}{Colors.BLUE}║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    
    # Status rápido do sistema
    await print_quick_stats(menu)
    
    # Menu de opções
    print(f"{Colors.BOLD}📋 CATEGORIAS DE ANÁLISE{Colors.RESET}")
    print()
    
    print(f"{Colors.DIM}┌─ Análises Principais ───────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[1]{Colors.RESET} 🎯 VISÃO GERAL      │ Métricas gerais do sistema e resumo    {Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[2]{Colors.RESET} 💼 ANÁLISE DE VAGAS │ Distribuição, níveis, modalidades      {Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[3]{Colors.RESET} 💻 TECNOLOGIAS      │ Stack mais demandado, tendências        {Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[4]{Colors.RESET} 🏢 EMPRESAS         │ Top contratantes, distribuição          {Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()
    
    print(f"{Colors.DIM}┌─ Análises Detalhadas ───────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[5]{Colors.RESET} 📍 LOCALIZAÇÃO      │ Distribuição geográfica de vagas        {Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[6]{Colors.RESET} 💰 SALÁRIOS         │ Faixas salariais, análise por nível     {Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[7]{Colors.RESET} ⚡ PERFORMANCE      │ Cache, tempos, eficiência do sistema    {Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[8]{Colors.RESET} 📈 HISTÓRICO        │ Evolução temporal e tendências          {Colors.DIM}│{Colors.RESET}")
    print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()
    
    print(f"  {Colors.BOLD}[0]{Colors.RESET} ⬅️  VOLTAR          Retornar ao menu principal")
    print()
    
    return menu.get_user_choice("Escolha uma categoria", "0", 
                               ["0", "1", "2", "3", "4", "5", "6", "7", "8"])


async def print_quick_stats(menu):
    """Imprime estatísticas rápidas no cabeçalho"""
    try:
        # Contar arquivos de resultados
        import os
        import json
        from pathlib import Path
        
        results_dir = Path("data/resultados/json")
        total_files = 0
        total_jobs = 0
        latest_date = "N/A"
        
        if results_dir.exists():
            files = list(results_dir.glob("*.json"))
            total_files = len(files)
            
            # Contar total de vagas e encontrar data mais recente
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        total_jobs += len(data)
                    
                    # Extrair data do nome do arquivo
                    if "_" in file_path.name:
                        date_part = file_path.name.split("_")[-1].replace(".json", "")
                        if len(date_part) >= 8:
                            formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                            if latest_date == "N/A" or formatted_date > latest_date:
                                latest_date = formatted_date
                except:
                    continue
        
        # Cache info
        cache_dir = Path("data/cache")
        cache_files = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0
        
        # Status do sistema
        print(f"{Colors.DIM}┌─ Status Rápido ─────────────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}📊 Total de Vagas:{Colors.RESET} {Colors.GREEN}{total_jobs:,}{Colors.RESET}{' ' * max(0, 15-len(f'{total_jobs:,}'))} │ {Colors.BOLD}📅 Última Coleta:{Colors.RESET} {Colors.CYAN}{latest_date}{Colors.RESET}{' ' * max(0, 15-len(latest_date))} {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}📁 Arquivos:{Colors.RESET} {Colors.YELLOW}{total_files}{Colors.RESET}{' ' * max(0, 20-len(str(total_files)))} │ {Colors.BOLD}💾 Cache:{Colors.RESET} {Colors.BLUE}{cache_files} arquivo(s){Colors.RESET}{' ' * max(0, 15-len(f'{cache_files} arquivo(s)'))} {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()
        
    except Exception as e:
        print(f"{Colors.DIM}┌─ Status Rápido ─────────────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.RED}❌ Erro ao carregar estatísticas rápidas: {str(e)[:40]}...{Colors.RESET}{' ' * 20} {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()


async def show_general_overview(menu):
    """Exibe visão geral do sistema"""
    menu.clear_screen()
    
    print(f"{Colors.BOLD}{Colors.GREEN}🎯 VISÃO GERAL DO SISTEMA{Colors.RESET}")
    print()
    
    try:
        import json
        from pathlib import Path
        from datetime import datetime
        
        # Carregar todos os dados
        all_jobs = []
        results_dir = Path("data/resultados/json")
        
        if results_dir.exists():
            for file_path in results_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_jobs.extend(data)
                except:
                    continue
        
        total_jobs = len(all_jobs)
        
        if total_jobs == 0:
            menu.print_warning_message("Nenhum dado encontrado. Execute o scraping primeiro.")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Análises gerais
        print(f"{Colors.BOLD}📊 MÉTRICAS GERAIS{Colors.RESET}")
        print(f"   Total de vagas coletadas: {Colors.GREEN}{total_jobs:,}{Colors.RESET}")
        
        # Tecnologias mais demandadas
        tech_count = {}
        for job in all_jobs:
            for tech in job.get('tecnologias_detectadas', []):
                tech_count[tech] = tech_count.get(tech, 0) + 1
        
        if tech_count:
            print(f"\n{Colors.BOLD}💻 TOP 10 TECNOLOGIAS MAIS DEMANDADAS{Colors.RESET}")
            for i, (tech, count) in enumerate(sorted(tech_count.items(), key=lambda x: x[1], reverse=True)[:10], 1):
                percentage = (count / total_jobs) * 100
                print(f"   {i:2d}. {Colors.CYAN}{tech:<20}{Colors.RESET} {Colors.GREEN}{count:4d}{Colors.RESET} vagas ({percentage:4.1f}%)")
        
        # Empresas que mais contratam
        company_count = {}
        for job in all_jobs:
            company = job.get('empresa', 'N/A')
            if company and company != 'N/A':
                company_count[company] = company_count.get(company, 0) + 1
        
        if company_count:
            print(f"\n{Colors.BOLD}🏢 TOP 10 EMPRESAS QUE MAIS CONTRATAM{Colors.RESET}")
            for i, (company, count) in enumerate(sorted(company_count.items(), key=lambda x: x[1], reverse=True)[:10], 1):
                print(f"   {i:2d}. {Colors.YELLOW}{company[:30]:<30}{Colors.RESET} {Colors.GREEN}{count:3d}{Colors.RESET} vagas")
        
        # Modalidades de trabalho
        modalidade_count = {}
        for job in all_jobs:
            modalidade = job.get('modalidade_trabalho', 'N/A')
            modalidade_count[modalidade] = modalidade_count.get(modalidade, 0) + 1
        
        if modalidade_count:
            print(f"\n{Colors.BOLD}🏠 MODALIDADES DE TRABALHO{Colors.RESET}")
            for modalidade, count in sorted(modalidade_count.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_jobs) * 100
                print(f"   • {Colors.BLUE}{modalidade:<20}{Colors.RESET} {Colors.GREEN}{count:4d}{Colors.RESET} vagas ({percentage:4.1f}%)")
        
        # Níveis de experiência
        nivel_count = {}
        for job in all_jobs:
            nivel = job.get('nivel_categorizado', 'N/A')
            nivel_count[nivel] = nivel_count.get(nivel, 0) + 1
        
        if nivel_count:
            print(f"\n{Colors.BOLD}📈 DISTRIBUIÇÃO POR NÍVEL{Colors.RESET}")
            for nivel, count in sorted(nivel_count.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_jobs) * 100
                nivel_display = nivel.replace('_', ' ').title() if nivel != 'N/A' else 'Não Categorizado'
                print(f"   • {Colors.MAGENTA}{nivel_display:<20}{Colors.RESET} {Colors.GREEN}{count:4d}{Colors.RESET} vagas ({percentage:4.1f}%)")
        
    except Exception as e:
        menu.print_error_message(f"Erro ao gerar visão geral: {e}")
    
    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def show_job_analysis(menu):
    """Análise detalhada de vagas"""
    menu.clear_screen()
    
    print(f"{Colors.BOLD}{Colors.BLUE}💼 ANÁLISE DETALHADA DE VAGAS{Colors.RESET}")
    print()
    
    try:
        import json
        from pathlib import Path
        
        # Carregar dados
        all_jobs = []
        results_dir = Path("data/resultados/json")
        
        if results_dir.exists():
            for file_path in results_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_jobs.extend(data)
                except:
                    continue
        
        if not all_jobs:
            menu.print_warning_message("Nenhum dado encontrado.")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        total_jobs = len(all_jobs)
        
        # Análise de descrições
        desc_stats = {
            'with_description': 0,
            'avg_length': 0,
            'with_requirements': 0,
            'with_benefits': 0
        }
        
        total_length = 0
        for job in all_jobs:
            desc = job.get('descricao', '')
            if desc and desc.strip():
                desc_stats['with_description'] += 1
                total_length += len(desc)
                
                if any(word in desc.lower() for word in ['requisito', 'experiência', 'conhecimento']):
                    desc_stats['with_requirements'] += 1
                    
                if any(word in desc.lower() for word in ['benefício', 'vale', 'plano', 'convênio']):
                    desc_stats['with_benefits'] += 1
        
        if desc_stats['with_description'] > 0:
            desc_stats['avg_length'] = total_length // desc_stats['with_description']
        
        print(f"{Colors.BOLD}📄 QUALIDADE DOS DADOS{Colors.RESET}")
        print(f"   Vagas com descrição: {Colors.GREEN}{desc_stats['with_description']:,}{Colors.RESET} ({(desc_stats['with_description']/total_jobs)*100:.1f}%)")
        print(f"   Tamanho médio da descrição: {Colors.CYAN}{desc_stats['avg_length']:,}{Colors.RESET} caracteres")
        print(f"   Com requisitos detalhados: {Colors.YELLOW}{desc_stats['with_requirements']:,}{Colors.RESET} ({(desc_stats['with_requirements']/total_jobs)*100:.1f}%)")
        print(f"   Com benefícios mencionados: {Colors.BLUE}{desc_stats['with_benefits']:,}{Colors.RESET} ({(desc_stats['with_benefits']/total_jobs)*100:.1f}%)")
        
        # Análise de campos obrigatórios
        print(f"\n{Colors.BOLD}✅ COMPLETUDE DOS DADOS{Colors.RESET}")
        fields_analysis = {
            'titulo': 'Título da vaga',
            'empresa': 'Nome da empresa',
            'localizacao': 'Localização',
            'modalidade_trabalho': 'Modalidade de trabalho',
            'tecnologias_detectadas': 'Tecnologias'
        }
        
        for field, label in fields_analysis.items():
            count = sum(1 for job in all_jobs if job.get(field) and str(job.get(field)).strip() not in ['', 'N/A', '[]'])
            percentage = (count / total_jobs) * 100
            print(f"   {label:<25}: {Colors.GREEN if percentage > 80 else Colors.YELLOW if percentage > 50 else Colors.RED}{count:,}{Colors.RESET} ({percentage:5.1f}%)")
        
        # Distribuição temporal (se tiver dados de data)
        dates_found = []
        for job in all_jobs:
            date_str = job.get('data_coleta', '')
            if date_str:
                try:
                    dates_found.append(date_str[:10])  # YYYY-MM-DD
                except:
                    continue
        
        if dates_found:
            from collections import Counter
            date_counts = Counter(dates_found)
            print(f"\n{Colors.BOLD}📅 DISTRIBUIÇÃO TEMPORAL{Colors.RESET}")
            for date, count in sorted(date_counts.items(), reverse=True)[:7]:
                print(f"   {date}: {Colors.GREEN}{count:,}{Colors.RESET} vagas")
        
    except Exception as e:
        menu.print_error_message(f"Erro na análise de vagas: {e}")
    
    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def show_technology_stats(menu):
    """Estatísticas de tecnologias"""
    menu.clear_screen()
    
    print(f"{Colors.BOLD}{Colors.CYAN}💻 ANÁLISE DE TECNOLOGIAS{Colors.RESET}")
    print()
    
    try:
        import json
        from pathlib import Path
        from collections import Counter
        
        # Carregar dados
        all_jobs = []
        results_dir = Path("data/resultados/json")
        
        if results_dir.exists():
            for file_path in results_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_jobs.extend(data)
                except:
                    continue
        
        if not all_jobs:
            menu.print_warning_message("Nenhum dado encontrado.")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Análise de tecnologias
        all_techs = []
        for job in all_jobs:
            techs = job.get('tecnologias_detectadas', [])
            all_techs.extend(techs)
        
        tech_counter = Counter(all_techs)
        total_jobs = len(all_jobs)
        
        if tech_counter:
            print(f"{Colors.BOLD}🏆 TOP 20 TECNOLOGIAS MAIS DEMANDADAS{Colors.RESET}")
            print()
            
            # Categorizar tecnologias
            categories = {
                'languages': ['Python', 'Java', 'JavaScript', 'C#', 'PHP', 'Ruby', 'Go', 'Rust', 'C++', 'TypeScript'],
                'frameworks': ['React', 'Angular', 'Vue', 'Django', 'Flask', 'Spring', 'Laravel', 'Express'],
                'databases': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQL Server'],
                'cloud': ['AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes'],
                'tools': ['Git', 'Jenkins', 'Jira', 'Confluence']
            }
            
            for i, (tech, count) in enumerate(tech_counter.most_common(20), 1):
                percentage = (count / total_jobs) * 100
                
                # Determinar categoria
                category = '🔧'
                for cat, items in categories.items():
                    if any(item.lower() in tech.lower() for item in items):
                        if cat == 'languages':
                            category = '🐍'
                        elif cat == 'frameworks':
                            category = '⚛️'
                        elif cat == 'databases':
                            category = '💾'
                        elif cat == 'cloud':
                            category = '☁️'
                        break
                
                print(f"   {i:2d}. {category} {Colors.CYAN}{tech:<25}{Colors.RESET} {Colors.GREEN}{count:4d}{Colors.RESET} vagas ({percentage:5.1f}%)")
            
            # Análise por categoria
            print(f"\n{Colors.BOLD}📊 ANÁLISE POR CATEGORIA{Colors.RESET}")
            category_stats = {cat: 0 for cat in categories.keys()}
            
            for tech, count in tech_counter.items():
                for cat, items in categories.items():
                    if any(item.lower() in tech.lower() for item in items):
                        category_stats[cat] += count
                        break
            
            category_names = {
                'languages': 'Linguagens de Programação',
                'frameworks': 'Frameworks e Bibliotecas',
                'databases': 'Bancos de Dados',
                'cloud': 'Cloud e DevOps',
                'tools': 'Ferramentas de Desenvolvimento'
            }
            
            for cat, total in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
                if total > 0:
                    print(f"   {category_names[cat]:<30}: {Colors.GREEN}{total:4d}{Colors.RESET} menções")
        
    except Exception as e:
        menu.print_error_message(f"Erro na análise de tecnologias: {e}")
    
    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def show_company_stats(menu):
    """Estatísticas de empresas"""
    menu.clear_screen()
    
    print(f"{Colors.BOLD}{Colors.YELLOW}🏢 ANÁLISE DE EMPRESAS{Colors.RESET}")
    print()
    
    try:
        import json
        from pathlib import Path
        from collections import Counter
        
        # Carregar dados
        all_jobs = []
        results_dir = Path("data/resultados/json")
        
        if results_dir.exists():
            for file_path in results_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_jobs.extend(data)
                except:
                    continue
        
        if not all_jobs:
            menu.print_warning_message("Nenhum dado encontrado.")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Análise de empresas
        companies = [job.get('empresa', 'N/A') for job in all_jobs if job.get('empresa') and job.get('empresa') != 'N/A']
        company_counter = Counter(companies)
        total_jobs = len(all_jobs)
        total_companies = len(company_counter)
        
        print(f"{Colors.BOLD}📈 ESTATÍSTICAS GERAIS{Colors.RESET}")
        print(f"   Total de empresas únicas: {Colors.GREEN}{total_companies:,}{Colors.RESET}")
        print(f"   Média de vagas por empresa: {Colors.CYAN}{len(companies)/total_companies:.1f}{Colors.RESET}")
        
        if company_counter:
            print(f"\n{Colors.BOLD}🏆 TOP 15 EMPRESAS QUE MAIS CONTRATAM{Colors.RESET}")
            print()
            
            for i, (company, count) in enumerate(company_counter.most_common(15), 1):
                percentage = (count / total_jobs) * 100
                company_display = company[:40] + "..." if len(company) > 40 else company
                
                # Determinar porte da empresa baseado no número de vagas
                if count >= 50:
                    size_icon = "🏭"  # Grande porte
                elif count >= 20:
                    size_icon = "🏢"  # Médio porte
                elif count >= 5:
                    size_icon = "🏪"  # Pequeno/Médio porte
                else:
                    size_icon = "🏬"  # Pequeno porte
                
                print(f"   {i:2d}. {size_icon} {Colors.YELLOW}{company_display:<42}{Colors.RESET} {Colors.GREEN}{count:3d}{Colors.RESET} vagas ({percentage:4.1f}%)")
            
            # Análise de distribuição
            print(f"\n{Colors.BOLD}📊 DISTRIBUIÇÃO DE VAGAS POR EMPRESA{Colors.RESET}")
            
            # Categorias de empresas por número de vagas
            categories = {
                'Grandes (50+ vagas)': len([c for c in company_counter.values() if c >= 50]),
                'Médias (20-49 vagas)': len([c for c in company_counter.values() if 20 <= c < 50]),
                'Pequenas (5-19 vagas)': len([c for c in company_counter.values() if 5 <= c < 20]),
                'Micro (1-4 vagas)': len([c for c in company_counter.values() if 1 <= c < 5])
            }
            
            for category, count in categories.items():
                percentage = (count / total_companies) * 100 if total_companies > 0 else 0
                print(f"   {category:<20}: {Colors.BLUE}{count:3d}{Colors.RESET} empresas ({percentage:4.1f}%)")
        
    except Exception as e:
        menu.print_error_message(f"Erro na análise de empresas: {e}")
    
    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def show_location_stats(menu):
    """Estatísticas de localização"""
    menu.clear_screen()
    
    print(f"{Colors.BOLD}{Colors.MAGENTA}📍 ANÁLISE DE LOCALIZAÇÃO{Colors.RESET}")
    print()
    
    try:
        import json
        from pathlib import Path
        from collections import Counter
        
        # Carregar dados
        all_jobs = []
        results_dir = Path("data/resultados/json")
        
        if results_dir.exists():
            for file_path in results_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_jobs.extend(data)
                except:
                    continue
        
        if not all_jobs:
            menu.print_warning_message("Nenhum dado encontrado.")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Análise de localização
        locations = []
        states = []
        cities = []
        
        for job in all_jobs:
            location = job.get('localizacao', '')
            if location and location != 'N/A':
                locations.append(location)
                
                # Tentar extrair estado e cidade
                if ',' in location:
                    parts = location.split(',')
                    if len(parts) >= 2:
                        city = parts[0].strip()
                        state = parts[-1].strip()
                        cities.append(city)
                        states.append(state)
        
        location_counter = Counter(locations)
        state_counter = Counter(states)
        city_counter = Counter(cities)
        total_jobs = len(all_jobs)
        
        print(f"{Colors.BOLD}🗺️ DISTRIBUIÇÃO GEOGRÁFICA{Colors.RESET}")
        
        if state_counter:
            print(f"\n{Colors.BOLD}🏛️ TOP 10 ESTADOS{Colors.RESET}")
            for i, (state, count) in enumerate(state_counter.most_common(10), 1):
                percentage = (count / total_jobs) * 100
                print(f"   {i:2d}. {Colors.MAGENTA}{state:<20}{Colors.RESET} {Colors.GREEN}{count:4d}{Colors.RESET} vagas ({percentage:5.1f}%)")
        
        if city_counter:
            print(f"\n{Colors.BOLD}🏙️ TOP 15 CIDADES{Colors.RESET}")
            for i, (city, count) in enumerate(city_counter.most_common(15), 1):
                percentage = (count / total_jobs) * 100
                print(f"   {i:2d}. {Colors.CYAN}{city:<25}{Colors.RESET} {Colors.GREEN}{count:4d}{Colors.RESET} vagas ({percentage:5.1f}%)")
        
        # Análise de modalidade por localização
        remote_keywords = ['remoto', 'home office', 'home-office', 'remota']
        hybrid_keywords = ['híbrido', 'hibrido']
        
        remote_count = 0
        hybrid_count = 0
        onsite_count = 0
        
        for job in all_jobs:
            modalidade = job.get('modalidade_trabalho', '').lower()
            location = job.get('localizacao', '').lower()
            
            if any(keyword in modalidade or keyword in location for keyword in remote_keywords):
                remote_count += 1
            elif any(keyword in modalidade for keyword in hybrid_keywords):
                hybrid_count += 1
            else:
                onsite_count += 1
        
        print(f"\n{Colors.BOLD}🏠 MODALIDADES DE TRABALHO{Colors.RESET}")
        total_classified = remote_count + hybrid_count + onsite_count
        if total_classified > 0:
            print(f"   Remoto: {Colors.GREEN}{remote_count:4d}{Colors.RESET} vagas ({(remote_count/total_classified)*100:5.1f}%)")
            print(f"   Híbrido: {Colors.YELLOW}{hybrid_count:4d}{Colors.RESET} vagas ({(hybrid_count/total_classified)*100:5.1f}%)")
            print(f"   Presencial: {Colors.BLUE}{onsite_count:4d}{Colors.RESET} vagas ({(onsite_count/total_classified)*100:5.1f}%)")
        
    except Exception as e:
        menu.print_error_message(f"Erro na análise de localização: {e}")
    
    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def show_salary_stats(menu):
    """Estatísticas de salários"""
    menu.clear_screen()
    
    print(f"{Colors.BOLD}{Colors.GREEN}💰 ANÁLISE DE SALÁRIOS{Colors.RESET}")
    print()
    
    menu.print_info_message("Análise de salários ainda não implementada - dados de salário não coletados sistematicamente.")
    print("\n💡 Esta funcionalidade será implementada quando o scraper começar a coletar dados salariais.")
    
    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def show_performance_stats(menu):
    """Estatísticas de performance do sistema"""
    menu.clear_screen()
    
    print(f"{Colors.BOLD}{Colors.RED}⚡ PERFORMANCE E CACHE{Colors.RESET}")
    print()
    
    try:
        import json
        import os
        from pathlib import Path
        
        # Análise do cache
        cache_dir = Path("data/cache")
        cache_stats = {
            'total_files': 0,
            'total_size': 0,
            'index_size': 0
        }
        
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.json"))
            cache_stats['total_files'] = len(cache_files)
            
            for file_path in cache_files:
                try:
                    cache_stats['total_size'] += file_path.stat().st_size
                except:
                    continue
            
            # Verificar índice do cache
            index_file = cache_dir / "cache_index.json"
            if index_file.exists():
                cache_stats['index_size'] = index_file.stat().st_size
        
        # Análise dos checkpoints
        checkpoint_dir = Path("data/checkpoints")
        checkpoint_stats = {
            'incremental_available': False,
            'stats_available': False
        }
        
        if checkpoint_dir.exists():
            checkpoint_stats['incremental_available'] = (checkpoint_dir / "incremental_checkpoint.json").exists()
            checkpoint_stats['stats_available'] = (checkpoint_dir / "incremental_stats.json").exists()
        
        # Análise dos resultados
        results_dir = Path("data/resultados")
        results_stats = {
            'json_files': 0,
            'csv_files': 0,
            'txt_files': 0,
            'total_size': 0
        }
        
        if results_dir.exists():
            results_stats['json_files'] = len(list((results_dir / "json").glob("*.json"))) if (results_dir / "json").exists() else 0
            results_stats['csv_files'] = len(list((results_dir / "csv").glob("*.csv"))) if (results_dir / "csv").exists() else 0
            results_stats['txt_files'] = len(list((results_dir / "txt").glob("*.txt"))) if (results_dir / "txt").exists() else 0
            
            for subdir in results_dir.iterdir():
                if subdir.is_dir():
                    for file_path in subdir.rglob("*"):
                        if file_path.is_file():
                            try:
                                results_stats['total_size'] += file_path.stat().st_size
                            except:
                                continue
        
        # Exibir estatísticas
        print(f"{Colors.BOLD}💾 ESTATÍSTICAS DE CACHE{Colors.RESET}")
        print(f"   Arquivos de cache: {Colors.CYAN}{cache_stats['total_files']}{Colors.RESET}")
        print(f"   Tamanho total: {Colors.GREEN}{cache_stats['total_size']/1024/1024:.1f}{Colors.RESET} MB")
        print(f"   Índice: {Colors.YELLOW}{cache_stats['index_size']/1024:.1f}{Colors.RESET} KB")
        
        print(f"\n{Colors.BOLD}🔄 SISTEMA INCREMENTAL{Colors.RESET}")
        checkpoint_status = f"{Colors.GREEN}✅ Ativo{Colors.RESET}" if checkpoint_stats['incremental_available'] else f"{Colors.RED}❌ Inativo{Colors.RESET}"
        stats_status = f"{Colors.GREEN}✅ Disponível{Colors.RESET}" if checkpoint_stats['stats_available'] else f"{Colors.RED}❌ Indisponível{Colors.RESET}"
        print(f"   Checkpoint incremental: {checkpoint_status}")
        print(f"   Estatísticas: {stats_status}")
        
        print(f"\n{Colors.BOLD}📁 ARQUIVOS DE RESULTADOS{Colors.RESET}")
        print(f"   Arquivos JSON: {Colors.GREEN}{results_stats['json_files']}{Colors.RESET}")
        print(f"   Arquivos CSV: {Colors.BLUE}{results_stats['csv_files']}{Colors.RESET}")
        print(f"   Arquivos TXT: {Colors.YELLOW}{results_stats['txt_files']}{Colors.RESET}")
        print(f"   Tamanho total: {Colors.MAGENTA}{results_stats['total_size']/1024/1024:.1f}{Colors.RESET} MB")
        
        # Eficiência do sistema
        if checkpoint_stats['stats_available']:
            try:
                with open("data/checkpoints/incremental_stats.json", 'r') as f:
                    stats_data = json.load(f)
                
                print(f"\n{Colors.BOLD}📊 EFICIÊNCIA DO SISTEMA{Colors.RESET}")
                if 'deduplication' in stats_data:
                    dedup_stats = stats_data['deduplication']
                    print(f"   Duplicatas removidas: {Colors.RED}{dedup_stats.get('duplicates_removed', 0):,}{Colors.RESET}")
                    print(f"   Taxa de duplicação: {Colors.YELLOW}{dedup_stats.get('duplication_rate', 0):.1f}%{Colors.RESET}")
                
                if 'compression' in stats_data:
                    comp_stats = stats_data['compression']
                    print(f"   Compressão de dados: {Colors.CYAN}{comp_stats.get('compression_ratio', 0):.1f}%{Colors.RESET}")
                
            except Exception as e:
                print(f"\n{Colors.RED}❌ Erro ao carregar estatísticas incrementais: {e}{Colors.RESET}")
        
    except Exception as e:
        menu.print_error_message(f"Erro na análise de performance: {e}")
    
    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def show_historical_data(menu):
    """Mostra dados históricos e tendências"""
    menu.clear_screen()
    
    print(f"{Colors.BOLD}{Colors.PURPLE}📈 ANÁLISE HISTÓRICA{Colors.RESET}")
    print()
    
    try:
        import json
        from pathlib import Path
        from collections import defaultdict
        from datetime import datetime
        
        # Carregar dados por arquivo (representando diferentes datas)
        results_dir = Path("data/resultados/json")
        historical_data = {}
        
        if results_dir.exists():
            for file_path in results_dir.glob("*.json"):
                try:
                    # Extrair data do nome do arquivo
                    filename = file_path.name
                    if "_" in filename:
                        date_part = filename.split("_")[-1].replace(".json", "")
                        if len(date_part) >= 8:
                            date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                            
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            if isinstance(data, list):
                                historical_data[date_str] = {
                                    'total_jobs': len(data),
                                    'jobs': data,
                                    'file': filename
                                }
                except:
                    continue
        
        if not historical_data:
            menu.print_warning_message("Nenhum dado histórico encontrado.")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Ordenar por data
        sorted_dates = sorted(historical_data.keys())
        
        print(f"{Colors.BOLD}📅 EVOLUÇÃO TEMPORAL{Colors.RESET}")
        print()
        
        print(f"{'Data':<12} {'Vagas':<8} {'Arquivo':<30} {'Tendência'}")
        print("-" * 65)
        
        prev_count = 0
        for i, date in enumerate(sorted_dates):
            data = historical_data[date]
            count = data['total_jobs']
            
            # Calcular tendência
            if i == 0:
                trend = "📊"
            elif count > prev_count:
                trend = f"📈 +{count - prev_count}"
            elif count < prev_count:
                trend = f"📉 -{prev_count - count}"
            else:
                trend = "➡️ =0"
            
            print(f"{Colors.CYAN}{date}{Colors.RESET}   {Colors.GREEN}{count:>6,}{Colors.RESET}   {Colors.GRAY}{data['file'][:28]:<28}{Colors.RESET} {trend}")
            prev_count = count
        
        # Análise de tecnologias ao longo do tempo
        tech_timeline = defaultdict(lambda: defaultdict(int))
        
        for date, data in historical_data.items():
            for job in data['jobs']:
                for tech in job.get('tecnologias_detectadas', []):
                    tech_timeline[tech][date] += 1
        
        # Mostrar evolução das top 5 tecnologias
        if tech_timeline:
            print(f"\n{Colors.BOLD}💻 EVOLUÇÃO DAS TOP 5 TECNOLOGIAS{Colors.RESET}")
            
            # Calcular total por tecnologia
            tech_totals = {tech: sum(dates.values()) for tech, dates in tech_timeline.items()}
            top_techs = sorted(tech_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for tech, total in top_techs:
                print(f"\n{Colors.BOLD}{tech}{Colors.RESET} (Total: {total} menções)")
                for date in sorted_dates:
                    count = tech_timeline[tech].get(date, 0)
                    if count > 0:
                        print(f"   {date}: {Colors.GREEN}{count:3d}{Colors.RESET} menções")
        
        # Estatísticas gerais
        if len(sorted_dates) > 1:
            first_date = sorted_dates[0]
            last_date = sorted_dates[-1]
            first_count = historical_data[first_date]['total_jobs']
            last_count = historical_data[last_date]['total_jobs']
            
            total_jobs = sum(data['total_jobs'] for data in historical_data.values())
            avg_jobs = total_jobs / len(historical_data)
            
            print(f"\n{Colors.BOLD}📊 RESUMO ESTATÍSTICO{Colors.RESET}")
            print(f"   Período analisado: {Colors.CYAN}{first_date}{Colors.RESET} a {Colors.CYAN}{last_date}{Colors.RESET}")
            print(f"   Total de coletas: {Colors.GREEN}{len(historical_data)}{Colors.RESET}")
            print(f"   Total de vagas: {Colors.GREEN}{total_jobs:,}{Colors.RESET}")
            print(f"   Média por coleta: {Colors.YELLOW}{avg_jobs:.1f}{Colors.RESET}")
            
            if first_count != last_count:
                growth = ((last_count - first_count) / first_count) * 100
                growth_color = Colors.GREEN if growth > 0 else Colors.RED
                growth_symbol = "📈" if growth > 0 else "📉"
                print(f"   Crescimento: {growth_color}{growth:+.1f}%{Colors.RESET} {growth_symbol}")
        
    except Exception as e:
        menu.print_error_message(f"Erro na análise histórica: {e}")
    
    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def main():
    """Função principal com menu melhorado"""
    menu = MenuSystem()
    
    while True:
        try:
            choice = menu.print_main_menu()
            
            if choice == "0":  # Sair
                menu.print_info_message("Obrigado por usar o Catho Job Scraper!")
                break
                
            elif choice == "1":  # Novo scraping
                config = menu.print_scraping_menu()
                if config:
                    await run_scraping_with_config(config)
                    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
                
            elif choice == "2":  # Buscar cache
                while True:
                    cache_choice = menu.print_cache_menu()
                    if cache_choice == "0":  # Voltar
                        break
                    else:
                        await handle_cache_operations(cache_choice)
                
            elif choice == "3":  # Análise de CV
                await handle_cv_analysis()
                
            elif choice == "4":  # Limpar dados
                await handle_clean_data()
                
            elif choice == "5":  # Deduplicação
                await handle_deduplication()
                
            elif choice == "6":  # Configurações
                await handle_settings_menu()
                
            elif choice == "7":  # Estatísticas
                await handle_statistics_dashboard()
                
            elif choice == "8":  # API Server
                await start_api_server()
                
            elif choice == "9":  # Ajuda
                menu.print_help_menu()
                
        except KeyboardInterrupt:
            menu.print_info_message("Saindo...")
            break
        except Exception as e:
            menu.print_error_message(f"Erro inesperado: {e}")
            import traceback
            traceback.print_exc()
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Erro fatal: {e}{Colors.RESET}")