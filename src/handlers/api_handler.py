"""
Handler para operações da API
"""

from typing import Dict, Optional

from ..utils.menu_system import MenuSystem, Colors


class APIHandler:
    """Gerencia operações da API"""
    
    def __init__(self):
        self.menu = MenuSystem()
    
    async def start_api_server(self) -> None:
        """Inicia servidor da API"""
        self.menu.print_info_message("Iniciando servidor da API REST...")
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
            self.menu.print_error_message("Dependências da API não encontradas")
            self.menu.print_info_message("Execute: pip install uvicorn fastapi")
        except Exception as e:
            self.menu.print_error_message(f"Erro ao iniciar API: {e}")
        
        print(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
        input()