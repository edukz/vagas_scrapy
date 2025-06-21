"""
Sistema Catho Job Scraper - Interface Melhorada
Versão com menu interativo e visual - Refatorado com Handlers
"""

import asyncio
import sys
import os
import signal
import atexit

# Adicionar pasta src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), ''))

# Handler robusto para sinais de interrupção no Windows
def setup_signal_handlers():
    """Configura handlers robustos para sinais de interrupção"""
    def signal_handler(sig, frame):
        print(f"\n🛑 Interrompendo aplicação...")
        print(f"Aguarde o fechamento seguro...")
        
        # Força saída limpa
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    
    def cleanup_handler():
        """Handler executado na saída do programa"""
        print(f"\n✅ Aplicação encerrada com sucesso.")
    
    # Registrar handlers para diferentes sinais
    try:
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)  # Ctrl+Break no Windows
        atexit.register(cleanup_handler)
    except Exception as e:
        print(f"Aviso: Não foi possível configurar handlers de sinal: {e}")

# Configurar handlers
setup_signal_handlers()

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


def run_with_error_handling():
    """Wrapper para executar main() com tratamento de erros do Windows"""
    try:
        # Tentar executar normalmente
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print(f"\n🛑 Programa interrompido")
        
    except SystemExit:
        # Exit normal, sem erro
        pass
        
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        
    finally:
        # Forçar saída limpa para evitar erros do Windows
        try:
            import gc
            gc.collect()
            sys.stdout.flush()
            sys.stderr.flush()
        except:
            pass
        
        # Saída final sem exceções
        try:
            sys.exit(0)
        except:
            os._exit(0)


if __name__ == "__main__":
    run_with_error_handling()