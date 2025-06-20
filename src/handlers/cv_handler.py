"""
Handler para operações de análise de CV
"""

from typing import Dict, Optional

from ..utils.menu_system import MenuSystem, Colors


class CVHandler:
    """Gerencia operações de análise de CV"""
    
    def __init__(self):
        self.menu = MenuSystem()
        self._cv_interface_loaded = False
    
    async def handle_cv_analysis(self) -> None:
        """Gerencia o menu de análise de CV"""
        try:
            # Import lazy - só carrega quando necessário
            if not self._cv_interface_loaded:
                self.menu.print_info_message("Carregando sistema de análise de CV...")
                self._cv_interface_loaded = True
            
            from ..utils.cv_interface import run_cv_interface
            run_cv_interface()
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