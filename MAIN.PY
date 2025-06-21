"""
Sistema Catho Job Scraper v6.0 - Interface Principal
====================================================

Sistema completo de Web Scraping + Inteligência Artificial
com interface modernizada, recomendações IA e análise detalhada.

Este é agora o ponto de entrada único do sistema.
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
        print(f"\n{Colors.YELLOW}🛑 Interrompendo aplicação...{Colors.RESET}")
        print(f"{Colors.DIM}Aguarde o fechamento seguro...{Colors.RESET}")
        
        # Força saída limpa
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    
    def cleanup_handler():
        """Handler executado na saída do programa"""
        print(f"\n{Colors.GREEN}✅ Aplicação encerrada com sucesso.{Colors.RESET}")
    
    # Registrar handlers para diferentes sinais
    try:
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)  # Ctrl+Break no Windows
        atexit.register(cleanup_handler)
    except Exception as e:
        print(f"Aviso: Não foi possível configurar handlers de sinal: {e}")

# Configurar handlers antes de importar outras bibliotecas
try:
    from src.utils.enhanced_menu_system import Colors
    setup_signal_handlers()
except ImportError:
    # Fallback se não conseguir importar Colors
    class FallbackColors:
        YELLOW = RESET = DIM = GREEN = ""
    Colors = FallbackColors()
    setup_signal_handlers()

from src.utils.enhanced_menu_system import EnhancedMenuSystem, Colors
from src.handlers.scraping_handler import ScrapingHandler
from src.handlers.cache_handler import CacheHandler
from src.handlers.data_handler import DataHandler
from src.handlers.api_handler import APIHandler
from src.handlers.cv_handler import CVHandler
from src.handlers.settings_handler import SettingsHandler
from src.handlers.statistics_handler import StatisticsHandler


class EnhancedJobScraperApp:
    """
    Aplicação principal do sistema com interface modernizada
    
    Funcionalidades:
    - Menu inteligente com níveis de complexidade
    - Tutorial interativo integrado
    - Acesso simplificado às funcionalidades de IA
    - Sistema de help contextual
    - Navegação intuitiva
    """
    
    def __init__(self):
        self.menu = EnhancedMenuSystem()
        self.current_user_level = self.menu.user_preferences.get("complexity_level", "beginner")
        
        # Inicializar handlers existentes
        self.scraping_handler = ScrapingHandler()
        self.cache_handler = CacheHandler()
        self.data_handler = DataHandler()
        self.api_handler = APIHandler()
        self.cv_handler = CVHandler()
        self.settings_handler = SettingsHandler()
        self.statistics_handler = StatisticsHandler()
        
        # Handler de recomendações (novo)
        self.recommendation_handler = None
        self._load_recommendation_handler()
    
    def _load_recommendation_handler(self):
        """Carrega handler de recomendações se disponível"""
        try:
            from src.handlers.recommendation_handler import RecommendationHandler
            self.recommendation_handler = RecommendationHandler()
        except ImportError:
            print("Sistema de recomendações IA não disponível (dependências ML ausentes)")
    
    async def run(self):
        """Loop principal da aplicação"""
        try:
            # Verificar se é primeira execução
            if self.menu.user_preferences.get("first_time", True):
                self._show_welcome_screen()
            
            while True:
                try:
                    choice = self.menu.print_main_menu()
                    
                    # Primeiro, verificar comandos especiais
                    special_result = self.menu.handle_special_commands(choice)
                    
                    if special_result == "exit":
                        self._show_goodbye_screen()
                        break
                    elif special_result == "handled":
                        continue
                    elif special_result == "refresh":
                        continue
                    
                    # Processar opções numéricas
                    await self._handle_menu_choice(choice)
                    
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}🛑 Interrupção detectada...{Colors.RESET}")
                    self._show_goodbye_screen()
                    break
                except EOFError:
                    print(f"\n{Colors.YELLOW}🛑 Entrada interrompida...{Colors.RESET}")
                    self._show_goodbye_screen()
                    break
                except Exception as e:
                    self.menu.clear_screen()
                    print(f"{Colors.RED}❌ Erro inesperado: {e}{Colors.RESET}")
                    import traceback
                    traceback.print_exc()
                    try:
                        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
                    except (KeyboardInterrupt, EOFError):
                        print(f"\n{Colors.YELLOW}🛑 Saindo devido à interrupção...{Colors.RESET}")
                        break
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 Aplicação interrompida pelo usuário{Colors.RESET}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro fatal na aplicação: {e}{Colors.RESET}")
        finally:
            # Cleanup final
            self._cleanup_application()
    
    def _show_welcome_screen(self):
        """Tela de boas-vindas para novos usuários"""
        self.menu.clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}🎉 BEM-VINDO AO CATHO JOB SCRAPER & AI PLATFORM!{Colors.RESET}")
        print("=" * 60)
        print()
        print("Este sistema oferece funcionalidades avançadas de:")
        print(f"   {Colors.GREEN}🚀 Web Scraping{Colors.RESET} - Coleta inteligente de vagas")
        print(f"   {Colors.PURPLE}🤖 Análise de CV{Colors.RESET} - Extração automática com IA")
        print(f"   {Colors.MAGENTA}💡 Recomendações{Colors.RESET} - Matching CV-Vagas personalizado")
        print(f"   {Colors.CYAN}📊 Business Intelligence{Colors.RESET} - Análise de mercado")
        print()
        print(f"{Colors.YELLOW}🎓 Recomendado para iniciantes:{Colors.RESET}")
        print("   1. Comece com o tutorial interativo")
        print("   2. Use o modo 'Iniciante' com funcionalidades essenciais")
        print("   3. Evolua para modo 'Avançado' conforme aprende")
        print()
        
        try:
            start_tutorial = input(f"{Colors.BOLD}{Colors.BLUE}Deseja começar com o tutorial? (s/N): {Colors.RESET}").strip().lower()
            if start_tutorial in ['s', 'sim', 'y', 'yes']:
                self.menu.start_interactive_tutorial()
        except (KeyboardInterrupt, EOFError):
            pass
    
    def _cleanup_application(self):
        """Limpeza final da aplicação"""
        try:
            # Limpar cache de ML se disponível
            if hasattr(self, 'recommendation_handler') and self.recommendation_handler:
                if hasattr(self.recommendation_handler, 'matcher') and self.recommendation_handler.matcher:
                    # Limpar caches grandes que podem estar causando problemas
                    if hasattr(self.recommendation_handler.matcher, 'cv_cache'):
                        self.recommendation_handler.matcher.cv_cache.clear()
                    if hasattr(self.recommendation_handler.matcher, 'job_cache'):
                        self.recommendation_handler.matcher.job_cache.clear()
            
            # Forçar garbage collection
            import gc
            gc.collect()
            
        except Exception as e:
            print(f"Aviso: Erro durante cleanup: {e}")
    
    def _show_goodbye_screen(self):
        """Tela de despedida"""
        try:
            self.menu.clear_screen()
            print(f"{Colors.BOLD}{Colors.CYAN}👋 OBRIGADO POR USAR O CATHO JOB SCRAPER!{Colors.RESET}")
            print()
            print("Sistema finalizado com sucesso.")
            print(f"Suas configurações foram salvas e estarão disponíveis na próxima execução.")
            print()
            print(f"{Colors.YELLOW}💡 Dica:{Colors.RESET} Use {Colors.BOLD}python main.py{Colors.RESET} para executar o sistema")
            print()
        except Exception:
            # Se algo der errado na despedida, apenas saia silenciosamente
            pass
    
    async def _handle_menu_choice(self, choice: str):
        """Manipula escolhas do menu principal"""
        try:
            choice_num = int(choice)
        except ValueError:
            print(f"{Colors.RED}⚠️ Opção '{choice}' não reconhecida{Colors.RESET}")
            input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Buscar opção correspondente
        option = self.menu.get_option_by_key(str(choice_num))
        
        if not option:
            print(f"{Colors.RED}⚠️ Opção {choice_num} não encontrada{Colors.RESET}")
            input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Mostrar tutorial se disponível e usuário é iniciante
        if (option.tutorial_available and 
            self.menu.user_preferences.get("show_tutorials", True) and
            self.current_user_level == "beginner"):
            
            show_tutorial = input(f"{Colors.YELLOW}💡 Tutorial disponível para '{option.title}'. Mostrar? (s/N): {Colors.RESET}").strip().lower()
            if show_tutorial in ['s', 'sim', 'y', 'yes']:
                self.menu.print_option_tutorial(option)
        
        # Executar funcionalidade baseada na escolha
        await self._execute_option(option)
    
    async def _execute_option(self, option):
        """Executa a funcionalidade selecionada"""
        try:
            if option.key == "1":  # Scraping Básico
                await self._execute_basic_scraping()
            elif option.key == "2":  # Scraping Rápido
                await self._execute_fast_scraping()
            elif option.key == "3":  # Scraping Avançado
                await self._execute_advanced_scraping()
            elif option.key == "4":  # Scraping Incremental
                await self._execute_incremental_scraping()
            elif option.key == "5":  # Análise de CV
                await self._execute_cv_analysis()
            elif option.key == "6":  # Recomendações IA
                await self._execute_ai_recommendations()
            elif option.key == "7":  # Business Intelligence
                await self._execute_business_intelligence()
            elif option.key == "8":  # Análise de Skills
                await self._execute_skills_analysis()
            elif option.key == "9":  # Buscar Cache
                await self._execute_cache_search()
            elif option.key == "10":  # Estatísticas
                await self._execute_statistics()
            elif option.key == "11":  # Limpar Dados
                await self._execute_clean_data()
            elif option.key == "12":  # Deduplicação
                await self._execute_deduplication()
            elif option.key == "13":  # API Server
                await self._execute_api_server()
            elif option.key == "14":  # Webhooks
                await self._execute_webhooks()
            elif option.key == "15":  # Exportar Dados
                await self._execute_export_data()
            elif option.key == "16":  # Dashboard Web
                await self._execute_web_dashboard()
            elif option.key == "17":  # Configurações
                await self._execute_settings()
            elif option.key == "18":  # Tutoriais
                await self._execute_tutorials()
            elif option.key == "19":  # Ajuda
                await self._execute_help()
            elif option.key == "20":  # Modo Tutorial
                await self._execute_tutorial_mode()
            else:
                print(f"{Colors.YELLOW}⚠️ Funcionalidade {option.title} em desenvolvimento{Colors.RESET}")
                input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao executar {option.title}: {e}{Colors.RESET}")
            input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    # === IMPLEMENTAÇÕES DAS FUNCIONALIDADES ===
    
    async def _execute_basic_scraping(self):
        """Scraping básico - modo iniciante"""
        print(f"{Colors.GREEN}🚀 Iniciando Scraping Básico...{Colors.RESET}")
        
        # Configuração simplificada compatível com o handler
        palavra_chave = input("Digite uma palavra-chave (ex: python): ").strip() or "python"
        
        config = {
            "palavra_chave": palavra_chave,
            "max_pages": 2,
            "max_concurrent": 5,
            "performance_mode": 1,  # Modo básico
            "incremental": False,
            "usar_cache": True,
            "filters": {
                "palavra_chave": palavra_chave,
                "modo_performance": "básico"
            }
        }
        
        print(f"\n{Colors.YELLOW}Configuração:{Colors.RESET}")
        print(f"   Palavra-chave: {config['palavra_chave']}")
        print(f"   Páginas: {config['max_pages']}")
        print(f"   Modo: Básico (Iniciante)")
        print()
        
        await self.scraping_handler.run_scraping_with_config(config)
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_fast_scraping(self):
        """Scraping rápido com cache"""
        print(f"{Colors.YELLOW}⚡ Iniciando Scraping Rápido...{Colors.RESET}")
        
        palavra_chave = input("Palavra-chave: ").strip() or "desenvolvedor"
        
        config = {
            "palavra_chave": palavra_chave,
            "max_pages": 5,
            "max_concurrent": 10,
            "performance_mode": 2,  # Modo otimizado
            "incremental": False,
            "usar_cache": True,
            "filters": {
                "palavra_chave": palavra_chave,
                "modo_performance": "rápido"
            }
        }
        
        print(f"\n{Colors.YELLOW}Configuração:{Colors.RESET}")
        print(f"   Palavra-chave: {config['palavra_chave']}")
        print(f"   Páginas: {config['max_pages']}")
        print(f"   Modo: Rápido (Cache Otimizado)")
        print()
        
        await self.scraping_handler.run_scraping_with_config(config)
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_advanced_scraping(self):
        """Scraping avançado com IA"""
        print(f"{Colors.CYAN}🎯 Iniciando Scraping Avançado...{Colors.RESET}")
        
        # Configuração avançada manual
        print("Configure os parâmetros avançados:")
        palavra_chave = input("Palavra-chave: ").strip() or "desenvolvedor"
        max_pages = int(input("Número de páginas (padrão 10): ").strip() or "10")
        max_concurrent = int(input("Jobs simultâneos (padrão 15): ").strip() or "15")
        
        config = {
            "palavra_chave": palavra_chave,
            "max_pages": max_pages,
            "max_concurrent": max_concurrent,
            "performance_mode": 3,  # Modo pooled/avançado
            "incremental": True,
            "usar_cache": True,
            "filters": {
                "palavra_chave": palavra_chave,
                "modo_performance": "avançado"
            }
        }
        
        print(f"\n{Colors.YELLOW}Configuração Avançada:{Colors.RESET}")
        print(f"   Palavra-chave: {config['palavra_chave']}")
        print(f"   Páginas: {config['max_pages']}")
        print(f"   Concurrent Jobs: {config['max_concurrent']}")
        print(f"   Modo: Avançado (IA + Cache)")
        print()
        
        await self.scraping_handler.run_scraping_with_config(config)
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_incremental_scraping(self):
        """Scraping incremental - nova funcionalidade"""
        print(f"{Colors.BLUE}🔄 Scraping Incremental em desenvolvimento...{Colors.RESET}")
        print("Esta funcionalidade permitirá atualizações inteligentes apenas de dados novos.")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_cv_analysis(self):
        """Análise de CV"""
        await self.cv_handler.handle_cv_analysis()
    
    async def _execute_ai_recommendations(self):
        """Recomendações com IA"""
        if self.recommendation_handler:
            await self.recommendation_handler.handle_recommendation_system()
        else:
            print(f"{Colors.RED}❌ Sistema de recomendações não disponível{Colors.RESET}")
            print("Instale as dependências ML para usar esta funcionalidade.")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_business_intelligence(self):
        """Business Intelligence"""
        print(f"{Colors.CYAN}📊 Business Intelligence{Colors.RESET}")
        print()
        print("Escolha o tipo de análise:")
        print("   1. 💰 Análise de Tendências Salariais")
        print("   2. 🗺️ Mapa de Calor Regional")
        print("   3. 🛠️ Skills em Demanda")
        print("   4. 📈 Relatório Executivo")
        print("   0. Voltar")
        print()
        
        choice = input(f"{Colors.BLUE}Sua escolha: {Colors.RESET}").strip()
        
        if choice == "1":
            await self._show_salary_trends()
        elif choice == "2":
            await self._show_regional_heatmap()
        elif choice == "3":
            await self._show_skills_demand()
        elif choice == "4":
            await self._show_executive_report()
    
    async def _show_salary_trends(self):
        """Mostra análise de tendências salariais"""
        try:
            from src.business_intelligence.salary_trend_analyzer import salary_trend_analyzer
            print(f"\n{Colors.GREEN}💰 Gerando análise de tendências salariais...{Colors.RESET}")
            salary_trend_analyzer.print_salary_trends_report()
        except ImportError:
            print(f"{Colors.RED}❌ Módulo de análise salarial não disponível{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_regional_heatmap(self):
        """Mostra mapa de calor regional"""
        try:
            from src.business_intelligence.regional_heatmap import regional_heatmap
            print(f"\n{Colors.GREEN}🗺️ Gerando mapa de calor regional...{Colors.RESET}")
            regional_heatmap.print_regional_heatmap_report()
        except ImportError:
            print(f"{Colors.RED}❌ Módulo de mapa regional não disponível{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_skills_demand(self):
        """Mostra análise de demanda de skills"""
        try:
            from src.business_intelligence.skills_demand_analyzer import skills_demand_analyzer
            print(f"\n{Colors.GREEN}🛠️ Gerando análise de skills...{Colors.RESET}")
            skills_demand_analyzer.print_skills_analysis_report()
        except ImportError:
            print(f"{Colors.RED}❌ Módulo de análise de skills não disponível{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_executive_report(self):
        """Mostra relatório executivo"""
        try:
            from src.business_intelligence.market_intelligence_reports import market_intelligence
            
            # Carregar dados recentes
            import json
            from pathlib import Path
            
            results_dir = Path("data/resultados/json")
            if results_dir.exists():
                json_files = list(results_dir.glob("*.json"))
                if json_files:
                    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        jobs = data.get('vagas', [])
                    
                    print(f"\n{Colors.GREEN}📊 Gerando relatório executivo...{Colors.RESET}")
                    dashboard = market_intelligence.generate_executive_dashboard(jobs)
                    market_intelligence.print_executive_dashboard_report(dashboard)
                else:
                    print(f"{Colors.YELLOW}⚠️ Nenhum dado encontrado. Execute um scraping primeiro.{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠️ Diretório de resultados não encontrado.{Colors.RESET}")
                
        except ImportError:
            print(f"{Colors.RED}❌ Módulo de inteligência de mercado não disponível{Colors.RESET}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_skills_analysis(self):
        """Análise específica de skills"""
        await self._show_skills_demand()
    
    async def _execute_cache_search(self):
        """Busca no cache"""
        while True:
            cache_choice = self.menu.print_cache_menu() if hasattr(self.menu, 'print_cache_menu') else "0"
            if cache_choice == "0":
                break
            else:
                await self.cache_handler.handle_cache_operations(cache_choice)
    
    async def _execute_statistics(self):
        """Estatísticas do sistema"""
        await self.statistics_handler.handle_statistics_dashboard()
    
    async def _execute_clean_data(self):
        """Limpeza de dados"""
        await self.data_handler.handle_clean_data()
    
    async def _execute_deduplication(self):
        """Deduplicação"""
        await self.data_handler.handle_deduplication()
    
    async def _execute_api_server(self):
        """Servidor API"""
        await self.api_handler.start_api_server()
    
    async def _execute_webhooks(self):
        """Webhooks - nova funcionalidade"""
        print(f"{Colors.BLUE}📡 Sistema de Webhooks em desenvolvimento...{Colors.RESET}")
        print("Esta funcionalidade permitirá notificações automáticas de novas vagas.")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_export_data(self):
        """Exportação de dados"""
        print(f"{Colors.CYAN}🔗 Exportação de Dados{Colors.RESET}")
        print("Esta funcionalidade permitirá exportar dados em vários formatos.")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_web_dashboard(self):
        """Dashboard web - nova funcionalidade"""
        print(f"{Colors.PURPLE}📊 Dashboard Web em desenvolvimento...{Colors.RESET}")
        print("Interface web moderna para visualização de dados e análises.")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _execute_settings(self):
        """Configurações do sistema"""
        await self.settings_handler.handle_settings_menu()
    
    async def _execute_tutorials(self):
        """Sistema de tutoriais"""
        self.menu.start_interactive_tutorial()
    
    async def _execute_help(self):
        """Sistema de ajuda"""
        self.menu.print_help_system()
    
    async def _execute_tutorial_mode(self):
        """Modo tutorial"""
        print(f"{Colors.GREEN}🎓 Ativando modo tutorial...{Colors.RESET}")
        self.menu.user_preferences["show_tutorials"] = True
        self.menu.user_preferences["complexity_level"] = "beginner"
        self.menu._save_user_preferences()
        print("Modo tutorial ativado! Guias serão mostrados para cada funcionalidade.")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")


async def main():
    """Função principal com tratamento robusto de erros"""
    app = None
    try:
        print(f"{Colors.CYAN}🚀 Inicializando Catho Job Scraper...{Colors.RESET}")
        app = EnhancedJobScraperApp()
        await app.run()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Interrupção pelo usuário (Ctrl+C){Colors.RESET}")
        if app:
            app._cleanup_application()
            
    except Exception as e:
        print(f"\n{Colors.RED}❌ Erro fatal: {e}{Colors.RESET}")
        if app:
            app._cleanup_application()
    
    finally:
        # Cleanup final garantido
        try:
            if app:
                app._cleanup_application()
            print(f"{Colors.GREEN}✅ Shutdown completo{Colors.RESET}")
        except:
            pass  # Falha silenciosa no cleanup


def run_with_error_handling():
    """Wrapper para executar main() com tratamento de erros do Windows"""
    try:
        # Tentar executar normalmente
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Programa interrompido{Colors.RESET}")
        
    except SystemExit:
        # Exit normal, sem erro
        pass
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ Erro crítico: {e}{Colors.RESET}")
        
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