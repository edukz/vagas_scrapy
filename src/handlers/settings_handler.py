"""
Handler para operações de configurações
"""

from typing import Dict, Optional

from ..utils.menu_system import MenuSystem, Colors
from ..utils.settings_ui import settings_ui


class SettingsHandler:
    """Gerencia operações de configurações"""
    
    def __init__(self):
        self.menu = MenuSystem()
    
    async def handle_settings_menu(self) -> None:
        """Gerencia o menu de configurações avançadas"""
        try:
            settings_ui.show_main_settings_menu()
        except Exception as e:
            self.menu.print_error_message(f"Erro no sistema de configurações: {e}")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")