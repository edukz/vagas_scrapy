"""
Sistema Catho Job Scraper - Interface Melhorada
Versão com menu interativo e visual - Refatorado com Handlers
"""

import asyncio
import sys
import os

# Adicionar pasta src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), ''))

from src.utils.menu_system import MenuSystem, Colors
from src.handlers.scraping_handler import ScrapingHandler
from src.handlers.cache_handler import CacheHandler
from src.handlers.data_handler import DataHandler
from src.handlers.api_handler import APIHandler
from src.handlers.cv_handler import CVHandler
from src.handlers.settings_handler import SettingsHandler
from src.handlers.statistics_handler import StatisticsHandler


async def main():
    """Função principal com menu melhorado"""
    menu = MenuSystem()
    
    # Inicializar handlers
    scraping_handler = ScrapingHandler()
    cache_handler = CacheHandler()
    data_handler = DataHandler()
    api_handler = APIHandler()
    cv_handler = CVHandler()
    settings_handler = SettingsHandler()
    statistics_handler = StatisticsHandler()
    
    while True:
        try:
            choice = menu.print_main_menu()
            
            if choice == "0":  # Sair
                menu.print_info_message("Obrigado por usar o Catho Job Scraper!")
                break
                
            elif choice == "1":  # Novo scraping
                config = menu.print_scraping_menu()
                if config:
                    await scraping_handler.run_scraping_with_config(config)
                    input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            
            elif choice == "2":  # Buscar cache
                while True:
                    cache_choice = menu.print_cache_menu()
                    if cache_choice == "0":  # Voltar
                        break
                    else:
                        await cache_handler.handle_cache_operations(cache_choice)
            
            elif choice == "3":  # Análise de CV
                await cv_handler.handle_cv_analysis()
                
            elif choice == "4":  # Limpar dados
                await data_handler.handle_clean_data()
                
            elif choice == "5":  # Deduplicação
                await data_handler.handle_deduplication()
                
            elif choice == "6":  # Configurações
                await settings_handler.handle_settings_menu()
                
            elif choice == "7":  # Estatísticas
                await statistics_handler.handle_statistics_dashboard()
                
            elif choice == "8":  # API Server
                await api_handler.start_api_server()
                
            elif choice == "9":  # Ajuda
                menu.print_help_menu()
                
        except KeyboardInterrupt:
            menu.print_info_message("Saindo...")
            break
        except Exception as e:
            menu.print_error_message(f"Erro inesperado: {e}")
            import traceback
            traceback.print_exc()
            try:
                input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            except (KeyboardInterrupt, EOFError):
                break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Erro fatal: {e}{Colors.RESET}")