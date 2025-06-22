"""
Sistema de Menu Avançado v2.0
=============================

Menu modernizado com categorização de funcionalidades,
guias interativos e acesso fácil às novas features de IA.
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass


@dataclass
class MenuOption:
    """Representa uma opção do menu"""
    key: str
    icon: str
    title: str
    description: str
    category: str
    complexity: str  # 'beginner', 'intermediate', 'advanced'
    color: str
    tutorial_available: bool = False
    new_feature: bool = False


class Colors:
    """Cores ANSI melhoradas para terminal"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    
    # Cores de texto
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    # Cores de fundo
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'
    BG_MAGENTA = '\033[105m'
    BG_CYAN = '\033[106m'
    BG_WHITE = '\033[107m'
    BG_GRAY = '\033[100m'
    
    # Gradientes simulados
    GRADIENT_CYAN = '\033[96m'
    GRADIENT_BLUE = '\033[94m'
    GRADIENT_PURPLE = '\033[95m'


class EnhancedMenuSystem:
    """
    Sistema de menu avançado v2.0
    
    Funcionalidades:
    - Categorização inteligente de funcionalidades
    - Guias interativos e tutoriais
    - Interface visual modernizada
    - Sistema de ajuda contextual
    - Navegação intuitiva
    - Indicadores de complexidade
    """
    
    def __init__(self):
        self.version = "5.0.0"
        self.user_preferences = self._load_user_preferences()
        self.current_category = "main"
        self.tutorial_mode = False
        
        # Definir todas as opções do menu
        self._initialize_menu_options()
        
        # Status do sistema
        self.system_status = self._check_system_status()
    
    def _load_user_preferences(self) -> Dict:
        """Carrega preferências do usuário"""
        prefs_file = Path("data/user_preferences.json")
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "show_tutorials": True,
            "complexity_level": "beginner",  # beginner, intermediate, advanced
            "theme": "dark",
            "language": "pt-br",
            "first_time": True
        }
    
    def _save_user_preferences(self):
        """Salva preferências do usuário"""
        try:
            prefs_file = Path("data/user_preferences.json")
            prefs_file.parent.mkdir(exist_ok=True)
            
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Aviso: Não foi possível salvar preferências: {e}")
    
    def _initialize_menu_options(self):
        """Inicializa todas as opções do menu organizadas por categoria"""
        self.menu_options = {
            # CATEGORIA: COLETA DE DADOS
            "data_collection": [
                MenuOption("1", "🎯", "BUSCA INTELIGENTE", "Interface moderna com presets automáticos", "data_collection", "beginner", Colors.GREEN, new_feature=True),
                MenuOption("2", "⚡", "SCRAPING RÁPIDO", "Coleta otimizada com cache inteligente", "data_collection", "intermediate", Colors.YELLOW),
                MenuOption("3", "🔧", "SCRAPING AVANÇADO", "Coleta com IA e filtros personalizados", "data_collection", "advanced", Colors.CYAN, tutorial_available=True),
                MenuOption("4", "🔄", "SCRAPING INCREMENTAL", "Atualização inteligente de dados", "data_collection", "advanced", Colors.BLUE),
            ],
            
            # CATEGORIA: ANÁLISE INTELIGENTE 
            "ai_analysis": [
                MenuOption("5", "🤖", "ANÁLISE DE CV", "Extrair perfil profissional com IA", "ai_analysis", "intermediate", Colors.PURPLE, tutorial_available=True),
                MenuOption("6", "💡", "RECOMENDAÇÕES IA", "Matching CV-Vagas personalizado", "ai_analysis", "advanced", Colors.MAGENTA, tutorial_available=True, new_feature=True),
                MenuOption("7", "📊", "BUSINESS INTELLIGENCE", "Análise de mercado e tendências", "ai_analysis", "advanced", Colors.CYAN, tutorial_available=True, new_feature=True),
                MenuOption("8", "🎯", "ANÁLISE DE SKILLS", "Demanda e valorização de tecnologias", "ai_analysis", "intermediate", Colors.GREEN, new_feature=True),
            ],
            
            # CATEGORIA: DADOS E CACHE
            "data_management": [
                MenuOption("9", "📋", "VISUALIZAR VAGAS", "Explorer vagas salvas no sistema", "data_management", "beginner", Colors.BLUE, new_feature=True),
                MenuOption("10", "📈", "ESTATÍSTICAS", "Dashboard e métricas do sistema", "data_management", "intermediate", Colors.YELLOW),
                MenuOption("11", "🧹", "LIMPAR DADOS", "Gerenciar armazenamento", "data_management", "beginner", Colors.RED),
                MenuOption("12", "🔄", "DEDUPLICAÇÃO", "Otimizar banco de dados", "data_management", "intermediate", Colors.MAGENTA),
            ],
            
            # CATEGORIA: INTEGRAÇÃO E API
            "integration": [
                MenuOption("13", "🌐", "API SERVER", "Servidor REST para integrações", "integration", "advanced", Colors.GREEN, tutorial_available=True),
                MenuOption("14", "📡", "WEBHOOKS", "Notificações automáticas", "integration", "advanced", Colors.BLUE, new_feature=True),
                MenuOption("15", "🔗", "EXPORTAR DADOS", "Relatórios e integrações", "integration", "intermediate", Colors.CYAN),
                MenuOption("16", "📊", "DASHBOARD WEB", "Interface web moderna", "integration", "advanced", Colors.PURPLE, new_feature=True),
            ],
            
            # CATEGORIA: CONFIGURAÇÃO E AJUDA
            "settings_help": [
                MenuOption("17", "⚙️", "CONFIGURAÇÕES", "Ajustar parâmetros do sistema", "settings_help", "intermediate", Colors.GRAY),
                MenuOption("18", "📚", "TUTORIAIS", "Guias passo-a-passo", "settings_help", "beginner", Colors.YELLOW, tutorial_available=True),
                MenuOption("19", "❓", "AJUDA", "Documentação e suporte", "settings_help", "beginner", Colors.WHITE),
                MenuOption("20", "🎓", "MODO TUTORIAL", "Aprendizado guiado", "settings_help", "beginner", Colors.GREEN, tutorial_available=True),
            ]
        }
    
    def _check_system_status(self) -> Dict:
        """Verifica status dos componentes do sistema"""
        status = {
            "scraping": "online",
            "cache": "available",
            "ai": "checking",
            "database": "checking",
            "api": "checking"
        }
        
        try:
            # Verificar cache
            cache_dir = Path("data/cache")
            if cache_dir.exists() and list(cache_dir.glob("*.json.gz")):
                status["cache"] = "available"
            else:
                status["cache"] = "empty"
            
            # Verificar IA
            try:
                from ..ml.cv_job_matcher import cv_job_matcher
                status["ai"] = "ready"
            except:
                status["ai"] = "limited"
            
            # Verificar dados
            results_dir = Path("data/resultados")
            if results_dir.exists() and list(results_dir.glob("**/*.json")):
                status["database"] = "populated"
            else:
                status["database"] = "empty"
                
        except Exception:
            pass
        
        return status
    
    def clear_screen(self):
        """Limpa a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_animated_header(self):
        """Cabeçalho principal com animação"""
        self.clear_screen()
        
        # Banner principal
        print(f"{Colors.BOLD}{Colors.GRADIENT_CYAN}╔" + "═" * 78 + "╗" + Colors.RESET)
        print(f"{Colors.BOLD}{Colors.GRADIENT_CYAN}║{Colors.RESET}" + " " * 78 + f"{Colors.BOLD}{Colors.GRADIENT_CYAN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GRADIENT_CYAN}║{Colors.RESET}         {Colors.BOLD}{Colors.WHITE}🚀 CATHO JOB SCRAPER & AI PLATFORM v{self.version}{Colors.RESET}         {Colors.BOLD}{Colors.GRADIENT_CYAN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GRADIENT_CYAN}║{Colors.RESET}           {Colors.GREEN}Sistema Completo de Web Scraping + Inteligência Artificial{Colors.RESET}           {Colors.BOLD}{Colors.GRADIENT_CYAN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GRADIENT_CYAN}║{Colors.RESET}" + " " * 78 + f"{Colors.BOLD}{Colors.GRADIENT_CYAN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GRADIENT_CYAN}╚" + "═" * 78 + "╝" + Colors.RESET)
        print()
        
        # Status do sistema
        self.print_enhanced_system_status()
        print()
        
        # Dica para novos usuários
        if self.user_preferences.get("first_time", True):
            self.print_welcome_message()
    
    def print_enhanced_system_status(self):
        """Status do sistema melhorado"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"{Colors.DIM}┌─ Status do Sistema ─────────────────────────────────────────────────────────┐{Colors.RESET}")
        
        # Linha 1: Status básico
        scraping_status = "🟢 Online" if self.system_status["scraping"] == "online" else "🔴 Offline"
        cache_status = "📦 Dados" if self.system_status["cache"] == "available" else "📭 Vazio"
        print(f"{Colors.DIM}│{Colors.RESET} {scraping_status}    {Colors.DIM}│{Colors.RESET} {cache_status}    {Colors.DIM}│{Colors.RESET} 📅 {now}    {Colors.DIM}│{Colors.RESET}")
        
        # Linha 2: Status avançado
        ai_status = "🧠 IA Ready" if self.system_status["ai"] == "ready" else "🤖 IA Limited"
        db_status = "🗄️ BD Pop." if self.system_status["database"] == "populated" else "🗄️ BD Empty"
        print(f"{Colors.DIM}│{Colors.RESET} {ai_status}    {Colors.DIM}│{Colors.RESET} {db_status}    {Colors.DIM}│{Colors.RESET} ⚡ Performance Máxima    {Colors.DIM}│{Colors.RESET}")
        
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    
    def print_welcome_message(self):
        """Mensagem de boas-vindas para novos usuários"""
        print(f"{Colors.YELLOW}🎉 BEM-VINDO AO SISTEMA!{Colors.RESET}")
        print(f"{Colors.DIM}   Novo por aqui? Digite {Colors.BOLD}tutorial{Colors.RESET}{Colors.DIM} para um tour guiado das funcionalidades!{Colors.RESET}")
        print(f"{Colors.DIM}   Para usuários experientes: {Colors.BOLD}avançado{Colors.RESET}{Colors.DIM} mostra todas as opções{Colors.RESET}")
        print()
    
    def print_main_menu(self) -> str:
        """Menu principal categorizado"""
        self.print_animated_header()
        
        # Determinar quais categorias mostrar baseado no nível do usuário
        complexity_level = self.user_preferences.get("complexity_level", "beginner")
        
        if complexity_level == "beginner":
            self._print_beginner_menu()
        elif complexity_level == "intermediate":
            self._print_intermediate_menu()
        else:
            self._print_advanced_menu()
        
        # Menu de navegação
        print(f"{Colors.DIM}┌─ Navegação ─────────────────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} 💡 {Colors.BOLD}tutorial{Colors.RESET} - Tour guiado    📚 {Colors.BOLD}ajuda{Colors.RESET} - Documentação    ⚙️ {Colors.BOLD}config{Colors.RESET} - Configurações  {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} 🔍 {Colors.BOLD}buscar{Colors.RESET} - Busca rápida    📊 {Colors.BOLD}status{Colors.RESET} - Info sistema    🚪 {Colors.BOLD}0{Colors.RESET} ou {Colors.BOLD}sair{Colors.RESET} - Sair     {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()
        
        # Input do usuário
        try:
            choice = input(f"{Colors.BOLD}{Colors.BLUE}➤ Sua escolha: {Colors.RESET}").strip().lower()
            return choice
        except (KeyboardInterrupt, EOFError):
            return "0"
    
    def _print_beginner_menu(self):
        """Menu simplificado para iniciantes"""
        print(f"{Colors.BOLD}{Colors.GREEN}🌱 MODO INICIANTE - Funcionalidades Essenciais{Colors.RESET}")
        print()
        
        essential_options = [
            ("1", "🚀", "COLETAR VAGAS", "Buscar novas vagas no Catho (FÁCIL)", Colors.GREEN),
            ("2", "🔍", "VER RESULTADOS", "Visualizar vagas já coletadas", Colors.BLUE),
            ("3", "📄", "ANALISAR CV", "Upload de currículo para análise", Colors.PURPLE),
            ("4", "📊", "ESTATÍSTICAS", "Ver resumo dos dados", Colors.YELLOW),
            ("tutorial", "🎓", "COMEÇAR TUTORIAL", "Aprender a usar o sistema", Colors.CYAN),
        ]
        
        for key, icon, title, desc, color in essential_options:
            print(f"  {Colors.BOLD}{color}[{key}]{Colors.RESET} {icon} {Colors.BOLD}{title:<18}{Colors.RESET} {Colors.DIM}{desc}{Colors.RESET}")
        
        print()
        print(f"{Colors.DIM}💡 Quer mais opções? Digite {Colors.BOLD}intermediario{Colors.RESET}{Colors.DIM} ou {Colors.BOLD}avançado{Colors.RESET}")
        print()
    
    def _print_intermediate_menu(self):
        """Menu para usuários intermediários"""
        print(f"{Colors.BOLD}{Colors.YELLOW}⚡ MODO INTERMEDIÁRIO - Funcionalidades Principais{Colors.RESET}")
        print()
        
        categories = [
            ("📥 COLETA DE DADOS", "data_collection", Colors.GREEN),
            ("🤖 ANÁLISE INTELIGENTE", "ai_analysis", Colors.PURPLE),
            ("🗄️ GERENCIAR DADOS", "data_management", Colors.BLUE),
            ("⚙️ CONFIGURAÇÕES", "settings_help", Colors.GRAY),
        ]
        
        for cat_name, cat_key, color in categories:
            print(f"{Colors.BOLD}{color}{cat_name}{Colors.RESET}")
            
            # Mostrar opções da categoria (limitado)
            options = self.menu_options.get(cat_key, [])[:3]  # Máximo 3 por categoria
            for opt in options:
                new_badge = f" {Colors.BG_RED}{Colors.WHITE} NOVO {Colors.RESET}" if opt.new_feature else ""
                tutorial_badge = f" {Colors.BG_BLUE}{Colors.WHITE} TUTORIAL {Colors.RESET}" if opt.tutorial_available else ""
                
                print(f"  {Colors.BOLD}{opt.color}[{opt.key}]{Colors.RESET} {opt.icon} {opt.title:<15} {Colors.DIM}{opt.description}{Colors.RESET}{new_badge}{tutorial_badge}")
            
            if len(self.menu_options.get(cat_key, [])) > 3:
                print(f"  {Colors.DIM}... e mais opções (digite {Colors.BOLD}avançado{Colors.RESET}{Colors.DIM} para ver todas){Colors.RESET}")
            print()
    
    def _print_advanced_menu(self):
        """Menu completo para usuários avançados"""
        print(f"{Colors.BOLD}{Colors.RED}🚀 MODO AVANÇADO - Todas as Funcionalidades{Colors.RESET}")
        print()
        
        categories = [
            ("📥 COLETA DE DADOS", "data_collection", Colors.GREEN),
            ("🤖 ANÁLISE INTELIGENTE", "ai_analysis", Colors.PURPLE),
            ("🗄️ GERENCIAR DADOS", "data_management", Colors.BLUE),
            ("🔗 INTEGRAÇÃO & API", "integration", Colors.CYAN),
            ("⚙️ CONFIGURAÇÕES & AJUDA", "settings_help", Colors.GRAY),
        ]
        
        for cat_name, cat_key, color in categories:
            print(f"{Colors.BOLD}{color}{cat_name}{Colors.RESET}")
            
            options = self.menu_options.get(cat_key, [])
            for opt in options:
                # Badges
                new_badge = f" {Colors.BG_RED}{Colors.WHITE} NOVO {Colors.RESET}" if opt.new_feature else ""
                tutorial_badge = f" {Colors.BG_BLUE}{Colors.WHITE} ? {Colors.RESET}" if opt.tutorial_available else ""
                complexity_badge = ""
                if opt.complexity == "advanced":
                    complexity_badge = f" {Colors.BG_RED}{Colors.WHITE} ADV {Colors.RESET}"
                elif opt.complexity == "intermediate":
                    complexity_badge = f" {Colors.BG_YELLOW}{Colors.BLACK} INT {Colors.RESET}"
                
                print(f"  {Colors.BOLD}{opt.color}[{opt.key}]{Colors.RESET} {opt.icon} {opt.title:<18} {Colors.DIM}{opt.description}{Colors.RESET}{new_badge}{tutorial_badge}{complexity_badge}")
            print()
    
    def handle_special_commands(self, choice: str) -> Optional[str]:
        """Manipula comandos especiais do menu"""
        if choice in ["tutorial", "tour", "help-tour"]:
            self.start_interactive_tutorial()
            return "handled"
        
        elif choice in ["ajuda", "help", "?"]:
            self.print_help_system()
            return "handled"
        
        elif choice in ["config", "configurar", "settings"]:
            self.show_quick_settings()
            return "handled"
        
        elif choice in ["status", "info", "sistema"]:
            self.show_detailed_status()
            return "handled"
        
        elif choice in ["buscar", "search", "find"]:
            self.quick_search_interface()
            return "handled"
        
        elif choice in ["iniciante", "beginner"]:
            self.user_preferences["complexity_level"] = "beginner"
            self._save_user_preferences()
            return "refresh"
        
        elif choice in ["intermediario", "intermediate"]:
            self.user_preferences["complexity_level"] = "intermediate"
            self._save_user_preferences()
            return "refresh"
        
        elif choice in ["avançado", "advanced", "expert"]:
            self.user_preferences["complexity_level"] = "advanced"
            self._save_user_preferences()
            return "refresh"
        
        elif choice in ["0", "sair", "exit", "quit"]:
            return "exit"
        
        return None
    
    def start_interactive_tutorial(self):
        """Tutorial interativo do sistema"""
        self.clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}🎓 TUTORIAL INTERATIVO DO SISTEMA{Colors.RESET}")
        print("=" * 50)
        print()
        
        tutorial_steps = [
            {
                "title": "🚀 1. Coleta de Vagas",
                "description": "Aprenda a coletar vagas do Catho com diferentes modos de performance",
                "demo_command": "Comando: Digite '1' no menu principal",
                "tips": ["Use scraping rápido para atualizações", "Scraping avançado tem filtros IA"]
            },
            {
                "title": "🤖 2. Análise de CV com IA",
                "description": "Upload e análise automática de currículos",
                "demo_command": "Comando: Digite '5' para análise de CV",
                "tips": ["Suporta PDF, DOCX e TXT", "IA extrai skills e experiência automaticamente"]
            },
            {
                "title": "💡 3. Recomendações Inteligentes",
                "description": "Sistema de matching CV-Vagas personalizado",
                "demo_command": "Comando: Digite '6' para recomendações",
                "tips": ["Sistema aprende com seu feedback", "Explicações detalhadas de compatibilidade"]
            },
            {
                "title": "📊 4. Business Intelligence",
                "description": "Análise de tendências e insights de mercado",
                "demo_command": "Comando: Digite '7' para BI",
                "tips": ["Análise salarial por região", "Skills em alta demanda", "Mapas de calor"]
            }
        ]
        
        for i, step in enumerate(tutorial_steps, 1):
            print(f"{Colors.BOLD}{Colors.GREEN}{step['title']}{Colors.RESET}")
            print(f"{step['description']}")
            print(f"{Colors.BLUE}{step['demo_command']}{Colors.RESET}")
            print(f"{Colors.YELLOW}💡 Dicas:{Colors.RESET}")
            for tip in step['tips']:
                print(f"   • {tip}")
            print()
            
            if i < len(tutorial_steps):
                try:
                    input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
                except (KeyboardInterrupt, EOFError):
                    break
        
        print(f"{Colors.BOLD}{Colors.GREEN}🎉 Tutorial concluído!{Colors.RESET}")
        print("Agora você está pronto para usar todas as funcionalidades do sistema.")
        print()
        
        # Marcar tutorial como visto
        self.user_preferences["first_time"] = False
        self._save_user_preferences()
        
        try:
            input(f"{Colors.DIM}Pressione Enter para voltar ao menu...{Colors.RESET}")
        except (KeyboardInterrupt, EOFError):
            pass
    
    def print_help_system(self):
        """Sistema de ajuda contextual"""
        self.clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}📚 SISTEMA DE AJUDA{Colors.RESET}")
        print("=" * 40)
        print()
        
        help_topics = [
            ("🚀 Como Começar", "Para novos usuários: use o tutorial interativo"),
            ("📥 Coleta de Dados", "3 modos: Básico (simples), Rápido (cache), Avançado (IA)"),
            ("🤖 Análise de CV", "Upload PDF/DOCX, extração automática de skills e experiência"),
            ("💡 Recomendações", "Matching inteligente entre CV e vagas com explicações"),
            ("📊 Business Intelligence", "Análise de mercado, tendências salariais, skills em demanda"),
            ("🔍 Busca de Dados", "Pesquisa inteligente em cache de vagas coletadas"),
            ("⚙️ Configurações", "Personalizar performance, filtros e preferências"),
            ("🌐 API Server", "Servidor REST para integrações externas"),
        ]
        
        for topic, description in help_topics:
            print(f"{Colors.BOLD}{Colors.GREEN}{topic}{Colors.RESET}")
            print(f"   {Colors.DIM}{description}{Colors.RESET}")
            print()
        
        print(f"{Colors.YELLOW}💡 Comandos Especiais:{Colors.RESET}")
        print(f"   • {Colors.BOLD}tutorial{Colors.RESET} - Tour guiado interativo")
        print(f"   • {Colors.BOLD}iniciante{Colors.RESET} - Menu simplificado")
        print(f"   • {Colors.BOLD}avançado{Colors.RESET} - Todas as funcionalidades")
        print(f"   • {Colors.BOLD}buscar{Colors.RESET} - Busca rápida")
        print(f"   • {Colors.BOLD}status{Colors.RESET} - Informações do sistema")
        print()
        
        try:
            input(f"{Colors.DIM}Pressione Enter para voltar...{Colors.RESET}")
        except (KeyboardInterrupt, EOFError):
            pass
    
    def show_quick_settings(self):
        """Configurações rápidas"""
        self.clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}⚙️ CONFIGURAÇÕES RÁPIDAS{Colors.RESET}")
        print("=" * 35)
        print()
        
        current_level = self.user_preferences.get("complexity_level", "beginner")
        
        print(f"{Colors.YELLOW}Configurações Atuais:{Colors.RESET}")
        print(f"   • Nível de usuário: {Colors.BOLD}{current_level.title()}{Colors.RESET}")
        print(f"   • Mostrar tutoriais: {Colors.BOLD}{self.user_preferences.get('show_tutorials', True)}{Colors.RESET}")
        print(f"   • Tema: {Colors.BOLD}{self.user_preferences.get('theme', 'dark')}{Colors.RESET}")
        print()
        
        print(f"{Colors.GREEN}Opções Disponíveis:{Colors.RESET}")
        print(f"   1. Mudar para modo {Colors.BOLD}Iniciante{Colors.RESET} (funcionalidades básicas)")
        print(f"   2. Mudar para modo {Colors.BOLD}Intermediário{Colors.RESET} (funcionalidades principais)")
        print(f"   3. Mudar para modo {Colors.BOLD}Avançado{Colors.RESET} (todas as funcionalidades)")
        print(f"   4. {Colors.BOLD}Resetar{Colors.RESET} tutorial (voltar ao estado inicial)")
        print(f"   0. Voltar")
        print()
        
        try:
            choice = input(f"{Colors.BLUE}Sua escolha: {Colors.RESET}").strip()
            
            if choice == "1":
                self.user_preferences["complexity_level"] = "beginner"
                print(f"{Colors.GREEN}✅ Modo iniciante ativado{Colors.RESET}")
            elif choice == "2":
                self.user_preferences["complexity_level"] = "intermediate"
                print(f"{Colors.GREEN}✅ Modo intermediário ativado{Colors.RESET}")
            elif choice == "3":
                self.user_preferences["complexity_level"] = "advanced"
                print(f"{Colors.GREEN}✅ Modo avançado ativado{Colors.RESET}")
            elif choice == "4":
                self.user_preferences["first_time"] = True
                print(f"{Colors.GREEN}✅ Tutorial resetado{Colors.RESET}")
            
            self._save_user_preferences()
            
            if choice != "0":
                input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
                
        except (KeyboardInterrupt, EOFError):
            pass
    
    def show_detailed_status(self):
        """Informações detalhadas do sistema"""
        self.clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}🔍 STATUS DETALHADO DO SISTEMA{Colors.RESET}")
        print("=" * 45)
        print()
        
        # Status dos componentes
        print(f"{Colors.YELLOW}📊 Componentes do Sistema:{Colors.RESET}")
        components = [
            ("Web Scraping", self.system_status["scraping"], "🌐"),
            ("Cache de Dados", self.system_status["cache"], "📦"),
            ("Inteligência Artificial", self.system_status["ai"], "🤖"),
            ("Banco de Dados", self.system_status["database"], "🗄️"),
        ]
        
        for name, status, icon in components:
            status_color = Colors.GREEN if status in ["online", "ready", "available", "populated"] else Colors.YELLOW
            print(f"   {icon} {name:<20} {status_color}{status.title()}{Colors.RESET}")
        
        print()
        
        # Estatísticas de uso
        try:
            cache_dir = Path("data/cache")
            cache_files = list(cache_dir.glob("*.json.gz")) if cache_dir.exists() else []
            
            results_dir = Path("data/resultados")
            result_files = list(results_dir.glob("**/*.json")) if results_dir.exists() else []
            
            cv_dir = Path("data/cv_analysis")
            cv_files = list(cv_dir.glob("*.json")) if cv_dir.exists() else []
            
            print(f"{Colors.YELLOW}📈 Estatísticas de Dados:{Colors.RESET}")
            print(f"   📦 Arquivos de cache: {len(cache_files)}")
            print(f"   📊 Resultados salvos: {len(result_files)}")
            print(f"   📄 CVs analisados: {len(cv_files)}")
            print()
            
            # Espaço em disco
            if cache_dir.exists():
                total_size = sum(f.stat().st_size for f in cache_files) / 1024 / 1024  # MB
                print(f"   💾 Espaço usado: {total_size:.1f} MB")
            
        except Exception as e:
            print(f"   ⚠️ Erro ao calcular estatísticas: {e}")
        
        print()
        try:
            input(f"{Colors.DIM}Pressione Enter para voltar...{Colors.RESET}")
        except (KeyboardInterrupt, EOFError):
            pass
    
    def quick_search_interface(self):
        """Interface de busca rápida"""
        self.clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}🔍 BUSCA RÁPIDA{Colors.RESET}")
        print("=" * 25)
        print()
        
        print("O que você gostaria de encontrar?")
        print(f"   • {Colors.BOLD}vagas{Colors.RESET} - Buscar em vagas coletadas")
        print(f"   • {Colors.BOLD}cvs{Colors.RESET} - Buscar CVs analisados")
        print(f"   • {Colors.BOLD}skills{Colors.RESET} - Buscar por tecnologia específica")
        print(f"   • {Colors.BOLD}empresas{Colors.RESET} - Buscar por empresa")
        print()
        
        try:
            search_type = input(f"{Colors.BLUE}Tipo de busca: {Colors.RESET}").strip().lower()
            
            if search_type in ["vagas", "jobs"]:
                print("🔍 Busca em vagas - implementar integração com cache_handler")
            elif search_type in ["cvs", "curriculos"]:
                print("🔍 Busca em CVs - implementar busca em análises")
            elif search_type in ["skills", "tecnologias"]:
                print("🔍 Busca por skills - implementar busca inteligente")
            elif search_type in ["empresas", "companies"]:
                print("🔍 Busca por empresas - implementar filtro de empresas")
            else:
                print(f"{Colors.YELLOW}⚠️ Tipo de busca não reconhecido{Colors.RESET}")
            
            input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            
        except (KeyboardInterrupt, EOFError):
            pass
    
    def get_option_by_key(self, key: str) -> Optional[MenuOption]:
        """Busca opção por chave"""
        for category in self.menu_options.values():
            for option in category:
                if option.key == key:
                    return option
        return None
    
    def print_option_tutorial(self, option: MenuOption):
        """Mostra tutorial específico de uma opção"""
        if not option.tutorial_available:
            return
        
        self.clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}🎓 TUTORIAL: {option.title}{Colors.RESET}")
        print("=" * 40)
        print()
        
        # Tutorial específico baseado na opção
        if option.key == "3":  # Scraping Avançado
            self._show_advanced_scraping_tutorial()
        elif option.key == "5":  # Análise de CV
            self._show_cv_analysis_tutorial()
        elif option.key == "6":  # Recomendações IA
            self._show_ai_recommendations_tutorial()
        elif option.key == "7":  # Business Intelligence
            self._show_bi_tutorial()
        
        try:
            input(f"{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
        except (KeyboardInterrupt, EOFError):
            pass
    
    def _show_advanced_scraping_tutorial(self):
        """Tutorial do scraping avançado"""
        print(f"{Colors.GREEN}🚀 Scraping Avançado com IA{Colors.RESET}")
        print()
        print("Este modo oferece:")
        print("   • Filtros inteligentes baseados em ML")
        print("   • Detecção automática de tecnologias")
        print("   • Análise de senioridade das vagas")
        print("   • Predição de salários")
        print()
        print(f"{Colors.YELLOW}📝 Como usar:{Colors.RESET}")
        print("   1. Escolha palavras-chave relevantes")
        print("   2. Configure filtros (localização, salário)")
        print("   3. O sistema coleta e enriquece automaticamente")
        print("   4. Resultados são salvos com metadados de IA")
    
    def _show_cv_analysis_tutorial(self):
        """Tutorial da análise de CV"""
        print(f"{Colors.PURPLE}📄 Análise de CV com IA{Colors.RESET}")
        print()
        print("Funcionalidades:")
        print("   • Extração automática de informações pessoais")
        print("   • Identificação de skills técnicas e soft skills")
        print("   • Análise de experiência e senioridade")
        print("   • Estimativa de faixa salarial")
        print("   • Suporte a PDF, DOCX e TXT")
        print()
        print(f"{Colors.YELLOW}📝 Passo a passo:{Colors.RESET}")
        print("   1. Coloque seu CV na pasta data/cv_input/")
        print("   2. Execute a análise")
        print("   3. Revise os resultados extraídos")
        print("   4. Use para gerar recomendações personalizadas")
    
    def _show_ai_recommendations_tutorial(self):
        """Tutorial das recomendações IA"""
        print(f"{Colors.MAGENTA}💡 Recomendações Inteligentes{Colors.RESET}")
        print()
        print("Sistema avançado que:")
        print("   • Combina perfil do CV com vagas disponíveis")
        print("   • Calcula compatibilidade multi-dimensional")
        print("   • Aprende com seu feedback")
        print("   • Oferece explicações detalhadas")
        print("   • Personaliza recomendações ao longo do tempo")
        print()
        print(f"{Colors.YELLOW}📝 Fluxo recomendado:{Colors.RESET}")
        print("   1. Analise seu CV primeiro")
        print("   2. Colete vagas recentes do mercado")
        print("   3. Execute matching inteligente")
        print("   4. Dê feedback nas recomendações")
        print("   5. Sistema aprende e melhora")
    
    def _show_bi_tutorial(self):
        """Tutorial do Business Intelligence"""
        print(f"{Colors.CYAN}📊 Business Intelligence{Colors.RESET}")
        print()
        print("Análises disponíveis:")
        print("   • Tendências salariais por região e senioridade")
        print("   • Skills em alta demanda no mercado")
        print("   • Mapas de calor de oportunidades")
        print("   • Análise histórica e projeções")
        print("   • Relatórios executivos automáticos")
        print()
        print(f"{Colors.YELLOW}📝 Melhores práticas:{Colors.RESET}")
        print("   1. Colete dados regularmente para análises precisas")
        print("   2. Use análises para identificar oportunidades")
        print("   3. Monitore tendências de skills")
        print("   4. Exporte relatórios para tomada de decisão")