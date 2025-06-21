"""
Sistema de Gerenciamento de Configurações Avançadas
==================================================

Este módulo gerencia todas as configurações do sistema, permitindo:
- Carregamento e salvamento de configurações
- Validação automática de valores
- Interface visual para modificação
- Backup e restauração
- Configurações por perfil
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict, field
import copy

from ..utils.menu_system import Colors


@dataclass
class ScrapingConfig:
    """Configurações de scraping"""
    # URLs para diversidade geográfica, modalidades e áreas profissionais
    base_urls: List[str] = field(default_factory=lambda: [
        # === MODALIDADES ===
        "https://www.catho.com.br/vagas/home-office/",           # Home office
        "https://www.catho.com.br/vagas/presencial/",            # Presencial
        "https://www.catho.com.br/vagas/hibrido/",               # Híbrido
        
        # === GEOGRAFIA ===
        "https://www.catho.com.br/vagas/",                       # Todas as vagas
        "https://www.catho.com.br/vagas/sao-paulo-sp/",          # São Paulo
        "https://www.catho.com.br/vagas/rio-de-janeiro-rj/",     # Rio de Janeiro
        "https://www.catho.com.br/vagas/belo-horizonte-mg/",     # Belo Horizonte
        "https://www.catho.com.br/vagas/brasilia-df/",           # Brasília
        "https://www.catho.com.br/vagas/curitiba-pr/",           # Curitiba
        "https://www.catho.com.br/vagas/porto-alegre-rs/",       # Porto Alegre
        "https://www.catho.com.br/vagas/recife-pe/",             # Recife
        "https://www.catho.com.br/vagas/salvador-ba/",           # Salvador
        
        # === ÁREAS PROFISSIONAIS ===
        "https://www.catho.com.br/vagas/tecnologia-da-informacao/",    # TI
        "https://www.catho.com.br/vagas/administracao/",               # Administração
        "https://www.catho.com.br/vagas/vendas/",                      # Vendas
        "https://www.catho.com.br/vagas/marketing/",                   # Marketing
        "https://www.catho.com.br/vagas/financas/",                    # Finanças
        "https://www.catho.com.br/vagas/recursos-humanos/",            # RH
        "https://www.catho.com.br/vagas/engenharia/",                  # Engenharia
        "https://www.catho.com.br/vagas/saude/",                       # Saúde
        "https://www.catho.com.br/vagas/educacao/",                    # Educação
        "https://www.catho.com.br/vagas/juridico/",                    # Jurídico
        
        # === NÍVEIS DE SENIORIDADE ===
        "https://www.catho.com.br/vagas/estagio/",                     # Estágio
        "https://www.catho.com.br/vagas/trainee/",                     # Trainee
        "https://www.catho.com.br/vagas/junior/",                      # Júnior
        "https://www.catho.com.br/vagas/pleno/",                       # Pleno
        "https://www.catho.com.br/vagas/senior/",                      # Sênior
        "https://www.catho.com.br/vagas/especialista/",                # Especialista
        "https://www.catho.com.br/vagas/coordenador/",                 # Coordenador
        "https://www.catho.com.br/vagas/gerente/",                     # Gerente
        "https://www.catho.com.br/vagas/diretor/"                      # Diretor
    ])
    
    # Configuração de diversidade
    diversity_mode: str = "balanced"  # Modos: "balanced", "geographic", "remote_only", "professional", "seniority", "complete", "custom"
    urls_per_session: int = 3  # Quantas URLs usar por sessão
    enable_url_rotation: bool = True
    
    # URLs ativas (selecionadas da lista base_urls)
    active_urls: List[str] = field(default_factory=lambda: ["https://www.catho.com.br/vagas/home-office/"])
    
    # Configurações existentes
    max_concurrent_jobs: int = 3
    max_pages: int = 5
    requests_per_second: float = 1.5
    burst_limit: int = 3
    enable_incremental: bool = True
    enable_deduplication: bool = True
    compression_level: int = 6


@dataclass
class CacheConfig:
    """Configurações de cache"""
    cache_dir: str = "data/cache"
    max_age_hours: int = 6
    auto_cleanup: bool = True
    max_cache_size_mb: int = 500
    rebuild_index_on_startup: bool = True


@dataclass
class PerformanceConfig:
    """Configurações de performance"""
    page_load_timeout: int = 60000
    network_idle_timeout: int = 30000
    element_wait_timeout: int = 3000
    retry_attempts: int = 3
    retry_delay: float = 1.0
    pool_min_size: int = 2
    pool_max_size: int = 10


@dataclass
class OutputConfig:
    """Configurações de saída"""
    results_dir: str = "data/resultados"
    max_files_per_type: int = 5
    auto_cleanup_results: bool = False
    export_formats: List[str] = field(default_factory=lambda: ["json", "csv", "txt"])
    generate_reports: bool = True


@dataclass
class LoggingConfig:
    """Configurações de logging"""
    log_level: str = "INFO"
    log_dir: str = "logs"
    max_log_files: int = 10
    max_log_size_mb: int = 10
    enable_debug_logs: bool = False
    enable_performance_logs: bool = True


@dataclass
class AlertConfig:
    """Configurações de alertas"""
    enable_console_alerts: bool = True
    enable_file_alerts: bool = True
    enable_email_alerts: bool = False
    email_smtp_server: str = ""
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = field(default_factory=list)
    webhook_url: str = ""


@dataclass
class BrowserConfig:
    """Configurações do navegador"""
    headless: bool = True
    user_agent: str = ""
    viewport_width: int = 1920
    viewport_height: int = 1080
    disable_images: bool = False
    disable_javascript: bool = False
    custom_args: List[str] = field(default_factory=lambda: [
        '--disable-blink-features=AutomationControlled',
        '--disable-web-security',
        '--no-sandbox'
    ])


@dataclass
class SystemSettings:
    """Configurações completas do sistema"""
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    
    # Metadados
    version: str = "4.0.0"
    created_at: str = ""
    updated_at: str = ""
    profile_name: str = "default"


class SettingsManager:
    """
    Gerenciador central de configurações do sistema
    
    Funcionalidades:
    - Carregamento automático de configurações
    - Validação de valores
    - Salvamento com backup
    - Múltiplos perfis
    - Interface visual
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "system_settings.json"
        self.backup_dir = self.config_dir / "backups"
        
        # Criar diretórios se não existirem
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configurações atuais
        self.settings: SystemSettings = SystemSettings()
        
        # Carregar configurações existentes
        self.load_settings()
    
    def load_settings(self) -> bool:
        """
        Carrega configurações do arquivo
        
        Returns:
            bool: True se carregou com sucesso, False se usou padrão
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Converter dicionário para dataclass
                self.settings = self._dict_to_settings(data)
                print(f"{Colors.GREEN}✅ Configurações carregadas: {self.config_file}{Colors.RESET}")
                return True
            else:
                print(f"{Colors.YELLOW}⚠️ Arquivo de configuração não encontrado, usando padrões{Colors.RESET}")
                self._create_default_settings()
                return False
                
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao carregar configurações: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}📋 Usando configurações padrão{Colors.RESET}")
            self._create_default_settings()
            return False
    
    def save_settings(self, create_backup: bool = True) -> bool:
        """
        Salva configurações no arquivo
        
        Args:
            create_backup: Se deve criar backup antes de salvar
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            # Criar backup se solicitado
            if create_backup and self.config_file.exists():
                self._create_backup()
            
            # Atualizar timestamp
            self.settings.updated_at = datetime.now().isoformat()
            
            # Converter para dicionário
            data = self._settings_to_dict(self.settings)
            
            # Salvar arquivo
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"{Colors.GREEN}✅ Configurações salvas: {self.config_file}{Colors.RESET}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao salvar configurações: {e}{Colors.RESET}")
            return False
    
    def _create_backup(self) -> str:
        """Cria backup das configurações atuais"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"settings_backup_{timestamp}.json"
        
        try:
            shutil.copy2(self.config_file, backup_file)
            print(f"{Colors.CYAN}💾 Backup criado: {backup_file.name}{Colors.RESET}")
            
            # Manter apenas os 10 backups mais recentes
            self._cleanup_old_backups()
            
            return str(backup_file)
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Erro ao criar backup: {e}{Colors.RESET}")
            return ""
    
    def _cleanup_old_backups(self, max_backups: int = 10):
        """Remove backups antigos mantendo apenas os mais recentes"""
        try:
            backup_files = list(self.backup_dir.glob("settings_backup_*.json"))
            if len(backup_files) > max_backups:
                # Ordenar por data de modificação
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Remover os mais antigos
                for old_backup in backup_files[max_backups:]:
                    old_backup.unlink()
                    print(f"{Colors.DIM}🗑️ Backup antigo removido: {old_backup.name}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Erro na limpeza de backups: {e}{Colors.RESET}")
    
    def _create_default_settings(self):
        """Cria configurações padrão"""
        self.settings = SystemSettings()
        self.settings.created_at = datetime.now().isoformat()
        self.settings.updated_at = self.settings.created_at
        
        # Salvar configurações padrão
        self.save_settings(create_backup=False)
    
    def _dict_to_settings(self, data: Dict[str, Any]) -> SystemSettings:
        """Converte dicionário para SystemSettings"""
        settings = SystemSettings()
        
        # Mapear cada seção com compatibilidade para versões antigas
        if 'scraping' in data:
            scraping_data = data['scraping'].copy()
            
            # Converter campo antigo base_url para novo formato
            if 'base_url' in scraping_data and 'base_urls' not in scraping_data:
                old_url = scraping_data.pop('base_url')
                scraping_data['active_urls'] = [old_url]
            
            settings.scraping = ScrapingConfig(**scraping_data)
        if 'cache' in data:
            settings.cache = CacheConfig(**data['cache'])
        if 'performance' in data:
            settings.performance = PerformanceConfig(**data['performance'])
        if 'output' in data:
            settings.output = OutputConfig(**data['output'])
        if 'logging' in data:
            settings.logging = LoggingConfig(**data['logging'])
        if 'alerts' in data:
            settings.alerts = AlertConfig(**data['alerts'])
        if 'browser' in data:
            settings.browser = BrowserConfig(**data['browser'])
        
        # Metadados
        settings.version = data.get('version', '4.0.0')
        settings.created_at = data.get('created_at', '')
        settings.updated_at = data.get('updated_at', '')
        settings.profile_name = data.get('profile_name', 'default')
        
        return settings
    
    def _settings_to_dict(self, settings: SystemSettings) -> Dict[str, Any]:
        """Converte SystemSettings para dicionário"""
        return {
            'scraping': asdict(settings.scraping),
            'cache': asdict(settings.cache),
            'performance': asdict(settings.performance),
            'output': asdict(settings.output),
            'logging': asdict(settings.logging),
            'alerts': asdict(settings.alerts),
            'browser': asdict(settings.browser),
            'version': settings.version,
            'created_at': settings.created_at,
            'updated_at': settings.updated_at,
            'profile_name': settings.profile_name
        }
    
    def validate_settings(self) -> List[str]:
        """
        Valida as configurações atuais
        
        Returns:
            List[str]: Lista de erros encontrados (vazia se tudo OK)
        """
        errors = []
        
        # Validar scraping
        if self.settings.scraping.max_concurrent_jobs < 1 or self.settings.scraping.max_concurrent_jobs > 10:
            errors.append("max_concurrent_jobs deve estar entre 1 e 10")
        
        if self.settings.scraping.max_pages < 1 or self.settings.scraping.max_pages > 100:
            errors.append("max_pages deve estar entre 1 e 100")
        
        if self.settings.scraping.requests_per_second < 0.1 or self.settings.scraping.requests_per_second > 10:
            errors.append("requests_per_second deve estar entre 0.1 e 10")
        
        # Validar cache
        if self.settings.cache.max_age_hours < 1 or self.settings.cache.max_age_hours > 168:  # 7 dias
            errors.append("cache max_age_hours deve estar entre 1 e 168")
        
        if self.settings.cache.max_cache_size_mb < 10 or self.settings.cache.max_cache_size_mb > 5000:
            errors.append("max_cache_size_mb deve estar entre 10 e 5000")
        
        # Validar performance
        if self.settings.performance.page_load_timeout < 5000 or self.settings.performance.page_load_timeout > 300000:
            errors.append("page_load_timeout deve estar entre 5000 e 300000ms")
        
        # Validar diretórios
        directories = [
            self.settings.cache.cache_dir,
            self.settings.output.results_dir,
            self.settings.logging.log_dir
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Erro ao validar diretório {directory}: {e}")
        
        return errors
    
    def get_current_profile_info(self) -> Dict[str, Any]:
        """Retorna informações do perfil atual"""
        return {
            'name': self.settings.profile_name,
            'version': self.settings.version,
            'created_at': self.settings.created_at,
            'updated_at': self.settings.updated_at,
            'config_file': str(self.config_file),
            'has_backups': len(list(self.backup_dir.glob("*.json"))) > 0
        }
    
    def export_settings(self, export_path: str) -> bool:
        """Exporta configurações para arquivo específico"""
        try:
            data = self._settings_to_dict(self.settings)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"{Colors.GREEN}✅ Configurações exportadas: {export_path}{Colors.RESET}")
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao exportar: {e}{Colors.RESET}")
            return False
    
    def import_settings(self, import_path: str) -> bool:
        """Importa configurações de arquivo específico"""
        try:
            # Criar backup antes de importar
            self._create_backup()
            
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar e carregar
            new_settings = self._dict_to_settings(data)
            errors = self.validate_settings()
            
            if errors:
                print(f"{Colors.RED}❌ Configurações inválidas:{Colors.RESET}")
                for error in errors:
                    print(f"  • {error}")
                return False
            
            self.settings = new_settings
            self.save_settings(create_backup=False)
            
            print(f"{Colors.GREEN}✅ Configurações importadas: {import_path}{Colors.RESET}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao importar: {e}{Colors.RESET}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reseta todas as configurações para os valores padrão"""
        try:
            # Criar backup
            self._create_backup()
            
            # Recriar configurações padrão
            self._create_default_settings()
            
            print(f"{Colors.GREEN}✅ Configurações resetadas para padrão{Colors.RESET}")
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao resetar configurações: {e}{Colors.RESET}")
            return False
    
    def get_active_urls(self) -> List[str]:
        """Retorna lista de URLs ativas baseada no modo de diversidade"""
        import random
        
        scraping = self.settings.scraping
        
        if not scraping.enable_url_rotation:
            return scraping.active_urls or [scraping.base_urls[0]]
        
        if scraping.diversity_mode == "remote_only":
            # Apenas URLs remotas/home office
            remote_urls = [url for url in scraping.base_urls 
                          if any(keyword in url for keyword in ["home-office", "remoto"])]
            return random.sample(remote_urls, min(scraping.urls_per_session, len(remote_urls)))
        
        elif scraping.diversity_mode == "geographic":
            # Foco em diversidade geográfica
            geo_urls = [url for url in scraping.base_urls 
                       if any(state in url for state in ["-sp/", "-rj/", "-mg/", "-df/", "-pr/", "-rs/", "-pe/", "-ba/"])]
            # Adicionar URL geral se disponível
            general_url = [url for url in scraping.base_urls if url == "https://www.catho.com.br/vagas/"]
            geo_urls.extend(general_url)
            return random.sample(geo_urls, min(scraping.urls_per_session, len(geo_urls)))
        
        elif scraping.diversity_mode == "professional":
            # Foco em áreas profissionais
            prof_urls = [url for url in scraping.base_urls 
                        if any(area in url for area in ["tecnologia", "administracao", "vendas", "marketing", 
                                                        "financas", "recursos-humanos", "engenharia", 
                                                        "saude", "educacao", "juridico"])]
            return random.sample(prof_urls, min(scraping.urls_per_session, len(prof_urls)))
        
        elif scraping.diversity_mode == "seniority":
            # Foco em níveis de senioridade
            senior_urls = [url for url in scraping.base_urls 
                          if any(level in url for level in ["estagio", "trainee", "junior", "pleno", 
                                                            "senior", "especialista", "coordenador", 
                                                            "gerente", "diretor"])]
            return random.sample(senior_urls, min(scraping.urls_per_session, len(senior_urls)))
        
        elif scraping.diversity_mode == "complete":
            # Mix completo: uma de cada categoria
            selected_urls = []
            
            # Categorias com pesos
            categories = {
                "modalidade": ([url for url in scraping.base_urls 
                               if any(m in url for m in ["home-office", "presencial", "hibrido"])], 1),
                "geografia": ([url for url in scraping.base_urls 
                             if any(g in url for g in ["-sp/", "-rj/", "-mg/", "-df/", "-pr/", "-rs/", "-pe/", "-ba/"])], 1),
                "profissional": ([url for url in scraping.base_urls 
                                if any(p in url for p in ["tecnologia", "administracao", "vendas", "marketing"])], 1),
                "senioridade": ([url for url in scraping.base_urls 
                               if any(s in url for s in ["junior", "pleno", "senior", "coordenador"])], 1)
            }
            
            # Selecionar URLs proporcionalmente
            for category, (urls, weight) in categories.items():
                if urls:
                    num_urls = max(1, int(scraping.urls_per_session * weight / len(categories)))
                    selected = random.sample(urls, min(num_urls, len(urls)))
                    selected_urls.extend(selected)
            
            # Limitar ao número configurado e remover duplicatas
            selected_urls = list(dict.fromkeys(selected_urls))[:scraping.urls_per_session]
            
            # Preencher com URLs aleatórias se necessário
            if len(selected_urls) < scraping.urls_per_session:
                remaining = [url for url in scraping.base_urls if url not in selected_urls]
                if remaining:
                    additional = random.sample(remaining, 
                                             min(scraping.urls_per_session - len(selected_urls), len(remaining)))
                    selected_urls.extend(additional)
            
            return selected_urls
        
        elif scraping.diversity_mode == "balanced":
            # Mix balanceado de modalidades e localizações
            selected_urls = []
            
            # Garantir pelo menos uma URL de cada categoria
            categories = {
                "remote": [url for url in scraping.base_urls 
                          if "home-office" in url or "remoto" in url],
                "presential": [url for url in scraping.base_urls 
                              if "presencial" in url],
                "hybrid": [url for url in scraping.base_urls 
                          if "hibrido" in url],
                "geographic": [url for url in scraping.base_urls 
                              if any(state in url for state in ["-sp/", "-rj/", "-mg/", "-df/"])],
                "general": [url for url in scraping.base_urls 
                           if url == "https://www.catho.com.br/vagas/"]
            }
            
            # Selecionar uma URL de cada categoria disponível
            for category, urls in categories.items():
                if urls and len(selected_urls) < scraping.urls_per_session:
                    selected_urls.append(random.choice(urls))
            
            # Preencher com URLs aleatórias se necessário
            remaining_slots = scraping.urls_per_session - len(selected_urls)
            if remaining_slots > 0:
                available_urls = [url for url in scraping.base_urls if url not in selected_urls]
                if available_urls:
                    additional_urls = random.sample(available_urls, 
                                                   min(remaining_slots, len(available_urls)))
                    selected_urls.extend(additional_urls)
            
            return selected_urls
        
        elif scraping.diversity_mode == "custom":
            # Usar URLs personalizadas
            return scraping.active_urls or [scraping.base_urls[0]]
        
        # Fallback: retornar URLs aleatórias
        return random.sample(scraping.base_urls, 
                           min(scraping.urls_per_session, len(scraping.base_urls)))
    
    def set_diversity_mode(self, mode: str, urls_per_session: int = None) -> bool:
        """
        Define o modo de diversidade de URLs
        
        Args:
            mode: "balanced", "geographic", "remote_only", "professional", "seniority", "complete", "custom"
            urls_per_session: Número de URLs por sessão (opcional)
        """
        valid_modes = ["balanced", "geographic", "remote_only", "professional", "seniority", "complete", "custom"]
        
        if mode not in valid_modes:
            print(f"{Colors.RED}❌ Modo inválido. Use: {', '.join(valid_modes)}{Colors.RESET}")
            return False
        
        self.settings.scraping.diversity_mode = mode
        
        if urls_per_session is not None:
            self.settings.scraping.urls_per_session = urls_per_session
        
        self.save_settings()
        print(f"{Colors.GREEN}✅ Modo de diversidade alterado para: {mode}{Colors.RESET}")
        return True
    
    def add_custom_url(self, url: str) -> bool:
        """Adiciona URL personalizada à lista base"""
        if url not in self.settings.scraping.base_urls:
            self.settings.scraping.base_urls.append(url)
            self.save_settings()
            print(f"{Colors.GREEN}✅ URL adicionada: {url}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️ URL já existe na lista{Colors.RESET}")
            return False
    
    def remove_url(self, url: str) -> bool:
        """Remove URL da lista base"""
        if url in self.settings.scraping.base_urls:
            self.settings.scraping.base_urls.remove(url)
            # Remover também das URLs ativas se existir
            if url in self.settings.scraping.active_urls:
                self.settings.scraping.active_urls.remove(url)
            self.save_settings()
            print(f"{Colors.GREEN}✅ URL removida: {url}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️ URL não encontrada na lista{Colors.RESET}")
            return False
    
    def preview_active_urls(self) -> None:
        """Mostra prévia das URLs que serão usadas na próxima sessão"""
        urls = self.get_active_urls()
        print(f"\n{Colors.CYAN}🎯 URLs que serão usadas na próxima sessão:{Colors.RESET}")
        print(f"{Colors.DIM}Modo: {self.settings.scraping.diversity_mode} | URLs por sessão: {self.settings.scraping.urls_per_session}{Colors.RESET}")
        print()
        
        # Categorizar URLs
        categorias = {"modalidade": [], "geografia": [], "profissional": [], "senioridade": []}
        
        for i, url in enumerate(urls, 1):
            # Extrair descrição e categoria da URL
            desc, categoria = self._categorize_url(url)
            
            print(f"  {Colors.GREEN}{i}.{Colors.RESET} {desc} {Colors.DIM}[{categoria}]{Colors.RESET}")
            print(f"     {Colors.DIM}{url}{Colors.RESET}")
            
            if categoria in categorias:
                categorias[categoria].append(desc)
        
        # Estatísticas de diversidade
        print(f"\n{Colors.YELLOW}📊 Análise de Diversidade:{Colors.RESET}")
        total_categorias = sum(1 for cat, items in categorias.items() if items)
        print(f"  • Categorias cobertas: {total_categorias}/4")
        print(f"  • Estimativa de aumento: +{len(urls) * 200}% vagas")
        
        # Mostrar distribuição
        print(f"\n{Colors.CYAN}📈 Distribuição:{Colors.RESET}")
        for cat, items in categorias.items():
            if items:
                print(f"  • {cat.capitalize()}: {len(items)} URL(s) - {', '.join(items)}")
    
    def _categorize_url(self, url: str) -> Tuple[str, str]:
        """Categoriza uma URL e retorna descrição e categoria"""
        # Modalidades
        if "home-office" in url:
            return ("Home Office", "modalidade")
        elif "presencial" in url:
            return ("Presencial", "modalidade")
        elif "hibrido" in url:
            return ("Híbrido", "modalidade")
        
        # Geografia
        elif "-sp/" in url:
            return ("São Paulo", "geografia")
        elif "-rj/" in url:
            return ("Rio de Janeiro", "geografia")
        elif "-mg/" in url:
            return ("Belo Horizonte", "geografia")
        elif "-df/" in url:
            return ("Brasília", "geografia")
        elif "-pr/" in url:
            return ("Curitiba", "geografia")
        elif "-rs/" in url:
            return ("Porto Alegre", "geografia")
        elif "-pe/" in url:
            return ("Recife", "geografia")
        elif "-ba/" in url:
            return ("Salvador", "geografia")
        
        # Áreas profissionais
        elif "tecnologia" in url:
            return ("Tecnologia/TI", "profissional")
        elif "administracao" in url:
            return ("Administração", "profissional")
        elif "vendas" in url:
            return ("Vendas", "profissional")
        elif "marketing" in url:
            return ("Marketing", "profissional")
        elif "financas" in url:
            return ("Finanças", "profissional")
        elif "recursos-humanos" in url:
            return ("RH", "profissional")
        elif "engenharia" in url:
            return ("Engenharia", "profissional")
        elif "saude" in url:
            return ("Saúde", "profissional")
        elif "educacao" in url:
            return ("Educação", "profissional")
        elif "juridico" in url:
            return ("Jurídico", "profissional")
        
        # Senioridade
        elif "estagio" in url:
            return ("Estágio", "senioridade")
        elif "trainee" in url:
            return ("Trainee", "senioridade")
        elif "junior" in url:
            return ("Júnior", "senioridade")
        elif "pleno" in url:
            return ("Pleno", "senioridade")
        elif "senior" in url:
            return ("Sênior", "senioridade")
        elif "especialista" in url:
            return ("Especialista", "senioridade")
        elif "coordenador" in url:
            return ("Coordenador", "senioridade")
        elif "gerente" in url:
            return ("Gerente", "senioridade")
        elif "diretor" in url:
            return ("Diretor", "senioridade")
        
        # Geral
        elif url == "https://www.catho.com.br/vagas/":
            return ("Todas as vagas", "geral")
        else:
            return ("Personalizada", "outro")


# Instância global do gerenciador
settings_manager = SettingsManager()