"""
Handler para operações de análise de CV
"""

from typing import Dict, Optional

from ..utils.menu_system import MenuSystem, Colors


class CVHandler:
    """Gerencia operações de análise de CV"""
    
    def __init__(self):
        self.menu = MenuSystem()
    
    async def handle_cv_analysis(self) -> None:
        """Gerencia o menu de análise de CV"""
        try:
            from ..utils.cv_interface import run_cv_interface
            run_cv_interface()
        except Exception as e:
            self.menu.print_error_message(f"Erro no sistema de análise de CV: {e}")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")