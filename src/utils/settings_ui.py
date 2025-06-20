"""
Interface Visual para Configurações Avançadas
=============================================

Este módulo implementa uma interface visual completa para gerenciar
todas as configurações do sistema de forma intuitiva.
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

from .menu_system import MenuSystem, Colors
from .settings_manager import settings_manager, SystemSettings


class SettingsUI:
    """
    Interface visual para configurações do sistema
    
    Funcionalidades:
    - Menu hierárquico de configurações
    - Edição visual de valores
    - Validação em tempo real
    - Backup e restauração
    - Import/Export
    """
    
    def __init__(self):
        self.menu = MenuSystem()
        self.settings_manager = settings_manager
    
    def show_main_settings_menu(self) -> bool:
        """
        Mostra menu principal de configurações
        
        Returns:
            bool: True se deve continuar, False para sair
        """
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            choice = self._print_main_menu()
            
            if choice == "0":  # Voltar
                return True
            elif choice == "1":  # Configurações de Scraping
                self._handle_scraping_settings()
            elif choice == "2":  # Configurações de Cache
                self._handle_cache_settings()
            elif choice == "3":  # Configurações de Performance
                self._handle_performance_settings()
            elif choice == "4":  # Configurações de Saída
                self._handle_output_settings()
            elif choice == "5":  # Configurações de Logs
                self._handle_logging_settings()
            elif choice == "6":  # Configurações de Alertas
                self._handle_alerts_settings()
            elif choice == "7":  # Configurações do Navegador
                self._handle_browser_settings()
            elif choice == "8":  # Gerenciamento de Perfis
                self._handle_profile_management()
            elif choice == "9":  # Import/Export
                self._handle_import_export()
            elif choice == "10":  # Reset para Padrão
                self._handle_reset_defaults()
            elif choice == "11":  # Validar Configurações
                self._handle_validate_settings()
    
    def _print_settings_header(self):
        """Imprime cabeçalho das configurações"""
        profile_info = self.settings_manager.get_current_profile_info()
        
        print(f"{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.RESET}                  {Colors.BOLD}{Colors.WHITE}⚙️  CONFIGURAÇÕES AVANÇADAS - v{self.settings_manager.settings.version}{Colors.RESET}                  {Colors.BOLD}{Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}║{Colors.RESET}                {Colors.GREEN}Sistema de Gerenciamento Completo de Configurações{Colors.RESET}               {Colors.BOLD}{Colors.CYAN}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        print()
        
        # Status das configurações com melhor formatação
        print(f"{Colors.DIM}┌─ Status do Sistema ─────────────────────────────────────────────────────────┐{Colors.RESET}")
        
        # Linha 1: Perfil e Status
        errors = self.settings_manager.validate_settings()
        status_text = f"{Colors.GREEN}✅ Válidas{Colors.RESET}" if not errors else f"{Colors.RED}⚠️  {len(errors)} erro(s){Colors.RESET}"
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}📋 Perfil:{Colors.RESET} {Colors.CYAN}{profile_info['name']}{Colors.RESET}{' ' * (20 - len(profile_info['name']))}│ {Colors.BOLD}✅ Status:{Colors.RESET} {status_text}{' ' * max(0, 15 - len(str(len(errors))) if errors else 15)}│")
        
        # Linha 2: Arquivo e Backups  
        config_file = profile_info['config_file'].replace('\\', '/')
        if len(config_file) > 35:
            config_file = "..." + config_file[-32:]
        backup_text = f"{Colors.GREEN}✅ Disponíveis{Colors.RESET}" if profile_info['has_backups'] else f"{Colors.YELLOW}❌ Nenhum{Colors.RESET}"
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}📁 Arquivo:{Colors.RESET} {config_file}{' ' * max(0, 35 - len(config_file))}│ {Colors.BOLD}💾 Backups:{Colors.RESET} {backup_text}{' ' * max(0, 10)}│")
        
        # Linha 3: Data de atualização e versão
        updated_date = profile_info.get('updated_at', 'N/A')[:19].replace('T', ' ')
        if updated_date == 'N/A':
            updated_date = "Não disponível"
        elif len(updated_date) > 19:
            updated_date = updated_date[:19]
        
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}🕒 Atualizado:{Colors.RESET} {Colors.YELLOW}{updated_date}{Colors.RESET}{' ' * max(0, 19 - len(updated_date))}│ {Colors.BOLD}🔧 Versão:{Colors.RESET} {Colors.MAGENTA}v{self.settings_manager.settings.version}{Colors.RESET}{' ' * max(0, 12 - len(self.settings_manager.settings.version))}│")
        
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()
    
    def _print_main_menu(self) -> str:
        """Imprime menu principal e retorna escolha"""
        print(f"{Colors.BOLD}{Colors.YELLOW}🎛️  MENU DE CONFIGURAÇÕES{Colors.RESET}")
        print()
        
        # Dividir opções em grupos para melhor organização
        main_options = [
            ("1", "🚀", "SCRAPING", "URLs, concorrência, páginas, rate limiting"),
            ("2", "💾", "CACHE", "Diretório, tempo de vida, limpeza automática"),
            ("3", "⚡", "PERFORMANCE", "Timeouts, retry, pool de conexões"),
            ("4", "📁", "SAÍDA", "Diretórios, formatos, relatórios"),
            ("5", "📝", "LOGS", "Níveis, arquivos, rotação"),
            ("6", "🚨", "ALERTAS", "Email, webhook, canais de notificação"),
            ("7", "🌐", "NAVEGADOR", "Headless, user-agent, argumentos")
        ]
        
        management_options = [
            ("8", "👤", "PERFIS", "Gerenciar perfis de configuração"),
            ("9", "📤", "IMPORT/EXPORT", "Backup, restauração, compartilhamento"),
            ("10", "🔄", "RESET PADRÃO", "Restaurar configurações originais"),
            ("11", "✅", "VALIDAR", "Verificar configurações atuais")
        ]
        
        # Imprimir opções principais
        print(f"{Colors.DIM}┌─ Configurações Principais ──────────────────────────────────────────────────┐{Colors.RESET}")
        for key, icon, title, desc in main_options:
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}{Colors.GREEN}[{key:>2}]{Colors.RESET} {icon} {Colors.BOLD}{title:<12}{Colors.RESET} │ {Colors.DIM}{desc:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()
        
        # Imprimir opções de gerenciamento
        print(f"{Colors.DIM}┌─ Gerenciamento e Ferramentas ───────────────────────────────────────────────┐{Colors.RESET}")
        for key, icon, title, desc in management_options:
            color = Colors.CYAN if key != "10" else Colors.YELLOW
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}{color}[{key:>2}]{Colors.RESET} {icon} {Colors.BOLD}{title:<12}{Colors.RESET} │ {Colors.DIM}{desc:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()
        
        # Opção de voltar
        print(f"  {Colors.BOLD}{Colors.GRAY}[0]{Colors.RESET} ⬅️  {Colors.BOLD}VOLTAR{Colors.RESET}          {Colors.DIM}Retornar ao menu principal{Colors.RESET}")
        print()
        
        print(f"{Colors.DIM}💡 Dica: As configurações são salvas automaticamente após cada alteração{Colors.RESET}")
        print(f"{Colors.DIM}🔧 Suporte: Use {Colors.BOLD}[11] VALIDAR{Colors.RESET}{Colors.DIM} para verificar problemas{Colors.RESET}")
        print()
        
        return self.menu.get_user_choice("Escolha uma opção", "1", 
                                       ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"])
    
    def _handle_scraping_settings(self):
        """Gerencia configurações de scraping"""
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            print(f"{Colors.BOLD}{Colors.GREEN}🚀 CONFIGURAÇÕES DE SCRAPING{Colors.RESET}")
            print()
            
            settings = self.settings_manager.settings.scraping
            
            # Mostrar configurações atuais com melhor formatação
            print(f"{Colors.BOLD}📋 CONFIGURAÇÕES DE SCRAPING ATUAIS{Colors.RESET}")
            print()
            print(f"{Colors.DIM}┌─ Parâmetros de Coleta ──────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[1]{Colors.RESET} 🌐 URL Base                │ {Colors.CYAN}{settings.base_url:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[2]{Colors.RESET} ⚡ Jobs Simultâneos         │ {Colors.YELLOW}{settings.max_concurrent_jobs:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[3]{Colors.RESET} 📄 Máximo de Páginas       │ {Colors.YELLOW}{settings.max_pages:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[4]{Colors.RESET} 🚦 Requisições/Segundo     │ {Colors.YELLOW}{settings.requests_per_second:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[5]{Colors.RESET} 💥 Limite de Burst         │ {Colors.YELLOW}{settings.burst_limit:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            print(f"{Colors.DIM}┌─ Otimizações ───────────────────────────────────────────────────────────────┐{Colors.RESET}")
            incremental_status = f"{Colors.GREEN}✅ Ativado{Colors.RESET}" if settings.enable_incremental else f"{Colors.RED}❌ Desativado{Colors.RESET}"
            dedup_status = f"{Colors.GREEN}✅ Ativada{Colors.RESET}" if settings.enable_deduplication else f"{Colors.RED}❌ Desativada{Colors.RESET}"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[6]{Colors.RESET} 🔄 Processamento Incremental│ {incremental_status:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[7]{Colors.RESET} 🧹 Deduplicação           │ {dedup_status:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[8]{Colors.RESET} 🗜️  Nível de Compressão    │ {Colors.YELLOW}{settings.compression_level} (1-9, padrão 6){' ' * 15}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Menu de opções
            choice = self.menu.get_user_choice("Editar configuração (0 para voltar)", "0", 
                                             ["0", "1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "0":
                break
            elif choice == "1":
                new_url = input(f"{Colors.BOLD}Nova URL base: {Colors.RESET}").strip()
                if new_url:
                    settings.base_url = new_url
                    self._save_settings_with_feedback()
            elif choice == "2":
                new_value = self.menu.get_user_number("Jobs simultâneos", settings.max_concurrent_jobs, 1, 10)
                settings.max_concurrent_jobs = new_value
                self._save_settings_with_feedback()
            elif choice == "3":
                new_value = self.menu.get_user_number("Máximo de páginas", settings.max_pages, 1, 100)
                settings.max_pages = new_value
                self._save_settings_with_feedback()
            elif choice == "4":
                response = input(f"{Colors.BOLD}Requisições por segundo [{settings.requests_per_second}]: {Colors.RESET}").strip()
                if response:
                    try:
                        new_value = float(response)
                        if 0.1 <= new_value <= 10:
                            settings.requests_per_second = new_value
                            self._save_settings_with_feedback()
                        else:
                            self.menu.print_error_message("Valor deve estar entre 0.1 e 10")
                            input("Pressione Enter...")
                    except ValueError:
                        self.menu.print_error_message("Valor inválido")
                        input("Pressione Enter...")
            elif choice == "5":
                new_value = self.menu.get_user_number("Limite de burst", settings.burst_limit, 1, 20)
                settings.burst_limit = new_value
                self._save_settings_with_feedback()
            elif choice == "6":
                settings.enable_incremental = not settings.enable_incremental
                self._save_settings_with_feedback()
            elif choice == "7":
                settings.enable_deduplication = not settings.enable_deduplication
                self._save_settings_with_feedback()
            elif choice == "8":
                new_value = self.menu.get_user_number("Nível de compressão", settings.compression_level, 1, 9)
                settings.compression_level = new_value
                self._save_settings_with_feedback()
    
    def _handle_cache_settings(self):
        """Gerencia configurações de cache"""
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            print(f"{Colors.BOLD}{Colors.BLUE}💾 CONFIGURAÇÕES DE CACHE{Colors.RESET}")
            print()
            
            settings = self.settings_manager.settings.cache
            
            # Mostrar configurações atuais com melhor formatação
            print(f"{Colors.BOLD}📋 CONFIGURAÇÕES DE CACHE ATUAIS{Colors.RESET}")
            print()
            print(f"{Colors.DIM}┌─ Armazenamento ─────────────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[1]{Colors.RESET} 📁 Diretório de Cache      │ {Colors.CYAN}{settings.cache_dir:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[2]{Colors.RESET} ⏰ Tempo de Vida (horas)   │ {Colors.YELLOW}{settings.max_age_hours} horas{' ' * 25}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[4]{Colors.RESET} 💾 Tamanho Máximo (MB)     │ {Colors.YELLOW}{settings.max_cache_size_mb} MB{' ' * 28}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            print(f"{Colors.DIM}┌─ Manutenção Automática ─────────────────────────────────────────────────────┐{Colors.RESET}")
            cleanup_status = f"{Colors.GREEN}✅ Ativada{Colors.RESET}" if settings.auto_cleanup else f"{Colors.RED}❌ Desativada{Colors.RESET}"
            rebuild_status = f"{Colors.GREEN}✅ Ativado{Colors.RESET}" if settings.rebuild_index_on_startup else f"{Colors.RED}❌ Desativado{Colors.RESET}"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[3]{Colors.RESET} 🧹 Limpeza Automática      │ {cleanup_status:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[5]{Colors.RESET} 🔄 Recriar Índice na Init. │ {rebuild_status:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Menu de opções
            choice = self.menu.get_user_choice("Editar configuração (0 para voltar)", "0", 
                                             ["0", "1", "2", "3", "4", "5"])
            
            if choice == "0":
                break
            elif choice == "1":
                new_dir = input(f"{Colors.BOLD}Novo diretório de cache: {Colors.RESET}").strip()
                if new_dir:
                    settings.cache_dir = new_dir
                    self._save_settings_with_feedback()
            elif choice == "2":
                new_value = self.menu.get_user_number("Tempo de vida (horas)", settings.max_age_hours, 1, 168)
                settings.max_age_hours = new_value
                self._save_settings_with_feedback()
            elif choice == "3":
                settings.auto_cleanup = not settings.auto_cleanup
                self._save_settings_with_feedback()
            elif choice == "4":
                new_value = self.menu.get_user_number("Tamanho máximo (MB)", settings.max_cache_size_mb, 10, 5000)
                settings.max_cache_size_mb = new_value
                self._save_settings_with_feedback()
            elif choice == "5":
                settings.rebuild_index_on_startup = not settings.rebuild_index_on_startup
                self._save_settings_with_feedback()
    
    def _handle_performance_settings(self):
        """Gerencia configurações de performance"""
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            print(f"{Colors.BOLD}{Colors.YELLOW}⚡ CONFIGURAÇÕES DE PERFORMANCE{Colors.RESET}")
            print()
            
            settings = self.settings_manager.settings.performance
            
            # Mostrar configurações atuais com melhor formatação
            print(f"{Colors.BOLD}📋 CONFIGURAÇÕES DE PERFORMANCE ATUAIS{Colors.RESET}")
            print()
            print(f"{Colors.DIM}┌─ Timeouts (milissegundos) ──────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[1]{Colors.RESET} ⏳ Carregamento de Página   │ {Colors.YELLOW}{settings.page_load_timeout:,} ms{' ' * 20}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[2]{Colors.RESET} 🌐 Timeout de Rede         │ {Colors.YELLOW}{settings.network_idle_timeout:,} ms{' ' * 20}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[3]{Colors.RESET} 🎯 Timeout de Elementos    │ {Colors.YELLOW}{settings.element_wait_timeout:,} ms{' ' * 25}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            print(f"{Colors.DIM}┌─ Sistema de Retry ──────────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[4]{Colors.RESET} 🔄 Tentativas de Retry     │ {Colors.YELLOW}{settings.retry_attempts} tentativas{' ' * 20}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[5]{Colors.RESET} ⏱️  Delay entre Tentativas  │ {Colors.YELLOW}{settings.retry_delay}s{' ' * 27}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            print(f"{Colors.DIM}┌─ Pool de Conexões ──────────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[6]{Colors.RESET} 📊 Tamanho Mínimo          │ {Colors.YELLOW}{settings.pool_min_size} conexões{' ' * 25}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[7]{Colors.RESET} 📈 Tamanho Máximo          │ {Colors.YELLOW}{settings.pool_max_size} conexões{' ' * 24}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Menu de opções
            choice = self.menu.get_user_choice("Editar configuração (0 para voltar)", "0", 
                                             ["0", "1", "2", "3", "4", "5", "6", "7"])
            
            if choice == "0":
                break
            elif choice == "1":
                new_value = self.menu.get_user_number("Timeout de carregamento (ms)", settings.page_load_timeout, 5000, 300000)
                settings.page_load_timeout = new_value
                self._save_settings_with_feedback()
            elif choice == "2":
                new_value = self.menu.get_user_number("Timeout de rede (ms)", settings.network_idle_timeout, 1000, 120000)
                settings.network_idle_timeout = new_value
                self._save_settings_with_feedback()
            elif choice == "3":
                new_value = self.menu.get_user_number("Timeout de elementos (ms)", settings.element_wait_timeout, 1000, 30000)
                settings.element_wait_timeout = new_value
                self._save_settings_with_feedback()
            elif choice == "4":
                new_value = self.menu.get_user_number("Tentativas de retry", settings.retry_attempts, 1, 10)
                settings.retry_attempts = new_value
                self._save_settings_with_feedback()
            elif choice == "5":
                response = input(f"{Colors.BOLD}Delay de retry (s) [{settings.retry_delay}]: {Colors.RESET}").strip()
                if response:
                    try:
                        new_value = float(response)
                        if 0.1 <= new_value <= 10:
                            settings.retry_delay = new_value
                            self._save_settings_with_feedback()
                        else:
                            self.menu.print_error_message("Valor deve estar entre 0.1 e 10")
                            input("Pressione Enter...")
                    except ValueError:
                        self.menu.print_error_message("Valor inválido")
                        input("Pressione Enter...")
            elif choice == "6":
                new_value = self.menu.get_user_number("Pool min size", settings.pool_min_size, 1, 20)
                settings.pool_min_size = new_value
                self._save_settings_with_feedback()
            elif choice == "7":
                new_value = self.menu.get_user_number("Pool max size", settings.pool_max_size, 2, 50)
                settings.pool_max_size = new_value
                self._save_settings_with_feedback()
    
    def _handle_output_settings(self):
        """Gerencia configurações de saída"""
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            print(f"{Colors.BOLD}{Colors.BLUE}📁 CONFIGURAÇÕES DE SAÍDA ATUAIS{Colors.RESET}")
            print()
            
            settings = self.settings_manager.settings.output
            
            # Mostrar configurações atuais com melhor formatação
            print(f"{Colors.DIM}┌─ Diretórios e Arquivos ─────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[1]{Colors.RESET} 📁 Diretório de Resultados │ {Colors.CYAN}{settings.results_dir:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[2]{Colors.RESET} 📄 Máx. Arquivos por Tipo  │ {Colors.YELLOW}{settings.max_files_per_type} arquivos{' ' * 25}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            cleanup_text = f"{Colors.GREEN}✅ Ativada{Colors.RESET}" if settings.auto_cleanup_results else f"{Colors.RED}❌ Desativada{Colors.RESET}"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[3]{Colors.RESET} 🧹 Limpeza Automática      │ {cleanup_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            print(f"{Colors.DIM}┌─ Formatos de Exportação ────────────────────────────────────────────────────┐{Colors.RESET}")
            formats_text = ", ".join(settings.export_formats)
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[4]{Colors.RESET} 📋 Formatos Ativos         │ {Colors.CYAN}{formats_text:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            reports_text = f"{Colors.GREEN}✅ Habilitados{Colors.RESET}" if settings.generate_reports else f"{Colors.RED}❌ Desabilitados{Colors.RESET}"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[5]{Colors.RESET} 📊 Relatórios Automáticos  │ {reports_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Menu de opções
            choice = self.menu.get_user_choice("Editar configuração (0 para voltar)", "0", 
                                             ["0", "1", "2", "3", "4", "5"])
            
            if choice == "0":
                break
            elif choice == "1":
                new_dir = input(f"{Colors.BOLD}Novo diretório de resultados: {Colors.RESET}").strip()
                if new_dir:
                    settings.results_dir = new_dir
                    self._save_settings_with_feedback()
            elif choice == "2":
                new_value = self.menu.get_user_number("Máximo de arquivos por tipo", settings.max_files_per_type, 1, 50)
                settings.max_files_per_type = new_value
                self._save_settings_with_feedback()
            elif choice == "3":
                settings.auto_cleanup_results = not settings.auto_cleanup_results
                self._save_settings_with_feedback()
            elif choice == "4":
                self._configure_export_formats(settings)
            elif choice == "5":
                settings.generate_reports = not settings.generate_reports
                self._save_settings_with_feedback()
    
    def _configure_export_formats(self, settings):
        """Configura formatos de exportação"""
        self.menu.clear_screen()
        self._print_settings_header()
        
        print(f"{Colors.BOLD}{Colors.CYAN}📋 CONFIGURAÇÃO DE FORMATOS DE EXPORTAÇÃO{Colors.RESET}")
        print()
        
        available_formats = ["json", "csv", "txt", "xlsx", "xml", "yaml"]
        current_formats = settings.export_formats.copy()
        
        print(f"{Colors.BOLD}Formatos disponíveis:{Colors.RESET}")
        print()
        
        for i, fmt in enumerate(available_formats, 1):
            status = f"{Colors.GREEN}✅ Ativo{Colors.RESET}" if fmt in current_formats else f"{Colors.DIM}❌ Inativo{Colors.RESET}"
            print(f"  {Colors.BOLD}[{i}]{Colors.RESET} {fmt.upper():<6} {status}")
        
        print()
        print(f"{Colors.DIM}Digite os números dos formatos desejados (ex: 1,2,3) ou Enter para manter atual{Colors.RESET}")
        
        response = input(f"{Colors.BOLD}Formatos desejados: {Colors.RESET}").strip()
        if response:
            try:
                selected_indices = [int(x.strip()) for x in response.split(',')]
                new_formats = []
                for idx in selected_indices:
                    if 1 <= idx <= len(available_formats):
                        new_formats.append(available_formats[idx - 1])
                
                if new_formats:
                    settings.export_formats = new_formats
                    self._save_settings_with_feedback()
                    print(f"{Colors.GREEN}✅ Formatos atualizados: {', '.join(new_formats)}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}❌ Nenhum formato válido selecionado{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}❌ Formato inválido. Use números separados por vírgula{Colors.RESET}")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_logging_settings(self):
        """Gerencia configurações de logging"""
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            print(f"{Colors.BOLD}{Colors.MAGENTA}📝 CONFIGURAÇÕES DE LOGGING ATUAIS{Colors.RESET}")
            print()
            
            settings = self.settings_manager.settings.logging
            
            # Mostrar configurações atuais com melhor formatação
            print(f"{Colors.DIM}┌─ Configurações Básicas ─────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[1]{Colors.RESET} 📊 Nível de Log            │ {Colors.YELLOW}{settings.log_level:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[2]{Colors.RESET} 📁 Diretório de Logs       │ {Colors.CYAN}{settings.log_dir:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            print(f"{Colors.DIM}┌─ Rotação de Arquivos ───────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[3]{Colors.RESET} 📄 Máx. Arquivos de Log    │ {Colors.YELLOW}{settings.max_log_files} arquivos{' ' * 25}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[4]{Colors.RESET} 💾 Tamanho Máx. por Log    │ {Colors.YELLOW}{settings.max_log_size_mb} MB{' ' * 30}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            print(f"{Colors.DIM}┌─ Logs Especializados ───────────────────────────────────────────────────────┐{Colors.RESET}")
            debug_text = f"{Colors.GREEN}✅ Habilitados{Colors.RESET}" if settings.enable_debug_logs else f"{Colors.RED}❌ Desabilitados{Colors.RESET}"
            perf_text = f"{Colors.GREEN}✅ Habilitados{Colors.RESET}" if settings.enable_performance_logs else f"{Colors.RED}❌ Desabilitados{Colors.RESET}"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[5]{Colors.RESET} 🐛 Logs de Debug          │ {debug_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[6]{Colors.RESET} ⚡ Logs de Performance     │ {perf_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Menu de opções
            choice = self.menu.get_user_choice("Editar configuração (0 para voltar)", "0", 
                                             ["0", "1", "2", "3", "4", "5", "6"])
            
            if choice == "0":
                break
            elif choice == "1":
                self._configure_log_level(settings)
            elif choice == "2":
                new_dir = input(f"{Colors.BOLD}Novo diretório de logs: {Colors.RESET}").strip()
                if new_dir:
                    settings.log_dir = new_dir
                    self._save_settings_with_feedback()
            elif choice == "3":
                new_value = self.menu.get_user_number("Máximo de arquivos de log", settings.max_log_files, 1, 100)
                settings.max_log_files = new_value
                self._save_settings_with_feedback()
            elif choice == "4":
                new_value = self.menu.get_user_number("Tamanho máximo por log (MB)", settings.max_log_size_mb, 1, 1000)
                settings.max_log_size_mb = new_value
                self._save_settings_with_feedback()
            elif choice == "5":
                settings.enable_debug_logs = not settings.enable_debug_logs
                self._save_settings_with_feedback()
            elif choice == "6":
                settings.enable_performance_logs = not settings.enable_performance_logs
                self._save_settings_with_feedback()
    
    def _configure_log_level(self, settings):
        """Configura nível de log"""
        self.menu.clear_screen()
        self._print_settings_header()
        
        print(f"{Colors.BOLD}{Colors.MAGENTA}📊 CONFIGURAÇÃO DE NÍVEL DE LOG{Colors.RESET}")
        print()
        
        log_levels = [
            ("1", "DEBUG", "Máximo detalhamento (desenvolvimento)"),
            ("2", "INFO", "Informações importantes (padrão)"),
            ("3", "WARNING", "Apenas avisos e erros"),
            ("4", "ERROR", "Apenas erros"),
            ("5", "CRITICAL", "Apenas erros críticos")
        ]
        
        current_level = settings.log_level
        
        print(f"{Colors.BOLD}Níveis disponíveis:{Colors.RESET}")
        print()
        
        for key, level, desc in log_levels:
            indicator = f" {Colors.GREEN}← ATUAL{Colors.RESET}" if level == current_level else ""
            print(f"  {Colors.BOLD}[{key}]{Colors.RESET} {Colors.YELLOW}{level:<8}{Colors.RESET} {Colors.DIM}{desc}{Colors.RESET}{indicator}")
        
        print()
        choice = self.menu.get_user_choice("Escolha o nível de log", "2", ["1", "2", "3", "4", "5"])
        
        level_map = {"1": "DEBUG", "2": "INFO", "3": "WARNING", "4": "ERROR", "5": "CRITICAL"}
        settings.log_level = level_map[choice]
        self._save_settings_with_feedback()
        
        print(f"{Colors.GREEN}✅ Nível de log alterado para: {settings.log_level}{Colors.RESET}")
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_alerts_settings(self):
        """Gerencia configurações de alertas"""
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            print(f"{Colors.BOLD}{Colors.RED}🚨 CONFIGURAÇÕES DE ALERTAS ATUAIS{Colors.RESET}")
            print()
            
            settings = self.settings_manager.settings.alerts
            
            # Mostrar configurações atuais com melhor formatação
            print(f"{Colors.DIM}┌─ Canais de Alerta ──────────────────────────────────────────────────────────┐{Colors.RESET}")
            console_text = f"{Colors.GREEN}✅ Ativo{Colors.RESET}" if settings.enable_console_alerts else f"{Colors.RED}❌ Inativo{Colors.RESET}"
            file_text = f"{Colors.GREEN}✅ Ativo{Colors.RESET}" if settings.enable_file_alerts else f"{Colors.RED}❌ Inativo{Colors.RESET}"
            email_text = f"{Colors.GREEN}✅ Ativo{Colors.RESET}" if settings.enable_email_alerts else f"{Colors.RED}❌ Inativo{Colors.RESET}"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[1]{Colors.RESET} 🖥️  Console/Terminal        │ {console_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[2]{Colors.RESET} 📄 Arquivo de Log          │ {file_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[3]{Colors.RESET} 📧 Email                   │ {email_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Configurações de Email
            if settings.enable_email_alerts:
                print(f"{Colors.DIM}┌─ Configurações de Email ────────────────────────────────────────────────────┐{Colors.RESET}")
                smtp_display = settings.email_smtp_server if settings.email_smtp_server else "Não configurado"
                port_display = f"{settings.email_port}" if settings.email_port else "Padrão"
                user_display = settings.email_username if settings.email_username else "Não configurado"
                recipients_display = f"{len(settings.email_recipients)} destinatário(s)" if settings.email_recipients else "Nenhum"
                
                print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[4]{Colors.RESET} 🌐 Servidor SMTP          │ {Colors.CYAN}{smtp_display:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
                print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[5]{Colors.RESET} 🔌 Porta                  │ {Colors.YELLOW}{port_display:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
                print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[6]{Colors.RESET} 👤 Usuário                │ {Colors.CYAN}{user_display:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
                print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[7]{Colors.RESET} 📮 Destinatários          │ {Colors.YELLOW}{recipients_display:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
                print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
                print()
            
            # Configurações de Webhook
            print(f"{Colors.DIM}┌─ Integração Externa ────────────────────────────────────────────────────────┐{Colors.RESET}")
            webhook_display = settings.webhook_url if settings.webhook_url else "Não configurado"
            webhook_status = f"{Colors.GREEN}✅ Configurado{Colors.RESET}" if settings.webhook_url else f"{Colors.YELLOW}❌ Não configurado{Colors.RESET}"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[8]{Colors.RESET} 🔗 Webhook URL            │ {webhook_status:<55} {Colors.DIM}│{Colors.RESET}")
            if settings.webhook_url:
                webhook_short = webhook_display[:40] + "..." if len(webhook_display) > 40 else webhook_display
                print(f"{Colors.DIM}│{Colors.RESET}     {Colors.CYAN}{webhook_short:<70}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Menu de opções
            available_choices = ["0", "1", "2", "3", "8"]
            if settings.enable_email_alerts:
                available_choices.extend(["4", "5", "6", "7"])
            
            choice = self.menu.get_user_choice("Editar configuração (0 para voltar)", "0", available_choices)
            
            if choice == "0":
                break
            elif choice == "1":
                settings.enable_console_alerts = not settings.enable_console_alerts
                self._save_settings_with_feedback()
            elif choice == "2":
                settings.enable_file_alerts = not settings.enable_file_alerts
                self._save_settings_with_feedback()
            elif choice == "3":
                settings.enable_email_alerts = not settings.enable_email_alerts
                self._save_settings_with_feedback()
            elif choice == "4" and settings.enable_email_alerts:
                new_smtp = input(f"{Colors.BOLD}Servidor SMTP (ex: smtp.gmail.com): {Colors.RESET}").strip()
                if new_smtp:
                    settings.email_smtp_server = new_smtp
                    self._save_settings_with_feedback()
            elif choice == "5" and settings.enable_email_alerts:
                new_port = self.menu.get_user_number("Porta SMTP", settings.email_port or 587, 1, 65535)
                settings.email_port = new_port
                self._save_settings_with_feedback()
            elif choice == "6" and settings.enable_email_alerts:
                new_user = input(f"{Colors.BOLD}Usuário/Email: {Colors.RESET}").strip()
                if new_user:
                    settings.email_username = new_user
                    # Solicitar senha
                    new_pass = input(f"{Colors.BOLD}Senha (será armazenada): {Colors.RESET}").strip()
                    if new_pass:
                        settings.email_password = new_pass
                    self._save_settings_with_feedback()
            elif choice == "7" and settings.enable_email_alerts:
                self._configure_email_recipients(settings)
            elif choice == "8":
                new_webhook = input(f"{Colors.BOLD}Webhook URL (deixe vazio para remover): {Colors.RESET}").strip()
                settings.webhook_url = new_webhook
                self._save_settings_with_feedback()
    
    def _configure_email_recipients(self, settings):
        """Configura destinatários de email"""
        self.menu.clear_screen()
        self._print_settings_header()
        
        print(f"{Colors.BOLD}{Colors.RED}📮 CONFIGURAÇÃO DE DESTINATÁRIOS{Colors.RESET}")
        print()
        
        if settings.email_recipients:
            print(f"{Colors.BOLD}Destinatários atuais:{Colors.RESET}")
            for i, email in enumerate(settings.email_recipients, 1):
                print(f"  {i}. {Colors.CYAN}{email}{Colors.RESET}")
            print()
        
        print(f"{Colors.BOLD}Opções:{Colors.RESET}")
        print(f"  {Colors.BOLD}[1]{Colors.RESET} Adicionar novo destinatário")
        print(f"  {Colors.BOLD}[2]{Colors.RESET} Remover destinatário")
        print(f"  {Colors.BOLD}[3]{Colors.RESET} Limpar todos os destinatários")
        print(f"  {Colors.BOLD}[0]{Colors.RESET} Voltar")
        print()
        
        choice = self.menu.get_user_choice("Escolha uma opção", "0", ["0", "1", "2", "3"])
        
        if choice == "1":
            new_email = input(f"{Colors.BOLD}Novo email: {Colors.RESET}").strip()
            if new_email and "@" in new_email:
                if new_email not in settings.email_recipients:
                    settings.email_recipients.append(new_email)
                    self._save_settings_with_feedback()
                    print(f"{Colors.GREEN}✅ Email adicionado: {new_email}{Colors.RESET}")
                else:
                    print(f"{Colors.YELLOW}⚠️ Email já existe na lista{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ Email inválido{Colors.RESET}")
        
        elif choice == "2" and settings.email_recipients:
            print(f"\\n{Colors.BOLD}Escolha o email para remover:{Colors.RESET}")
            for i, email in enumerate(settings.email_recipients, 1):
                print(f"  {Colors.BOLD}[{i}]{Colors.RESET} {email}")
            
            try:
                idx = int(input(f"\\n{Colors.BOLD}Número do email: {Colors.RESET}").strip()) - 1
                if 0 <= idx < len(settings.email_recipients):
                    removed_email = settings.email_recipients.pop(idx)
                    self._save_settings_with_feedback()
                    print(f"{Colors.GREEN}✅ Email removido: {removed_email}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}❌ Número inválido{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}❌ Digite um número válido{Colors.RESET}")
        
        elif choice == "3":
            if self.menu.get_user_bool("Tem certeza que deseja remover todos os destinatários?", False):
                settings.email_recipients.clear()
                self._save_settings_with_feedback()
                print(f"{Colors.GREEN}✅ Todos os destinatários foram removidos{Colors.RESET}")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_browser_settings(self):
        """Gerencia configurações do navegador"""
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            print(f"{Colors.BOLD}{Colors.BLUE}🌐 CONFIGURAÇÕES DO NAVEGADOR ATUAIS{Colors.RESET}")
            print()
            
            settings = self.settings_manager.settings.browser
            
            # Configurações básicas
            print(f"{Colors.DIM}┌─ Configurações Básicas ─────────────────────────────────────────────────────┐{Colors.RESET}")
            headless_text = f"{Colors.GREEN}✅ Ativado{Colors.RESET}" if settings.headless else f"{Colors.RED}❌ Desativado{Colors.RESET}"
            user_agent_display = settings.user_agent if settings.user_agent else "Padrão do navegador"
            if len(user_agent_display) > 40:
                user_agent_display = user_agent_display[:37] + "..."
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[1]{Colors.RESET} 👁️  Modo Headless           │ {headless_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[2]{Colors.RESET} 🤖 User Agent             │ {Colors.CYAN}{user_agent_display:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Configurações de tela
            print(f"{Colors.DIM}┌─ Configurações de Viewport ─────────────────────────────────────────────────┐{Colors.RESET}")
            viewport_text = f"{settings.viewport_width}x{settings.viewport_height}"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[3]{Colors.RESET} 📐 Largura da Tela        │ {Colors.YELLOW}{settings.viewport_width} pixels{Colors.RESET}{' ' * max(0, 35-len(str(settings.viewport_width)))} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[4]{Colors.RESET} 📏 Altura da Tela         │ {Colors.YELLOW}{settings.viewport_height} pixels{Colors.RESET}{' ' * max(0, 35-len(str(settings.viewport_height)))} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Otimizações
            print(f"{Colors.DIM}┌─ Otimizações de Performance ───────────────────────────────────────────────┐{Colors.RESET}")
            images_text = f"{Colors.RED}❌ Desabilitadas{Colors.RESET}" if settings.disable_images else f"{Colors.GREEN}✅ Habilitadas{Colors.RESET}"
            js_text = f"{Colors.RED}❌ Desabilitado{Colors.RESET}" if settings.disable_javascript else f"{Colors.GREEN}✅ Habilitado{Colors.RESET}"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[5]{Colors.RESET} 🖼️  Carregar Imagens        │ {images_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[6]{Colors.RESET} ⚙️  JavaScript             │ {js_text:<55} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Argumentos customizados
            print(f"{Colors.DIM}┌─ Argumentos Customizados ───────────────────────────────────────────────────┐{Colors.RESET}")
            args_count = len(settings.custom_args) if settings.custom_args else 0
            args_text = f"{args_count} argumento(s) configurado(s)"
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[7]{Colors.RESET} 🔧 Argumentos do Chrome   │ {Colors.YELLOW}{args_text:<45}{Colors.RESET} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            choice = self.menu.get_user_choice("Editar configuração (0 para voltar)", "0", 
                                             ["0", "1", "2", "3", "4", "5", "6", "7"])
            
            if choice == "0":
                break
            elif choice == "1":
                settings.headless = not settings.headless
                self._save_settings_with_feedback()
            elif choice == "2":
                new_ua = input(f"{Colors.BOLD}User Agent (deixe vazio para padrão): {Colors.RESET}").strip()
                settings.user_agent = new_ua
                self._save_settings_with_feedback()
            elif choice == "3":
                new_width = self.menu.get_user_number("Largura da tela (pixels)", settings.viewport_width, 800, 4096)
                settings.viewport_width = new_width
                self._save_settings_with_feedback()
            elif choice == "4":
                new_height = self.menu.get_user_number("Altura da tela (pixels)", settings.viewport_height, 600, 2160)
                settings.viewport_height = new_height
                self._save_settings_with_feedback()
            elif choice == "5":
                settings.disable_images = not settings.disable_images
                self._save_settings_with_feedback()
            elif choice == "6":
                settings.disable_javascript = not settings.disable_javascript
                self._save_settings_with_feedback()
            elif choice == "7":
                self._configure_browser_args(settings)
    
    def _configure_browser_args(self, settings):
        """Configura argumentos customizados do navegador"""
        self.menu.clear_screen()
        self._print_settings_header()
        
        print(f"{Colors.BOLD}{Colors.BLUE}🔧 CONFIGURAÇÃO DE ARGUMENTOS DO CHROME{Colors.RESET}")
        print()
        
        if settings.custom_args:
            print(f"{Colors.BOLD}Argumentos atuais:{Colors.RESET}")
            for i, arg in enumerate(settings.custom_args, 1):
                print(f"  {i}. {Colors.CYAN}{arg}{Colors.RESET}")
            print()
        
        print(f"{Colors.BOLD}Opções:{Colors.RESET}")
        print(f"  {Colors.BOLD}[1]{Colors.RESET} Adicionar novo argumento")
        print(f"  {Colors.BOLD}[2]{Colors.RESET} Remover argumento")
        print(f"  {Colors.BOLD}[3]{Colors.RESET} Resetar para padrão")
        print(f"  {Colors.BOLD}[0]{Colors.RESET} Voltar")
        print()
        
        choice = self.menu.get_user_choice("Escolha uma opção", "0", ["0", "1", "2", "3"])
        
        if choice == "1":
            new_arg = input(f"{Colors.BOLD}Novo argumento (ex: --disable-gpu): {Colors.RESET}").strip()
            if new_arg and new_arg not in settings.custom_args:
                settings.custom_args.append(new_arg)
                self._save_settings_with_feedback()
                print(f"{Colors.GREEN}✅ Argumento adicionado: {new_arg}{Colors.RESET}")
            elif new_arg in settings.custom_args:
                print(f"{Colors.YELLOW}⚠️ Argumento já existe na lista{Colors.RESET}")
        
        elif choice == "2" and settings.custom_args:
            print(f"\\n{Colors.BOLD}Escolha o argumento para remover:{Colors.RESET}")
            for i, arg in enumerate(settings.custom_args, 1):
                print(f"  {Colors.BOLD}[{i}]{Colors.RESET} {arg}")
            
            try:
                idx = int(input(f"\\n{Colors.BOLD}Número do argumento: {Colors.RESET}").strip()) - 1
                if 0 <= idx < len(settings.custom_args):
                    removed_arg = settings.custom_args.pop(idx)
                    self._save_settings_with_feedback()
                    print(f"{Colors.GREEN}✅ Argumento removido: {removed_arg}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}❌ Número inválido{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}❌ Digite um número válido{Colors.RESET}")
        
        elif choice == "3":
            if self.menu.get_user_bool("Resetar argumentos para padrão?", False):
                settings.custom_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--no-sandbox"
                ]
                self._save_settings_with_feedback()
                print(f"{Colors.GREEN}✅ Argumentos resetados para padrão{Colors.RESET}")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_profile_management(self):
        """Gerencia perfis de configuração"""
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            print(f"{Colors.BOLD}{Colors.PURPLE}👤 GERENCIAMENTO DE PERFIS{Colors.RESET}")
            print()
            
            current_profile = self.settings_manager.settings.profile_name
            profile_info = self.settings_manager.get_current_profile_info()
            
            # Informações do perfil atual
            print(f"{Colors.DIM}┌─ Perfil Atual ──────────────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}📋 Nome:{Colors.RESET} {Colors.CYAN}{current_profile:<25}{Colors.RESET} │ {Colors.BOLD}📅 Criado:{Colors.RESET} {profile_info.get('created_at', 'N/A')[:10]:<15} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}📁 Arquivo:{Colors.RESET} {Colors.GRAY}{profile_info['config_file'][-35:] if len(profile_info['config_file']) > 35 else profile_info['config_file']:<20}{Colors.RESET} │ {Colors.BOLD}🔄 Atualizado:{Colors.RESET} {profile_info.get('updated_at', 'N/A')[:10]:<10} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
            # Lista de perfis disponíveis
            available_profiles = self._get_available_profiles()
            
            if len(available_profiles) > 1:
                print(f"{Colors.BOLD}📂 Perfis Disponíveis:{Colors.RESET}")
                print()
                for i, profile_name in enumerate(available_profiles, 1):
                    status = f" {Colors.GREEN}← ATUAL{Colors.RESET}" if profile_name == current_profile else ""
                    print(f"  {i}. {Colors.CYAN}{profile_name}{Colors.RESET}{status}")
                print()
            
            # Menu de opções
            print(f"{Colors.BOLD}Opções disponíveis:{Colors.RESET}")
            print()
            print(f"  {Colors.BOLD}[1]{Colors.RESET} 📋 Listar todos os perfis")
            print(f"  {Colors.BOLD}[2]{Colors.RESET} ➕ Criar novo perfil")
            print(f"  {Colors.BOLD}[3]{Colors.RESET} 🔄 Alternar perfil")
            print(f"  {Colors.BOLD}[4]{Colors.RESET} 📝 Renomear perfil atual")
            print(f"  {Colors.BOLD}[5]{Colors.RESET} 📄 Duplicar perfil atual")
            print(f"  {Colors.BOLD}[6]{Colors.RESET} 🗑️ Excluir perfil")
            print(f"  {Colors.BOLD}[0]{Colors.RESET} ⬅️ Voltar")
            print()
            
            choice = self.menu.get_user_choice("Escolha uma opção", "0", 
                                             ["0", "1", "2", "3", "4", "5", "6"])
            
            if choice == "0":
                break
            elif choice == "1":
                self._list_all_profiles()
            elif choice == "2":
                self._create_new_profile()
            elif choice == "3":
                self._switch_profile()
            elif choice == "4":
                self._rename_current_profile()
            elif choice == "5":
                self._duplicate_current_profile()
            elif choice == "6":
                self._delete_profile()
    
    def _get_available_profiles(self):
        """Retorna lista de perfis disponíveis"""
        config_dir = Path("config")
        if not config_dir.exists():
            return ["default"]
        
        profiles = []
        for config_file in config_dir.glob("*_settings.json"):
            profile_name = config_file.stem.replace("_settings", "")
            if profile_name == "system":
                profile_name = "default"
            profiles.append(profile_name)
        
        # Adicionar 'default' se não existir
        if "default" not in profiles:
            profiles.append("default")
        
        return sorted(profiles)
    
    def _list_all_profiles(self):
        """Lista detalhadamente todos os perfis"""
        self.menu.clear_screen()
        self._print_settings_header()
        
        print(f"{Colors.BOLD}{Colors.PURPLE}📋 LISTA COMPLETA DE PERFIS{Colors.RESET}")
        print()
        
        profiles = self._get_available_profiles()
        current_profile = self.settings_manager.settings.profile_name
        
        for i, profile_name in enumerate(profiles, 1):
            # Tentar carregar informações do perfil
            config_file = f"config/{profile_name if profile_name != 'default' else 'system'}_settings.json"
            
            status_icon = f"{Colors.GREEN}🟢{Colors.RESET}" if profile_name == current_profile else f"{Colors.GRAY}⚪{Colors.RESET}"
            
            print(f"{status_icon} {Colors.BOLD}{i}. {profile_name.upper()}{Colors.RESET}")
            
            if os.path.exists(config_file):
                try:
                    import json
                    with open(config_file, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                    
                    created_at = profile_data.get('created_at', 'N/A')[:19].replace('T', ' ')
                    updated_at = profile_data.get('updated_at', 'N/A')[:19].replace('T', ' ')
                    version = profile_data.get('version', 'N/A')
                    
                    print(f"     📁 Arquivo: {config_file}")
                    print(f"     📅 Criado: {created_at}")
                    print(f"     🔄 Atualizado: {updated_at}")
                    print(f"     🏷️ Versão: {version}")
                    
                except Exception as e:
                    print(f"     {Colors.RED}❌ Erro ao carregar: {e}{Colors.RESET}")
            else:
                print(f"     {Colors.YELLOW}⚠️ Arquivo não encontrado{Colors.RESET}")
            
            print()
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _create_new_profile(self):
        """Cria um novo perfil"""
        profile_name = input(f"{Colors.BOLD}Nome do novo perfil: {Colors.RESET}").strip()
        
        if not profile_name:
            print(f"{Colors.RED}❌ Nome não pode estar vazio{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Verificar se já existe
        if profile_name in self._get_available_profiles():
            print(f"{Colors.RED}❌ Perfil '{profile_name}' já existe{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Perguntar se deve copiar configurações atuais
        copy_current = self.menu.get_user_bool("Copiar configurações do perfil atual?", True)
        
        try:
            if copy_current:
                # Copiar configurações atuais
                new_settings = self.settings_manager.settings.copy()
                new_settings.profile_name = profile_name
            else:
                # Criar com configurações padrão
                from .settings_manager import SystemSettings
                new_settings = SystemSettings()
                new_settings.profile_name = profile_name
            
            # Salvar novo perfil
            config_file = f"config/{profile_name}_settings.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(new_settings.to_dict(), f, indent=2, ensure_ascii=False)
            
            print(f"{Colors.GREEN}✅ Perfil '{profile_name}' criado com sucesso!{Colors.RESET}")
            
            # Perguntar se deve alternar para o novo perfil
            if self.menu.get_user_bool("Alternar para o novo perfil agora?", True):
                self._switch_to_profile(profile_name)
                
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao criar perfil: {e}{Colors.RESET}")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _switch_profile(self):
        """Alterna para outro perfil"""
        profiles = self._get_available_profiles()
        current_profile = self.settings_manager.settings.profile_name
        
        # Remover perfil atual da lista
        other_profiles = [p for p in profiles if p != current_profile]
        
        if not other_profiles:
            print(f"{Colors.YELLOW}⚠️ Não há outros perfis disponíveis{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        print(f"\\n{Colors.BOLD}Perfis disponíveis:{Colors.RESET}")
        for i, profile_name in enumerate(other_profiles, 1):
            print(f"  {Colors.BOLD}[{i}]{Colors.RESET} {profile_name}")
        
        try:
            choice = int(input(f"\\n{Colors.BOLD}Escolha o perfil (0 para cancelar): {Colors.RESET}").strip())
            if choice == 0:
                return
            
            if 1 <= choice <= len(other_profiles):
                selected_profile = other_profiles[choice - 1]
                self._switch_to_profile(selected_profile)
            else:
                print(f"{Colors.RED}❌ Opção inválida{Colors.RESET}")
                
        except ValueError:
            print(f"{Colors.RED}❌ Digite um número válido{Colors.RESET}")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _switch_to_profile(self, profile_name):
        """Alterna para um perfil específico"""
        try:
            # Recarregar configurações com o novo perfil
            old_profile = self.settings_manager.settings.profile_name
            
            # Atualizar o nome do arquivo de configuração
            if profile_name == "default":
                config_file = "config/system_settings.json"
            else:
                config_file = f"config/{profile_name}_settings.json"
            
            if os.path.exists(config_file):
                self.settings_manager.config_file = Path(config_file)
                self.settings_manager.load_settings()
                print(f"{Colors.GREEN}✅ Alternado para perfil '{profile_name}'{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ Arquivo de perfil não encontrado: {config_file}{Colors.RESET}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao alternar perfil: {e}{Colors.RESET}")
    
    def _rename_current_profile(self):
        """Renomeia o perfil atual"""
        current_profile = self.settings_manager.settings.profile_name
        
        if current_profile == "default":
            print(f"{Colors.YELLOW}⚠️ O perfil 'default' não pode ser renomeado{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        new_name = input(f"{Colors.BOLD}Novo nome para '{current_profile}': {Colors.RESET}").strip()
        
        if not new_name or new_name == current_profile:
            print(f"{Colors.YELLOW}⚠️ Operação cancelada{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        if new_name in self._get_available_profiles():
            print(f"{Colors.RED}❌ Já existe um perfil com nome '{new_name}'{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        try:
            # Renomear arquivo
            old_file = f"config/{current_profile}_settings.json"
            new_file = f"config/{new_name}_settings.json"
            
            if os.path.exists(old_file):
                # Atualizar o nome no arquivo
                self.settings_manager.settings.profile_name = new_name
                self.settings_manager.save_settings()
                
                # Renomear arquivo
                os.rename(old_file, new_file)
                
                # Atualizar referência no settings manager
                self.settings_manager.config_file = Path(new_file)
                
                print(f"{Colors.GREEN}✅ Perfil renomeado de '{current_profile}' para '{new_name}'{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ Arquivo do perfil não encontrado{Colors.RESET}")
                
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao renomear perfil: {e}{Colors.RESET}")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _duplicate_current_profile(self):
        """Duplica o perfil atual"""
        current_profile = self.settings_manager.settings.profile_name
        new_name = input(f"{Colors.BOLD}Nome para a cópia de '{current_profile}': {Colors.RESET}").strip()
        
        if not new_name:
            print(f"{Colors.YELLOW}⚠️ Operação cancelada{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        if new_name in self._get_available_profiles():
            print(f"{Colors.RED}❌ Já existe um perfil com nome '{new_name}'{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        try:
            # Copiar configurações atuais
            new_settings = self.settings_manager.settings.copy()
            new_settings.profile_name = new_name
            
            # Salvar cópia
            config_file = f"config/{new_name}_settings.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(new_settings.to_dict(), f, indent=2, ensure_ascii=False)
            
            print(f"{Colors.GREEN}✅ Perfil '{current_profile}' duplicado como '{new_name}'{Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao duplicar perfil: {e}{Colors.RESET}")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _delete_profile(self):
        """Exclui um perfil"""
        profiles = self._get_available_profiles()
        current_profile = self.settings_manager.settings.profile_name
        
        # Não permitir excluir o perfil atual se for o único
        if len(profiles) <= 1:
            print(f"{Colors.YELLOW}⚠️ Não é possível excluir o único perfil disponível{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        # Mostrar perfis disponíveis para exclusão
        deletable_profiles = [p for p in profiles if p != "default"]  # Não permitir excluir default
        
        if not deletable_profiles:
            print(f"{Colors.YELLOW}⚠️ Não há perfis que possam ser excluídos{Colors.RESET}")
            input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            return
        
        print(f"\\n{Colors.BOLD}Perfis disponíveis para exclusão:{Colors.RESET}")
        for i, profile_name in enumerate(deletable_profiles, 1):
            status = f" {Colors.RED}(ATUAL - será alternado){Colors.RESET}" if profile_name == current_profile else ""
            print(f"  {Colors.BOLD}[{i}]{Colors.RESET} {profile_name}{status}")
        
        try:
            choice = int(input(f"\\n{Colors.BOLD}Escolha o perfil para excluir (0 para cancelar): {Colors.RESET}").strip())
            if choice == 0:
                return
            
            if 1 <= choice <= len(deletable_profiles):
                profile_to_delete = deletable_profiles[choice - 1]
                
                # Confirmação
                if not self.menu.get_user_bool(f"Tem certeza que deseja excluir o perfil '{profile_to_delete}'?", False):
                    print(f"{Colors.YELLOW}⚠️ Exclusão cancelada{Colors.RESET}")
                    input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
                    return
                
                # Se for o perfil atual, alternar para default primeiro
                if profile_to_delete == current_profile:
                    print(f"{Colors.BLUE}🔄 Alternando para perfil 'default'...{Colors.RESET}")
                    self._switch_to_profile("default")
                
                # Excluir arquivo
                config_file = f"config/{profile_to_delete}_settings.json"
                if os.path.exists(config_file):
                    os.remove(config_file)
                    print(f"{Colors.GREEN}✅ Perfil '{profile_to_delete}' excluído com sucesso{Colors.RESET}")
                else:
                    print(f"{Colors.YELLOW}⚠️ Arquivo do perfil não encontrado{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ Opção inválida{Colors.RESET}")
                
        except ValueError:
            print(f"{Colors.RED}❌ Digite um número válido{Colors.RESET}")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_import_export(self):
        """Gerencia import/export de configurações"""
        while True:
            self.menu.clear_screen()
            self._print_settings_header()
            
            print(f"{Colors.BOLD}{Colors.PURPLE}📤 IMPORT/EXPORT DE CONFIGURAÇÕES{Colors.RESET}")
            print()
            
            options = [
                ("1", "📤", "EXPORTAR", "Salvar configurações em arquivo"),
                ("2", "📥", "IMPORTAR", "Carregar configurações de arquivo"),
                ("3", "💾", "BACKUP MANUAL", "Criar backup das configurações atuais"),
                ("4", "📋", "LISTAR BACKUPS", "Ver backups disponíveis"),
                ("0", "⬅️", "VOLTAR", "Retornar ao menu anterior")
            ]
            
            for key, icon, title, desc in options:
                color = Colors.GREEN if key != "0" else Colors.GRAY
                print(f"  {Colors.BOLD}{color}[{key}]{Colors.RESET} {icon} {Colors.BOLD}{title:<15}{Colors.RESET} {Colors.DIM}{desc}{Colors.RESET}")
            
            print()
            choice = self.menu.get_user_choice("Escolha uma opção", "0", ["0", "1", "2", "3", "4"])
            
            if choice == "0":
                break
            elif choice == "1":
                self._handle_export_settings()
            elif choice == "2":
                self._handle_import_settings()
            elif choice == "3":
                self._handle_manual_backup()
            elif choice == "4":
                self._handle_list_backups()
    
    def _handle_export_settings(self):
        """Exporta configurações"""
        default_filename = f"catho_settings_{self.settings_manager.settings.profile_name}.json"
        filename = input(f"{Colors.BOLD}Nome do arquivo [{default_filename}]: {Colors.RESET}").strip()
        if not filename:
            filename = default_filename
        
        if self.settings_manager.export_settings(filename):
            self.menu.print_success_message(f"Configurações exportadas: {filename}")
        else:
            self.menu.print_error_message("Erro ao exportar configurações")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_import_settings(self):
        """Importa configurações"""
        filename = input(f"{Colors.BOLD}Nome do arquivo para importar: {Colors.RESET}").strip()
        if filename and os.path.exists(filename):
            if self.settings_manager.import_settings(filename):
                self.menu.print_success_message(f"Configurações importadas: {filename}")
            else:
                self.menu.print_error_message("Erro ao importar configurações")
        else:
            self.menu.print_error_message("Arquivo não encontrado")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_manual_backup(self):
        """Cria backup manual"""
        backup_file = self.settings_manager._create_backup()
        if backup_file:
            self.menu.print_success_message(f"Backup criado: {backup_file}")
        else:
            self.menu.print_error_message("Erro ao criar backup")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_list_backups(self):
        """Lista backups disponíveis"""
        backup_files = list(self.settings_manager.backup_dir.glob("*.json"))
        
        if backup_files:
            print(f"{Colors.BOLD}📋 Backups Disponíveis:{Colors.RESET}")
            print()
            
            # Ordenar por data
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for i, backup_file in enumerate(backup_files[:10], 1):
                mtime = backup_file.stat().st_mtime
                date_str = self._format_timestamp(mtime)
                size_kb = backup_file.stat().st_size // 1024
                
                print(f"  {i:2d}. {Colors.CYAN}{backup_file.name}{Colors.RESET}")
                print(f"      📅 {date_str} | 📦 {size_kb}KB")
                print()
        else:
            self.menu.print_info_message("Nenhum backup encontrado")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_reset_defaults(self):
        """Reset para configurações padrão"""
        self.menu.print_warning_message("ATENÇÃO: Isso irá resetar TODAS as configurações para os valores padrão!")
        
        if self.menu.get_user_bool("Tem certeza que deseja continuar?", False):
            if self.settings_manager.reset_to_defaults():
                self.menu.print_success_message("Configurações resetadas para padrão")
            else:
                self.menu.print_error_message("Erro ao resetar configurações")
        else:
            self.menu.print_info_message("Reset cancelado")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _handle_validate_settings(self):
        """Valida configurações atuais"""
        errors = self.settings_manager.validate_settings()
        
        if errors:
            self.menu.print_error_message(f"Encontrados {len(errors)} erro(s) de configuração:")
            print()
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {Colors.RED}{error}{Colors.RESET}")
        else:
            self.menu.print_success_message("Todas as configurações são válidas!")
            
            # Mostrar resumo
            print()
            print(f"{Colors.BOLD}📊 Resumo das Configurações:{Colors.RESET}")
            settings = self.settings_manager.settings
            print(f"  • Scraping: {settings.scraping.max_concurrent_jobs} jobs, {settings.scraping.max_pages} páginas")
            print(f"  • Cache: {settings.cache.max_age_hours}h, {settings.cache.max_cache_size_mb}MB")
            print(f"  • Performance: {settings.performance.page_load_timeout}ms timeout")
            print(f"  • Features: {'Incremental' if settings.scraping.enable_incremental else 'Completo'}, {'Dedup' if settings.scraping.enable_deduplication else 'No-Dedup'}")
        
        input(f"\\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _save_settings_with_feedback(self):
        """Salva configurações com feedback visual"""
        if self.settings_manager.save_settings():
            print(f"{Colors.GREEN}✅ Configuração salva!{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ Erro ao salvar!{Colors.RESET}")
        
        # Pequena pausa para mostrar feedback
        import time
        time.sleep(0.5)
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Formata timestamp para exibição"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


# Instância global da UI
settings_ui = SettingsUI()