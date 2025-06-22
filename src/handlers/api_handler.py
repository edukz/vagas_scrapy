"""
Handler para operações da API
"""

import os
import sys
import subprocess
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
        
        # Verificar dependências primeiro
        if not self._check_dependencies():
            return
        
        # Verificar se arquivo da API existe
        api_file = os.path.join(os.getcwd(), "api", "main.py")
        if not os.path.exists(api_file):
            print(f"{Colors.RED}❌ Arquivo da API não encontrado: {api_file}{Colors.RESET}")
            print(f"{Colors.YELLOW}💡 Criando API básica...{Colors.RESET}")
            await self._create_basic_api()
            return
        
        try:
            # Tentar importar e iniciar API
            await self._start_api_safely()
            
        except ImportError as ie:
            print(f"{Colors.RED}❌ Erro de importação: {ie}{Colors.RESET}")
            await self._start_api_fallback()
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao iniciar API: {e}{Colors.RESET}")
            await self._start_api_fallback()
    
    def _check_dependencies(self) -> bool:
        """Verifica se as dependências estão instaladas"""
        try:
            import uvicorn
            import fastapi
            print(f"{Colors.GREEN}✅ Dependências encontradas{Colors.RESET}")
            print(f"   - FastAPI: {fastapi.__version__}")
            print(f"   - Uvicorn: {uvicorn.__version__}")
            return True
        except ImportError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else "desconhecida"
            print(f"{Colors.RED}❌ Dependência ausente: {missing}{Colors.RESET}")
            print(f"{Colors.YELLOW}📋 SOLUÇÃO:{Colors.RESET}")
            print("   Execute: pip install fastapi uvicorn")
            print("   Ou: pip install -r requirements.txt")
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return False
    
    async def _start_api_safely(self) -> None:
        """Tenta iniciar API de forma segura"""
        try:
            # Importação dinâmica para evitar problemas
            import uvicorn
            
            print(f"{Colors.GREEN}🚀 Iniciando API em http://localhost:8000{Colors.RESET}")
            print(f"{Colors.BLUE}📚 Documentação: http://localhost:8000/docs{Colors.RESET}")
            print(f"{Colors.CYAN}📖 ReDoc: http://localhost:8000/redoc{Colors.RESET}")
            print()
            print(f"{Colors.YELLOW}🔧 ENDPOINTS PRINCIPAIS:{Colors.RESET}")
            print("   GET  / - Informações da API")
            print("   GET  /api/v1/health - Health check")
            print("   POST /api/v1/scraping/start - Iniciar scraping")
            print("   GET  /api/v1/data/search - Buscar vagas")
            print()
            print(f"{Colors.DIM}Pressione Ctrl+C para parar o servidor{Colors.RESET}")
            print(f"{Colors.GRAY}{'─' * 60}{Colors.RESET}")
            
            # Tentar carregar API principal
            try:
                # Verificar se dependências da API principal estão disponíveis
                try:
                    import pydantic_settings
                    pydantic_available = True
                except ImportError:
                    pydantic_available = False
                
                if not pydantic_available:
                    print(f"{Colors.YELLOW}⚠️ pydantic-settings não disponível, usando API simplificada{Colors.RESET}")
                    print(f"{Colors.BLUE}🔄 Iniciando API simplificada...{Colors.RESET}")
                    await self._start_simple_api()
                    return
                
                # Importar módulo da API
                sys.path.insert(0, os.getcwd())
                from api.main import app
                
                # Iniciar servidor
                uvicorn.run(
                    app,
                    host="0.0.0.0",
                    port=8000,
                    reload=False,  # Desabilitar reload para evitar problemas
                    log_level="info"
                )
            except Exception as import_error:
                print(f"{Colors.YELLOW}⚠️ Erro ao carregar API principal: {import_error}{Colors.RESET}")
                print(f"{Colors.BLUE}🔄 Iniciando API simplificada...{Colors.RESET}")
                await self._start_simple_api()
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 Servidor API parado pelo usuário{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Erro inesperado: {e}{Colors.RESET}")
        finally:
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _start_simple_api(self) -> None:
        """Inicia API simplificada sem dependências complexas"""
        try:
            import uvicorn
            from fastapi import FastAPI
            from fastapi.responses import JSONResponse
            import threading
            import asyncio
            from datetime import datetime
            
            # Criar API simples
            app = FastAPI(
                title="Catho Job Scraper API (Simplified)",
                description="API simplificada para o sistema de scraping",
                version="1.0.0-lite"
            )
            
            @app.get("/")
            async def root():
                return {
                    "name": "Catho Job Scraper API",
                    "version": "1.0.0-lite",
                    "status": "running",
                    "mode": "simplified",
                    "timestamp": datetime.now().isoformat(),
                    "endpoints": {
                        "health": "/health",
                        "status": "/api/v1/status",
                        "docs": "/docs"
                    }
                }
            
            @app.get("/health")
            async def health():
                return {
                    "status": "healthy",
                    "mode": "simplified",
                    "timestamp": datetime.now().isoformat()
                }
            
            @app.get("/api/v1/status")
            async def status():
                return {
                    "scraper": "available",
                    "cache": "available",
                    "api": "running",
                    "mode": "simplified"
                }
            
            @app.get("/api/v1/health")
            async def health_detailed():
                return {
                    "status": "healthy",
                    "components": {
                        "api": "running",
                        "scraper": "available", 
                        "cache": "available"
                    },
                    "version": "1.0.0-lite",
                    "mode": "simplified"
                }
            
            print(f"{Colors.GREEN}✅ API simplificada criada com sucesso!{Colors.RESET}")
            print(f"{Colors.CYAN}📋 ENDPOINTS DISPONÍVEIS:{Colors.RESET}")
            print("   GET / - Informações da API")
            print("   GET /health - Health check básico")
            print("   GET /api/v1/status - Status do sistema")
            print("   GET /api/v1/health - Health check detalhado")
            print("   GET /docs - Documentação Swagger")
            
            # Usar thread para executar o servidor e evitar conflito de event loop
            def run_server():
                try:
                    uvicorn.run(
                        app,
                        host="127.0.0.1",
                        port=8000,
                        log_level="info",
                        access_log=False  # Reduzir logs
                    )
                except Exception as e:
                    print(f"{Colors.RED}❌ Erro no servidor: {e}{Colors.RESET}")
            
            print(f"\n{Colors.GREEN}🚀 Iniciando servidor simplificado em thread separada...{Colors.RESET}")
            print(f"{Colors.BLUE}🌐 Acesse: http://127.0.0.1:8000{Colors.RESET}")
            print(f"{Colors.CYAN}📚 Docs: http://127.0.0.1:8000/docs{Colors.RESET}")
            
            # Executar em thread separada para evitar conflito de event loop
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Aguardar input do usuário
            print(f"\n{Colors.YELLOW}⚡ API SIMPLIFICADA RODANDO!{Colors.RESET}")
            print(f"{Colors.DIM}Pressione Enter para parar...{Colors.RESET}")
            input()
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erro na API simplificada: {e}{Colors.RESET}")
    
    async def _start_api_fallback(self) -> None:
        """Fallback usando subprocess para evitar problemas de importação"""
        print(f"\n{Colors.BLUE}🔄 TENTANDO MÉTODO ALTERNATIVO{Colors.RESET}")
        
        try:
            # Verificar se uvicorn está disponível via command line
            result = subprocess.run(["uvicorn", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ Uvicorn disponível via CLI{Colors.RESET}")
                print(f"{Colors.YELLOW}🚀 Iniciando API via subprocess...{Colors.RESET}")
                
                # Executar via subprocess
                api_cmd = [
                    "uvicorn", 
                    "api.main:app",
                    "--host", "0.0.0.0",
                    "--port", "8000",
                    "--reload"
                ]
                
                print(f"{Colors.GRAY}Comando: {' '.join(api_cmd)}{Colors.RESET}")
                print(f"{Colors.GREEN}🌐 API iniciada em http://localhost:8000{Colors.RESET}")
                print(f"{Colors.DIM}Pressione Ctrl+C para parar...{Colors.RESET}")
                
                # Executar comando
                subprocess.run(api_cmd, cwd=os.getcwd())
                
            else:
                await self._create_basic_api()
                
        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}❌ Timeout ao verificar uvicorn{Colors.RESET}")
            await self._create_basic_api()
        except FileNotFoundError:
            print(f"{Colors.YELLOW}⚠️ Uvicorn não encontrado no PATH{Colors.RESET}")
            await self._create_basic_api()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 Servidor parado pelo usuário{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Erro no fallback: {e}{Colors.RESET}")
            await self._create_basic_api()
    
    async def _create_basic_api(self) -> None:
        """Cria uma API básica funcional"""
        print(f"\n{Colors.YELLOW}🔧 CRIANDO API BÁSICA FUNCIONAL{Colors.RESET}")
        
        try:
            import uvicorn
            from fastapi import FastAPI, HTTPException
            from fastapi.responses import JSONResponse
            import time
            from datetime import datetime
            
            # Criar aplicação básica
            app = FastAPI(
                title="Catho Job Scraper API (Basic)",
                description="API básica para demonstração do sistema",
                version="1.0.0-basic"
            )
            
            @app.get("/")
            async def root():
                return {
                    "name": "Catho Job Scraper API",
                    "version": "1.0.0-basic",
                    "status": "running",
                    "mode": "basic",
                    "timestamp": datetime.now().isoformat(),
                    "endpoints": {
                        "health": "/health",
                        "status": "/status",
                        "docs": "/docs",
                        "system": "/system"
                    }
                }
            
            @app.get("/health")
            async def health_check():
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "uptime": "running",
                    "version": "1.0.0-basic"
                }
            
            @app.get("/status")
            async def system_status():
                return {
                    "scraper": "available",
                    "cache": "available",
                    "api": "running",
                    "mode": "basic demonstration",
                    "features": [
                        "Health monitoring",
                        "Basic status endpoints",
                        "System information"
                    ]
                }
            
            @app.get("/system")
            async def system_info():
                import os
                import platform
                
                return {
                    "platform": platform.system(),
                    "python_version": platform.python_version(),
                    "working_directory": os.getcwd(),
                    "environment": "development",
                    "api_mode": "basic"
                }
            
            print(f"{Colors.GREEN}✅ API básica criada com sucesso!{Colors.RESET}")
            print(f"{Colors.CYAN}📋 ENDPOINTS DISPONÍVEIS:{Colors.RESET}")
            print("   GET / - Informações da API")
            print("   GET /health - Health check")
            print("   GET /status - Status do sistema")
            print("   GET /system - Informações do sistema")
            print("   GET /docs - Documentação Swagger")
            
            print(f"\n{Colors.GREEN}🚀 Iniciando servidor básico...{Colors.RESET}")
            
            # Executar servidor
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=8000,
                log_level="info"
            )
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 API básica parada pelo usuário{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao criar API básica: {e}{Colors.RESET}")
        finally:
            input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")