"""
Handler para operações de cache
"""

from typing import Dict, Optional

from ..utils.menu_system import MenuSystem, Colors


class CacheHandler:
    """Gerencia operações de cache"""
    
    def __init__(self):
        self.menu = MenuSystem()
    
    async def handle_cache_operations(self, choice: str) -> None:
        """Manipula operações de cache"""
        try:
            from ..systems.compressed_cache import CompressedCache
            cache = CompressedCache()
            
            if choice == "1":  # Listar tudo
                await self._list_all_entries(cache)
            elif choice == "2":  # Por empresa
                await self._search_by_company(cache)
            elif choice == "3":  # Por tecnologia
                await self._search_by_technology(cache)
            elif choice == "4":  # Por localização
                await self._search_by_location(cache)
            elif choice == "5":  # Estatísticas
                await self._show_cache_statistics(cache)
            elif choice == "6":  # Top rankings
                await self._show_top_rankings(cache)
            
            print(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
            input()
            
        except Exception as e:
            self.menu.print_error_message(f"Erro ao acessar cache: {e}")
            input()
    
    async def _list_all_entries(self, cache) -> None:
        """Lista todas as entradas do cache"""
        results = cache.search_cache({})
        print(f"\n{Colors.BOLD}📋 TODAS AS ENTRADAS ({len(results)} encontradas):{Colors.RESET}")
        
        for i, entry in enumerate(results[:10], 1):  # Mostrar apenas 10 primeiros
            print(f"\n{Colors.BOLD}{i:2d}.{Colors.RESET} {entry.url[:60]}...")
            print(f"     📅 Data: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}")
            print(f"     💼 Vagas: {Colors.GREEN}{entry.job_count}{Colors.RESET}")
            print(f"     🏢 Empresas: {Colors.BLUE}{', '.join(entry.companies[:3])}{Colors.RESET}{'...' if len(entry.companies) > 3 else ''}")
        
        if len(results) > 10:
            print(f"\n{Colors.DIM}... e mais {len(results) - 10} entradas{Colors.RESET}")
    
    async def _search_by_company(self, cache) -> None:
        """Busca por empresa"""
        company = input(f"{Colors.BOLD}Digite o nome da empresa: {Colors.RESET}").strip()
        if company:
            results = cache.search_cache({'companies': [company]})
            print(f"\n{Colors.BOLD}🏢 Vagas da empresa '{company}' ({len(results)} encontradas):{Colors.RESET}")
            
            for i, entry in enumerate(results[:5], 1):
                print(f"  {i}. {entry.url[:50]}... ({entry.job_count} vagas)")
    
    async def _search_by_technology(self, cache) -> None:
        """Busca por tecnologia"""
        tech = input(f"{Colors.BOLD}Digite a tecnologia: {Colors.RESET}").strip()
        if tech:
            results = cache.search_cache({'technologies': [tech]})
            print(f"\n{Colors.BOLD}💻 Vagas com '{tech}' ({len(results)} encontradas):{Colors.RESET}")
            
            for i, entry in enumerate(results[:5], 1):
                print(f"  {i}. {entry.url[:50]}... ({entry.job_count} vagas)")
    
    async def _search_by_location(self, cache) -> None:
        """Busca por localização"""
        location = input(f"{Colors.BOLD}Digite a localização: {Colors.RESET}").strip()
        if location:
            results = cache.search_cache({'locations': [location]})
            print(f"\n{Colors.BOLD}📍 Vagas em '{location}' ({len(results)} encontradas):{Colors.RESET}")
            
            for i, entry in enumerate(results[:5], 1):
                print(f"  {i}. {entry.url[:50]}... ({entry.job_count} vagas)")
    
    async def _show_cache_statistics(self, cache) -> None:
        """Mostra estatísticas do cache"""
        cache.print_compression_report()
        cache.index.print_summary()
    
    async def _show_top_rankings(self, cache) -> None:
        """Mostra top rankings"""
        print(f"\n{Colors.BOLD}🏆 TOP RANKINGS:{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}🏢 TOP 10 EMPRESAS:{Colors.RESET}")
        top_companies = cache.get_top_companies(10)
        for i, (company, count) in enumerate(top_companies, 1):
            print(f"   {i:2d}. {Colors.GREEN}{company}{Colors.RESET}: {count} vagas")
        
        print(f"\n{Colors.BOLD}💻 TOP 10 TECNOLOGIAS:{Colors.RESET}")
        top_techs = cache.get_top_technologies(10)
        for i, (tech, count) in enumerate(top_techs, 1):
            print(f"   {i:2d}. {Colors.BLUE}{tech}{Colors.RESET}: {count} vagas")