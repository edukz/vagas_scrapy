"""
Handler para operações de análise de CV
"""

from typing import Dict, Optional

from ..utils.menu_system import MenuSystem, Colors
from .manual_cv_handler import ManualCVHandler


class CVHandler:
    """Gerencia operações de análise de CV"""
    
    def __init__(self):
        self.menu = MenuSystem()
        self._cv_interface_loaded = False
        self.manual_cv_handler = ManualCVHandler()
    
    async def handle_cv_analysis(self) -> None:
        """Gerencia o menu de análise de CV com opções expandidas"""
        try:
            # Mostrar menu de opções
            print(f"\n{Colors.BOLD}{Colors.CYAN}📄 ANÁLISE DE CURRÍCULO{Colors.RESET}")
            print("=" * 50)
            print()
            print("Escolha como deseja fornecer seu currículo:")
            print()
            print(f"  {Colors.GREEN}1.{Colors.RESET} 📎 Anexar arquivo (PDF, DOCX, TXT)")
            print(f"  {Colors.GREEN}2.{Colors.RESET} ✍️  Preencher formulário manual")
            print(f"  {Colors.GREEN}3.{Colors.RESET} 📂 Carregar CV salvo anteriormente")
            print(f"  {Colors.GREEN}0.{Colors.RESET} ↩️  Voltar")
            print()
            
            choice = input(f"{Colors.BLUE}Sua escolha: {Colors.RESET}").strip()
            
            if choice == "1":
                # Import lazy - só carrega quando necessário
                if not self._cv_interface_loaded:
                    self.menu.print_info_message("Carregando sistema de análise de CV...")
                    self._cv_interface_loaded = True
                
                from ..utils.cv_interface import run_cv_interface
                run_cv_interface()
                
            elif choice == "2":
                # Usar formulário manual
                await self.manual_cv_handler.handle_manual_cv_input()
                
            elif choice == "3":
                # Carregar CV salvo
                if await self.manual_cv_handler.load_saved_cv():
                    if input("\nDeseja analisar este CV? (s/n): ").lower() == 's':
                        await self.manual_cv_handler.analyze_manual_cv()
                else:
                    print("Você pode criar um novo CV usando a opção 2.")
                    
            elif choice == "0":
                return
            else:
                print(f"{Colors.RED}Opção inválida!{Colors.RESET}")
                
        except KeyboardInterrupt:
            # Usuário pressionou Ctrl+C - sair silenciosamente
            self.menu.print_info_message("Saindo da análise de CV...")
        except EOFError:
            # Input foi interrompido - sair silenciosamente
            self.menu.print_info_message("Operação cancelada")
        except Exception as e:
            self.menu.print_error_message(f"Erro no sistema de análise de CV: {e}")
            try:
                input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            except (KeyboardInterrupt, EOFError):
                pass  # Ignora se o usuário pressionar Ctrl+C novamente