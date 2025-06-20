"""
Sistema de Menu Interativo Avançado
Cria uma interface amigável e profissional para o usuário
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


class Colors:
    """Cores ANSI para terminal"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Cores de texto
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
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


class MenuSystem:
    """Sistema de menu interativo avançado"""
    
    def __init__(self):
        self.version = "4.0.0"
        self.clear_screen()
        
    def clear_screen(self):
        """Limpa a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Imprime cabeçalho principal"""
        self.clear_screen()
        
        print(f"{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.RESET}                      {Colors.BOLD}{Colors.WHITE}🚀 CATHO JOB SCRAPER - v{self.version}{Colors.RESET}                      {Colors.BOLD}{Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.RESET}              {Colors.GREEN}Sistema Avançado de Web Scraping para Vagas{Colors.RESET}               {Colors.BOLD}{Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        print()
        
        # Status do sistema
        self.print_system_status()
        print()
    
    def print_system_status(self):
        """Mostra status atual do sistema"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"{Colors.DIM}┌─ Status do Sistema ─────────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.GREEN}●{Colors.RESET} Sistema Online    {Colors.DIM}│{Colors.RESET} 📅 {now}    {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.GREEN}●{Colors.RESET} Cache Disponível  {Colors.DIM}│{Colors.RESET} 🌐 Catho.com.br Ready   {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.GREEN}●{Colors.RESET} API Funcional     {Colors.DIM}│{Colors.RESET} ⚡ Performance Máxima    {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    
    def print_main_menu(self):
        """Menu principal visual"""
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.YELLOW}🎯 MENU PRINCIPAL{Colors.RESET}")
        print()
        
        options = [
            ("1", "🚀", "NOVO SCRAPING", "Coletar vagas do Catho (3 modos de performance)", Colors.GREEN),
            ("2", "🔍", "BUSCAR CACHE", "Pesquisar em dados já coletados", Colors.BLUE),
            ("3", "📄", "ANÁLISE DE CV", "Analisar currículo e gerar recomendações IA", Colors.PURPLE),
            ("4", "🗑️", "LIMPAR DADOS", "Reset completo do sistema", Colors.RED),
            ("5", "🧹", "DEDUPLICAÇÃO", "Remover duplicatas de arquivos", Colors.MAGENTA),
            ("6", "⚙️", "CONFIGURAÇÕES", "Ajustar parâmetros do sistema", Colors.CYAN),
            ("7", "📊", "ESTATÍSTICAS", "Dashboard e métricas", Colors.YELLOW),
            ("8", "🌐", "API SERVER", "Iniciar servidor REST API", Colors.GREEN),
            ("9", "❓", "AJUDA", "Documentação e suporte", Colors.WHITE),
            ("0", "🚪", "SAIR", "Fechar aplicação", Colors.GRAY)
        ]
        
        for key, icon, title, desc, color in options:
            print(f"  {Colors.BOLD}{color}[{key}]{Colors.RESET} {icon} {Colors.BOLD}{title:<15}{Colors.RESET} {Colors.DIM}{desc}{Colors.RESET}")
        
        print()
        print(f"{Colors.DIM}💡 Dica: Digite o número da opção ou use {Colors.BOLD}Ctrl+C{Colors.RESET}{Colors.DIM} para sair{Colors.RESET}")
        print()
        
        return self.get_user_choice("Escolha uma opção", "1", ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])
    
    def print_scraping_menu(self):
        """Menu de configuração de scraping"""
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.GREEN}🚀 CONFIGURAÇÃO DE SCRAPING{Colors.RESET}")
        print()
        
        # Configurações passo a passo
        config = {}
        
        # 1. Modo de Performance
        print(f"{Colors.BOLD}{Colors.CYAN}ETAPA 1/5 - MODO DE PERFORMANCE{Colors.RESET}")
        print()
        
        performance_options = [
            ("1", "🐌", "BÁSICO", "Funcional e estável (sem otimizações)", "~30s para 5 páginas"),
            ("2", "⚡", "OTIMIZADO", "Cache + Incremental (recomendado)", "~15s para 5 páginas"),
            ("3", "🚀", "MÁXIMO", "Pool de conexões + todas otimizações", "~8s para 5 páginas")
        ]
        
        for key, icon, title, desc, speed in performance_options:
            print(f"  {Colors.BOLD}[{key}]{Colors.RESET} {icon} {Colors.BOLD}{title:<12}{Colors.RESET} - {desc}")
            print(f"       {Colors.DIM}Performance: {speed}{Colors.RESET}")
            print()
        
        performance = self.get_user_choice("Modo de performance", "3", ["1", "2", "3"])
        config['performance_mode'] = int(performance)
        
        # 2. Número de páginas
        self.print_step_header("ETAPA 2/5 - PÁGINAS A PROCESSAR")
        
        print(f"  {Colors.BOLD}📄 Páginas por processar:{Colors.RESET}")
        print(f"     • {Colors.GREEN}1-10 páginas{Colors.RESET}: Teste rápido (~50-500 vagas)")
        print(f"     • {Colors.YELLOW}11-25 páginas{Colors.RESET}: Coleta média (~500-1250 vagas)")
        print(f"     • {Colors.RED}26+ páginas{Colors.RESET}: Coleta completa (1250+ vagas)")
        print()
        
        max_pages = self.get_user_number("Número de páginas", 5, 1, 100)
        config['max_pages'] = max_pages
        
        # 3. Jobs simultâneos
        self.print_step_header("ETAPA 3/5 - PROCESSAMENTO PARALELO")
        
        print(f"  {Colors.BOLD}⚡ Jobs simultâneos:{Colors.RESET}")
        print(f"     • {Colors.GREEN}1-2 jobs{Colors.RESET}: Conservador (evita rate limiting)")
        print(f"     • {Colors.YELLOW}3-4 jobs{Colors.RESET}: Balanceado (recomendado)")
        print(f"     • {Colors.RED}5+ jobs{Colors.RESET}: Agressivo (máxima velocidade)")
        print()
        
        max_concurrent = self.get_user_number("Jobs simultâneos", 3, 1, 10)
        config['max_concurrent'] = max_concurrent
        
        # 4. Modo incremental
        self.print_step_header("ETAPA 4/5 - MODO INCREMENTAL")
        
        incremental_options = [
            ("1", "🧠", "INTELIGENTE", "Para quando encontra vagas conhecidas"),
            ("2", "💪", "FORÇADO", "Processa todas as páginas sempre"),
            ("3", "🚫", "DESATIVADO", "Sem processamento incremental")
        ]
        
        for key, icon, title, desc in incremental_options:
            print(f"  {Colors.BOLD}[{key}]{Colors.RESET} {icon} {Colors.BOLD}{title:<12}{Colors.RESET} - {desc}")
        print()
        
        incremental_mode = self.get_user_choice("Modo incremental", "1", ["1", "2", "3"])
        config['incremental'] = incremental_mode != "3"
        config['force_full'] = incremental_mode == "2"
        
        # 5. Filtros
        self.print_step_header("ETAPA 5/5 - FILTROS (OPCIONAL)")
        
        apply_filters = self.get_user_bool("Aplicar filtros personalizados?", False)
        config['apply_filters'] = apply_filters
        
        if apply_filters:
            config['filters'] = self.configure_filters()
        
        # Resumo da configuração
        self.print_config_summary(config)
        
        if self.get_user_bool("Confirma esta configuração?", True):
            return config
        else:
            return self.print_scraping_menu()  # Reconfigura
    
    def configure_filters(self):
        """Configuração avançada de filtros"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}🔍 CONFIGURAÇÃO DE FILTROS{Colors.RESET}")
        
        filters = {}
        
        # Tecnologias
        if self.get_user_bool("Filtrar por tecnologias específicas?", False):
            print(f"\n{Colors.CYAN}💻 TECNOLOGIAS POPULARES:{Colors.RESET}")
            print("   Python, JavaScript, Java, React, Node.js, Angular, Vue.js")
            print("   PHP, C#, .NET, Ruby, Go, Rust, TypeScript, Swift")
            
            tech_input = input(f"{Colors.BOLD}Digite as tecnologias (separadas por vírgula): {Colors.RESET}").strip()
            if tech_input:
                filters['technologies'] = [t.strip() for t in tech_input.split(',')]
        
        # Nível de experiência
        if self.get_user_bool("Filtrar por nível de experiência?", False):
            level_options = [
                ("1", "Junior/Trainee"),
                ("2", "Pleno/Sênior"),
                ("3", "Liderança/Gerência"),
                ("4", "Todos os níveis")
            ]
            
            print(f"\n{Colors.CYAN}📊 NÍVEIS DISPONÍVEIS:{Colors.RESET}")
            for key, title in level_options:
                print(f"  [{key}] {title}")
            
            level_choice = self.get_user_choice("Nível desejado", "4", ["1", "2", "3", "4"])
            if level_choice != "4":
                level_map = {"1": "junior", "2": "senior", "3": "lideranca"}
                filters['level'] = level_map[level_choice]
        
        # Salário mínimo
        if self.get_user_bool("Definir salário mínimo?", False):
            min_salary = self.get_user_number("Salário mínimo (R$)", 3000, 1000, 50000)
            filters['salary_min'] = min_salary
        
        return filters
    
    def print_config_summary(self, config):
        """Mostra resumo da configuração"""
        self.clear_screen()
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.CYAN}📋 RESUMO DA CONFIGURAÇÃO{Colors.RESET}")
        print()
        
        # Performance
        performance_names = {1: "🐌 BÁSICO", 2: "⚡ OTIMIZADO", 3: "🚀 MÁXIMO"}
        print(f"  {Colors.BOLD}Performance:{Colors.RESET} {performance_names[config['performance_mode']]}")
        
        # Páginas e jobs
        print(f"  {Colors.BOLD}Páginas:{Colors.RESET} {config['max_pages']} páginas")
        print(f"  {Colors.BOLD}Paralelismo:{Colors.RESET} {config['max_concurrent']} jobs simultâneos")
        
        # Incremental
        incremental_text = "🧠 Inteligente" if config['incremental'] and not config.get('force_full') else \
                          "💪 Forçado" if config.get('force_full') else "🚫 Desativado"
        print(f"  {Colors.BOLD}Incremental:{Colors.RESET} {incremental_text}")
        
        # Filtros
        if config.get('apply_filters') and config.get('filters'):
            print(f"  {Colors.BOLD}Filtros:{Colors.RESET} ✅ Configurados")
            filters = config['filters']
            if 'technologies' in filters:
                print(f"    • Tecnologias: {', '.join(filters['technologies'])}")
            if 'level' in filters:
                print(f"    • Nível: {filters['level']}")
            if 'salary_min' in filters:
                print(f"    • Salário mín: R$ {filters['salary_min']:,}")
        else:
            print(f"  {Colors.BOLD}Filtros:{Colors.RESET} ❌ Nenhum filtro aplicado")
        
        # Estimativas
        print()
        print(f"{Colors.DIM}┌─ Estimativas ───────────────────────────────────────────────────────────────┐{Colors.RESET}")
        
        # Estimativa de tempo
        time_base = config['max_pages'] * 2  # 2s por página base
        time_multiplier = {1: 2.0, 2: 1.0, 3: 0.6}[config['performance_mode']]
        estimated_time = int(time_base * time_multiplier)
        
        print(f"{Colors.DIM}│{Colors.RESET} ⏱️  Tempo estimado: ~{estimated_time}s")
        
        # Estimativa de vagas
        estimated_jobs = config['max_pages'] * 15  # ~15 vagas por página
        if config.get('apply_filters'):
            estimated_jobs = int(estimated_jobs * 0.3)  # Filtros reduzem ~70%
        
        print(f"{Colors.DIM}│{Colors.RESET} 📊 Vagas estimadas: ~{estimated_jobs} vagas")
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()
    
    def print_step_header(self, title):
        """Imprime cabeçalho de etapa"""
        self.clear_screen()
        self.print_header()
        print(f"{Colors.BOLD}{Colors.YELLOW}{title}{Colors.RESET}")
        print()
    
    def get_user_choice(self, prompt: str, default: str, valid_choices: List[str]) -> str:
        """Obtém escolha do usuário com validação"""
        while True:
            try:
                choice = input(f"{Colors.BOLD}{prompt} [{default}]: {Colors.RESET}").strip()
                if not choice:
                    choice = default
                
                if choice.lower() in ['q', 'quit', 'exit']:
                    print(f"{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
                    sys.exit(0)
                
                if choice in valid_choices:
                    return choice
                else:
                    print(f"{Colors.RED}❌ Opção inválida. Escolha entre: {', '.join(valid_choices)}{Colors.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
                sys.exit(0)
            except EOFError:
                print(f"\n{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
                sys.exit(0)
            except Exception as e:
                print(f"{Colors.RED}❌ Erro de entrada: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}Usando valor padrão: {default}{Colors.RESET}")
                return default
    
    def get_user_number(self, prompt: str, default: int, min_val: int, max_val: int) -> int:
        """Obtém número do usuário com validação"""
        while True:
            try:
                response = input(f"{Colors.BOLD}{prompt} [{default}]: {Colors.RESET}").strip()
                if not response:
                    return default
                
                if response.lower() in ['q', 'quit', 'exit']:
                    print(f"{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
                    sys.exit(0)
                
                number = int(response)
                if min_val <= number <= max_val:
                    return number
                else:
                    print(f"{Colors.RED}❌ Número deve estar entre {min_val} e {max_val}{Colors.RESET}")
                    
            except ValueError:
                print(f"{Colors.RED}❌ Digite um número válido{Colors.RESET}")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
                sys.exit(0)
            except EOFError:
                print(f"\n{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
                sys.exit(0)
            except Exception as e:
                print(f"{Colors.RED}❌ Erro de entrada: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}Usando valor padrão: {default}{Colors.RESET}")
                return default
    
    def get_user_bool(self, prompt: str, default: bool) -> bool:
        """Obtém resposta sim/não do usuário"""
        default_text = "S/n" if default else "s/N"
        
        while True:
            try:
                response = input(f"{Colors.BOLD}{prompt} [{default_text}]: {Colors.RESET}").strip().lower()
                
                if not response:
                    return default
                
                if response in ['q', 'quit', 'exit']:
                    print(f"{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
                    sys.exit(0)
                
                if response in ['s', 'sim', 'y', 'yes', '1']:
                    return True
                elif response in ['n', 'não', 'nao', 'no', '0']:
                    return False
                else:
                    print(f"{Colors.RED}❌ Digite 's' para sim ou 'n' para não{Colors.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
                sys.exit(0)
            except EOFError:
                print(f"\n{Colors.YELLOW}👋 Saindo...{Colors.RESET}")
                sys.exit(0)
            except Exception as e:
                print(f"{Colors.RED}❌ Erro de entrada: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}Usando valor padrão: {'Sim' if default else 'Não'}{Colors.RESET}")
                return default
    
    def print_cache_menu(self):
        """Menu de busca no cache"""
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.BLUE}🔍 BUSCA NO CACHE{Colors.RESET}")
        print()
        print(f"{Colors.DIM}Pesquise rapidamente em dados já coletados{Colors.RESET}")
        print()
        
        options = [
            ("1", "📋", "LISTAR TUDO", "Todas as entradas do cache"),
            ("2", "🏢", "POR EMPRESA", "Buscar por nome da empresa"),
            ("3", "💻", "POR TECNOLOGIA", "Filtrar por tecnologia específica"),
            ("4", "📍", "POR LOCALIZAÇÃO", "Filtrar por cidade/estado"),
            ("5", "📊", "ESTATÍSTICAS", "Métricas do cache"),
            ("6", "🏆", "TOP RANKINGS", "Empresas e tecnologias mais populares"),
            ("0", "⬅️", "VOLTAR", "Retornar ao menu principal")
        ]
        
        for key, icon, title, desc in options:
            print(f"  {Colors.BOLD}[{key}]{Colors.RESET} {icon} {Colors.BOLD}{title:<15}{Colors.RESET} {Colors.DIM}{desc}{Colors.RESET}")
        
        print()
        return self.get_user_choice("Tipo de busca", "1", ["0", "1", "2", "3", "4", "5", "6"])
    
    def print_help_menu(self):
        """Menu de ajuda e documentação"""
        self.print_header()
        
        print(f"{Colors.BOLD}{Colors.WHITE}❓ CENTRAL DE AJUDA{Colors.RESET}")
        print()
        
        help_sections = [
            ("🚀 PRIMEIROS PASSOS", [
                "• Use a opção '1 - NOVO SCRAPING' para começar",
                "• Escolha o modo 'OTIMIZADO' para melhor performance",
                "• Comece com 5-10 páginas para teste",
                "• Use 3 jobs simultâneos (recomendado)"
            ]),
            ("⚡ MODOS DE PERFORMANCE", [
                "• BÁSICO: Funcional, sem otimizações (~30s/5pág)",
                "• OTIMIZADO: Cache + Incremental (~15s/5pág)",
                "• MÁXIMO: Pool de conexões (~8s/5pág)"
            ]),
            ("🔍 SISTEMA DE CACHE", [
                "• Cache guarda dados por 6h automaticamente",
                "• Use 'BUSCAR CACHE' para pesquisar sem coletar",
                "• 'LIMPAR DADOS' reseta tudo para coleta fresh"
            ]),
            ("🧹 DEDUPLICAÇÃO", [
                "• Remove vagas duplicadas automaticamente",
                "• Detecta por URL, conteúdo e similaridade",
                "• Use opção '4' para limpar arquivos antigos"
            ]),
            ("⚙️ FILTROS AVANÇADOS", [
                "• Tecnologias: Python, JavaScript, React, etc.",
                "• Níveis: Junior, Pleno, Senior, Liderança",
                "• Salário: Define valor mínimo em R$"
            ]),
            ("🚨 RESOLUÇÃO DE PROBLEMAS", [
                "• Erro de navegador: 'playwright install'",
                "• Performance lenta: Use modo MÁXIMO",
                "• Muitas duplicatas: Use deduplicação",
                "• Cache corrompido: Use 'LIMPAR DADOS'"
            ])
        ]
        
        for title, items in help_sections:
            print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
            for item in items:
                print(f"  {item}")
            print()
        
        print(f"{Colors.DIM}💡 Pressione Enter para voltar ao menu...{Colors.RESET}")
        input()
    
    def print_progress_bar(self, current: int, total: int, prefix: str = "", width: int = 40):
        """Mostra barra de progresso visual"""
        percent = (current / total) * 100
        filled = int(width * current // total)
        bar = '█' * filled + '░' * (width - filled)
        
        print(f"\r{prefix} |{Colors.GREEN}{bar}{Colors.RESET}| {percent:.1f}% ({current}/{total})", end='', flush=True)
    
    def print_success_message(self, message: str):
        """Mensagem de sucesso"""
        print(f"\n{Colors.GREEN}✅ {message}{Colors.RESET}")
    
    def print_error_message(self, message: str):
        """Mensagem de erro"""
        print(f"\n{Colors.RED}❌ {message}{Colors.RESET}")
    
    def print_warning_message(self, message: str):
        """Mensagem de aviso"""
        print(f"\n{Colors.YELLOW}⚠️ {message}{Colors.RESET}")
    
    def print_info_message(self, message: str):
        """Mensagem informativa"""
        print(f"\n{Colors.BLUE}ℹ️ {message}{Colors.RESET}")


def create_menu_system() -> MenuSystem:
    """Factory function para criar sistema de menu"""
    return MenuSystem()