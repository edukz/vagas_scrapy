"""
Handler para operações de estatísticas
"""

import json
import os
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Optional

from ..utils.menu_system import MenuSystem, Colors


class StatisticsHandler:
    """Gerencia operações de estatísticas e dashboard"""
    
    def __init__(self):
        self.menu = MenuSystem()
    
    async def handle_statistics_dashboard(self) -> None:
        """Exibe dashboard completo de estatísticas"""
        while True:
            try:
                choice = await self._show_statistics_menu()
                
                if choice == "0":  # Voltar
                    break
                elif choice == "1":  # Visão Geral
                    await self._show_general_overview()
                elif choice == "2":  # Análise de Vagas
                    await self._show_job_analysis()
                elif choice == "3":  # Tecnologias
                    await self._show_technology_stats()
                elif choice == "4":  # Empresas
                    await self._show_company_stats()
                elif choice == "5":  # Localização
                    await self._show_location_stats()
                elif choice == "6":  # Salários
                    await self._show_salary_stats()
                elif choice == "7":  # Cache e Performance
                    await self._show_performance_stats()
                elif choice == "8":  # Histórico
                    await self._show_historical_data()
                    
            except Exception as e:
                self.menu.print_error_message(f"Erro no dashboard: {e}")
                input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_statistics_menu(self) -> str:
        """Mostra menu principal de estatísticas"""
        self.menu.clear_screen()
        
        print(f"{Colors.BOLD}{Colors.BLUE}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}║{Colors.RESET}                    {Colors.BOLD}{Colors.WHITE}📊 DASHBOARD DE ESTATÍSTICAS - v4.0.0{Colors.RESET}                    {Colors.BOLD}{Colors.BLUE}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}║{Colors.RESET}                {Colors.GREEN}Sistema Completo de Análise e Métricas{Colors.RESET}                 {Colors.BOLD}{Colors.BLUE}║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        print()
        
        # Status rápido do sistema
        await self._print_quick_stats()
        
        # Menu de opções
        print(f"{Colors.BOLD}📋 CATEGORIAS DE ANÁLISE{Colors.RESET}")
        print()
        
        print(f"{Colors.DIM}┌─ Análises Principais ───────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[1]{Colors.RESET} 🎯 VISÃO GERAL      │ Métricas gerais do sistema e resumo    {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[2]{Colors.RESET} 💼 ANÁLISE DE VAGAS │ Distribuição, níveis, modalidades      {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[3]{Colors.RESET} 💻 TECNOLOGIAS      │ Stack mais demandado, tendências        {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[4]{Colors.RESET} 🏢 EMPRESAS         │ Top contratantes, distribuição          {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()
        
        print(f"{Colors.DIM}┌─ Análises Detalhadas ───────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[5]{Colors.RESET} 📍 LOCALIZAÇÃO      │ Distribuição geográfica de vagas        {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[6]{Colors.RESET} 💰 SALÁRIOS         │ Faixas salariais, análise por nível     {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[7]{Colors.RESET} ⚡ PERFORMANCE      │ Cache, tempos, eficiência do sistema    {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}[8]{Colors.RESET} 📈 HISTÓRICO        │ Evolução temporal e tendências          {Colors.DIM}│{Colors.RESET}")
        print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()
        
        print(f"  {Colors.BOLD}[0]{Colors.RESET} ⬅️  VOLTAR          Retornar ao menu principal")
        print()
        
        return self.menu.get_user_choice("Escolha uma categoria", "0", 
                                       ["0", "1", "2", "3", "4", "5", "6", "7", "8"])
    
    async def _print_quick_stats(self) -> None:
        """Imprime estatísticas rápidas no cabeçalho"""
        try:
            # Contar arquivos de resultados
            results_dir = Path("data/resultados/json")
            total_files = 0
            total_jobs = 0
            latest_date = "N/A"
            
            if results_dir.exists():
                files = list(results_dir.glob("*.json"))
                total_files = len(files)
                
                # Contar total de vagas e encontrar data mais recente
                for file_path in files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if isinstance(data, list):
                            total_jobs += len(data)
                        
                        # Extrair data do nome do arquivo
                        if "_" in file_path.name:
                            date_part = file_path.name.split("_")[-1].replace(".json", "")
                            if len(date_part) >= 8:
                                formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                                if latest_date == "N/A" or formatted_date > latest_date:
                                    latest_date = formatted_date
                    except:
                        continue
            
            # Cache info
            cache_dir = Path("data/cache")
            cache_files = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0
            
            # Status do sistema
            print(f"{Colors.DIM}┌─ Status Rápido ─────────────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}📊 Total de Vagas:{Colors.RESET} {Colors.GREEN}{total_jobs:,}{Colors.RESET}{' ' * max(0, 15-len(f'{total_jobs:,}'))} │ {Colors.BOLD}📅 Última Coleta:{Colors.RESET} {Colors.CYAN}{latest_date}{Colors.RESET}{' ' * max(0, 15-len(latest_date))} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.BOLD}📁 Arquivos:{Colors.RESET} {Colors.YELLOW}{total_files}{Colors.RESET}{' ' * max(0, 20-len(str(total_files)))} │ {Colors.BOLD}💾 Cache:{Colors.RESET} {Colors.BLUE}{cache_files} arquivo(s){Colors.RESET}{' ' * max(0, 15-len(f'{cache_files} arquivo(s)'))} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
            
        except Exception as e:
            print(f"{Colors.DIM}┌─ Status Rápido ─────────────────────────────────────────────────────────────┐{Colors.RESET}")
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.RED}❌ Erro ao carregar estatísticas rápidas: {str(e)[:40]}...{Colors.RESET}{' ' * 20} {Colors.DIM}│{Colors.RESET}")
            print(f"{Colors.DIM}└─────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
            print()
    
    def _load_all_jobs(self) -> list:
        """Carrega todos os jobs dos arquivos JSON"""
        all_jobs = []
        results_dir = Path("data/resultados/json")
        
        if results_dir.exists():
            for file_path in results_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_jobs.extend(data)
                except:
                    continue
        
        return all_jobs
    
    async def _show_general_overview(self) -> None:
        """Exibe visão geral do sistema"""
        self.menu.clear_screen()
        
        print(f"{Colors.BOLD}{Colors.GREEN}🎯 VISÃO GERAL DO SISTEMA{Colors.RESET}")
        print()
        
        try:
            all_jobs = self._load_all_jobs()
            total_jobs = len(all_jobs)
            
            if total_jobs == 0:
                self.menu.print_warning_message("Nenhum dado encontrado. Execute o scraping primeiro.")
                input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
                return
            
            # Análises gerais
            print(f"{Colors.BOLD}📊 MÉTRICAS GERAIS{Colors.RESET}")
            print(f"   Total de vagas coletadas: {Colors.GREEN}{total_jobs:,}{Colors.RESET}")
            
            # Top tecnologias, empresas, etc. (implementação similar ao código original)
            self._show_technology_overview(all_jobs, total_jobs)
            self._show_company_overview(all_jobs, total_jobs)
            self._show_work_mode_overview(all_jobs, total_jobs)
            
        except Exception as e:
            self.menu.print_error_message(f"Erro ao gerar visão geral: {e}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _show_technology_overview(self, all_jobs: list, total_jobs: int) -> None:
        """Mostra overview de tecnologias"""
        tech_count = {}
        for job in all_jobs:
            for tech in job.get('tecnologias_detectadas', []):
                tech_count[tech] = tech_count.get(tech, 0) + 1
        
        if tech_count:
            print(f"\n{Colors.BOLD}💻 TOP 10 TECNOLOGIAS MAIS DEMANDADAS{Colors.RESET}")
            for i, (tech, count) in enumerate(sorted(tech_count.items(), key=lambda x: x[1], reverse=True)[:10], 1):
                percentage = (count / total_jobs) * 100
                print(f"   {i:2d}. {Colors.CYAN}{tech:<20}{Colors.RESET} {Colors.GREEN}{count:4d}{Colors.RESET} vagas ({percentage:4.1f}%)")
    
    def _show_company_overview(self, all_jobs: list, total_jobs: int) -> None:
        """Mostra overview de empresas"""
        company_count = {}
        for job in all_jobs:
            company = job.get('empresa', 'N/A')
            if company and company != 'N/A':
                company_count[company] = company_count.get(company, 0) + 1
        
        if company_count:
            print(f"\n{Colors.BOLD}🏢 TOP 10 EMPRESAS QUE MAIS CONTRATAM{Colors.RESET}")
            for i, (company, count) in enumerate(sorted(company_count.items(), key=lambda x: x[1], reverse=True)[:10], 1):
                print(f"   {i:2d}. {Colors.YELLOW}{company[:30]:<30}{Colors.RESET} {Colors.GREEN}{count:3d}{Colors.RESET} vagas")
    
    def _show_work_mode_overview(self, all_jobs: list, total_jobs: int) -> None:
        """Mostra overview de modalidades de trabalho"""
        modalidade_count = {}
        for job in all_jobs:
            modalidade = job.get('modalidade_trabalho', 'N/A')
            modalidade_count[modalidade] = modalidade_count.get(modalidade, 0) + 1
        
        if modalidade_count:
            print(f"\n{Colors.BOLD}🏠 MODALIDADES DE TRABALHO{Colors.RESET}")
            for modalidade, count in sorted(modalidade_count.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_jobs) * 100
                print(f"   • {Colors.BLUE}{modalidade:<20}{Colors.RESET} {Colors.GREEN}{count:4d}{Colors.RESET} vagas ({percentage:4.1f}%)")
    
    # Métodos simplificados para outras análises
    async def _show_job_analysis(self) -> None:
        """Análise detalhada de vagas"""
        self.menu.clear_screen()
        print(f"{Colors.BOLD}{Colors.BLUE}💼 ANÁLISE DETALHADA DE VAGAS{Colors.RESET}")
        print()
        
        try:
            all_jobs = self._load_all_jobs()
            total_jobs = len(all_jobs)
            
            if total_jobs == 0:
                self.menu.print_warning_message("Nenhum dado encontrado. Execute o scraping primeiro.")
                input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
                return
            
            # Análise de níveis de senioridade
            self._show_seniority_analysis(all_jobs, total_jobs)
            
            # Análise de qualidade dos dados
            self._show_data_quality_analysis(all_jobs, total_jobs)
            
            # Análise de completude
            self._show_completeness_analysis(all_jobs, total_jobs)
            
        except Exception as e:
            self.menu.print_error_message(f"Erro na análise de vagas: {e}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_technology_stats(self) -> None:
        """Estatísticas de tecnologias"""
        self.menu.clear_screen()
        print(f"{Colors.BOLD}{Colors.CYAN}💻 ANÁLISE DETALHADA DE TECNOLOGIAS{Colors.RESET}")
        print()
        
        try:
            all_jobs = self._load_all_jobs()
            total_jobs = len(all_jobs)
            
            if total_jobs == 0:
                self.menu.print_warning_message("Nenhum dado encontrado. Execute o scraping primeiro.")
                input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
                return
            
            # Análise por categoria de tecnologia
            self._show_tech_categories(all_jobs, total_jobs)
            
            # Stack completo mais comum
            self._show_common_stacks(all_jobs, total_jobs)
            
            # Tecnologias emergentes
            self._show_emerging_technologies(all_jobs, total_jobs)
            
        except Exception as e:
            self.menu.print_error_message(f"Erro na análise de tecnologias: {e}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_company_stats(self) -> None:
        """Estatísticas de empresas"""
        self.menu.clear_screen()
        print(f"{Colors.BOLD}{Colors.YELLOW}🏢 ANÁLISE DE EMPRESAS{Colors.RESET}")
        self.menu.print_info_message("Top empresas e distribuição por porte")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_location_stats(self) -> None:
        """Estatísticas de localização"""
        self.menu.clear_screen()
        print(f"{Colors.BOLD}{Colors.MAGENTA}📍 ANÁLISE DE LOCALIZAÇÃO{Colors.RESET}")
        self.menu.print_info_message("Distribuição geográfica e modalidades de trabalho")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_salary_stats(self) -> None:
        """Estatísticas de salários"""
        self.menu.clear_screen()
        print(f"{Colors.BOLD}{Colors.GREEN}💰 ANÁLISE DE SALÁRIOS{Colors.RESET}")
        self.menu.print_info_message("Análise de salários ainda não implementada - dados de salário não coletados sistematicamente.")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_performance_stats(self) -> None:
        """Estatísticas de performance do sistema"""
        self.menu.clear_screen()
        print(f"{Colors.BOLD}{Colors.RED}⚡ PERFORMANCE E CACHE{Colors.RESET}")
        print()
        
        try:
            # Estatísticas de arquivos
            self._show_file_statistics()
            
            # Estatísticas de cache
            self._show_cache_statistics()
            
            # Estatísticas de sistema
            self._show_system_statistics()
            
        except Exception as e:
            self.menu.print_error_message(f"Erro nas estatísticas de performance: {e}")
        
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_historical_data(self) -> None:
        """Mostra dados históricos e tendências"""
        self.menu.clear_screen()
        print(f"{Colors.BOLD}{Colors.PURPLE}📈 ANÁLISE HISTÓRICA{Colors.RESET}")
        self.menu.print_info_message("Evolução temporal e tendências de tecnologias")
        input(f"\n{Colors.DIM}Pressione Enter para continuar...{Colors.RESET}")
    
    def _show_seniority_analysis(self, all_jobs: list, total_jobs: int) -> None:
        """Análise de níveis de senioridade"""
        seniority_count = {}
        for job in all_jobs:
            seniority = job.get('nivel_senioridade', 'N/A')
            seniority_count[seniority] = seniority_count.get(seniority, 0) + 1
        
        print(f"{Colors.BOLD}🎯 DISTRIBUIÇÃO POR NÍVEL DE SENIORIDADE{Colors.RESET}")
        if seniority_count:
            for seniority, count in sorted(seniority_count.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_jobs) * 100
                bar_length = int(percentage / 3)  # Scale bar
                bar = "█" * bar_length + "░" * (33 - bar_length)
                print(f"   {Colors.CYAN}{seniority:<15}{Colors.RESET} {Colors.GREEN}{count:4d}{Colors.RESET} │{bar}│ {percentage:5.1f}%")
    
    def _show_data_quality_analysis(self, all_jobs: list, total_jobs: int) -> None:
        """Análise de qualidade dos dados"""
        complete_fields = 0
        fields_to_check = ['titulo', 'empresa', 'modalidade_trabalho', 'localizacao']
        
        for job in all_jobs:
            job_complete = all(job.get(field) and job.get(field) != 'N/A' for field in fields_to_check)
            if job_complete:
                complete_fields += 1
        
        print(f"\n{Colors.BOLD}📊 QUALIDADE DOS DADOS{Colors.RESET}")
        quality_percentage = (complete_fields / total_jobs) * 100 if total_jobs > 0 else 0
        print(f"   Registros completos: {Colors.GREEN}{complete_fields:,}{Colors.RESET} de {Colors.YELLOW}{total_jobs:,}{Colors.RESET} ({quality_percentage:.1f}%)")
        
        # Análise de campos vazios
        field_stats = {}
        for field in fields_to_check:
            empty_count = sum(1 for job in all_jobs if not job.get(field) or job.get(field) == 'N/A')
            field_stats[field] = empty_count
        
        print(f"   Campos com dados faltantes:")
        for field, empty_count in sorted(field_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (empty_count / total_jobs) * 100
            print(f"     • {field}: {Colors.RED}{empty_count:,}{Colors.RESET} ({percentage:.1f}%)")
    
    def _show_completeness_analysis(self, all_jobs: list, total_jobs: int) -> None:
        """Análise de completude dos dados"""
        tech_detected = sum(1 for job in all_jobs if job.get('tecnologias_detectadas'))
        with_description = sum(1 for job in all_jobs if job.get('descricao') and len(job.get('descricao', '')) > 50)
        
        print(f"\n{Colors.BOLD}🔍 ANÁLISE DE COMPLETUDE{Colors.RESET}")
        print(f"   Vagas com tecnologias detectadas: {Colors.GREEN}{tech_detected:,}{Colors.RESET} ({(tech_detected/total_jobs)*100:.1f}%)")
        print(f"   Vagas com descrição detalhada: {Colors.GREEN}{with_description:,}{Colors.RESET} ({(with_description/total_jobs)*100:.1f}%)")
    
    def _show_tech_categories(self, all_jobs: list, total_jobs: int) -> None:
        """Mostra tecnologias por categoria"""
        tech_categories = {
            'Linguagens': ['python', 'java', 'javascript', 'typescript', 'c#', 'php', 'kotlin', 'swift'],
            'Frontend': ['react', 'angular', 'vue', 'jquery', 'html', 'css', 'bootstrap'],
            'Backend': ['node.js', 'spring', 'django', 'flask', 'express', '.net'],
            'Mobile': ['react native', 'flutter', 'android', 'ios', 'xamarin'],
            'Databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sql server'],
            'Cloud/DevOps': ['aws', 'azure', 'docker', 'kubernetes', 'jenkins', 'gitlab']
        }
        
        print(f"{Colors.BOLD}🏗️ TECNOLOGIAS POR CATEGORIA{Colors.RESET}")
        
        for category, techs in tech_categories.items():
            category_count = {}
            for job in all_jobs:
                job_techs = job.get('tecnologias_detectadas', [])
                for tech in techs:
                    if tech.lower() in [t.lower() for t in job_techs]:
                        category_count[tech] = category_count.get(tech, 0) + 1
            
            if category_count:
                print(f"\n   {Colors.BOLD}{Colors.BLUE}{category}:{Colors.RESET}")
                for tech, count in sorted(category_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / total_jobs) * 100
                    print(f"     • {Colors.CYAN}{tech:<20}{Colors.RESET} {Colors.GREEN}{count:3d}{Colors.RESET} ({percentage:4.1f}%)")
    
    def _show_common_stacks(self, all_jobs: list, total_jobs: int) -> None:
        """Mostra stacks tecnológicos mais comuns"""
        stack_combinations = {}
        
        for job in all_jobs:
            techs = job.get('tecnologias_detectadas', [])
            if len(techs) >= 2:
                # Combinar tecnologias em stacks de 2-3
                for i in range(len(techs)):
                    for j in range(i+1, len(techs)):
                        stack = tuple(sorted([techs[i].lower(), techs[j].lower()]))
                        stack_combinations[stack] = stack_combinations.get(stack, 0) + 1
        
        print(f"\n{Colors.BOLD}🔗 COMBINAÇÕES TECNOLÓGICAS MAIS COMUNS{Colors.RESET}")
        if stack_combinations:
            top_stacks = sorted(stack_combinations.items(), key=lambda x: x[1], reverse=True)[:8]
            for stack, count in top_stacks:
                percentage = (count / total_jobs) * 100
                stack_str = " + ".join(stack)
                print(f"   • {Colors.YELLOW}{stack_str:<35}{Colors.RESET} {Colors.GREEN}{count:3d}{Colors.RESET} ({percentage:4.1f}%)")
    
    def _show_emerging_technologies(self, all_jobs: list, total_jobs: int) -> None:
        """Identifica tecnologias emergentes"""
        emerging_keywords = ['ai', 'machine learning', 'blockchain', 'microservices', 'graphql', 
                           'tensorflow', 'pytorch', 'kubernetes', 'serverless', 'edge computing']
        
        emerging_count = {}
        for job in all_jobs:
            description = job.get('descricao', '').lower()
            title = job.get('titulo', '').lower()
            full_text = f"{description} {title}"
            
            for keyword in emerging_keywords:
                if keyword in full_text:
                    emerging_count[keyword] = emerging_count.get(keyword, 0) + 1
        
        print(f"\n{Colors.BOLD}🚀 TECNOLOGIAS EMERGENTES{Colors.RESET}")
        if emerging_count:
            for tech, count in sorted(emerging_count.items(), key=lambda x: x[1], reverse=True)[:8]:
                percentage = (count / total_jobs) * 100
                if percentage > 0.5:  # Só mostrar se tiver pelo menos 0.5%
                    print(f"   • {Colors.MAGENTA}{tech:<20}{Colors.RESET} {Colors.GREEN}{count:3d}{Colors.RESET} ({percentage:4.1f}%)")
    
    def _show_file_statistics(self) -> None:
        """Mostra estatísticas de arquivos"""
        results_dir = Path("data/resultados")
        
        print(f"{Colors.BOLD}📁 ESTATÍSTICAS DE ARQUIVOS{Colors.RESET}")
        
        if results_dir.exists():
            json_files = list((results_dir / "json").glob("*.json")) if (results_dir / "json").exists() else []
            csv_files = list((results_dir / "csv").glob("*.csv")) if (results_dir / "csv").exists() else []
            
            total_size_json = sum(f.stat().st_size for f in json_files) / (1024*1024)  # MB
            total_size_csv = sum(f.stat().st_size for f in csv_files) / (1024*1024) if csv_files else 0
            
            print(f"   📄 Arquivos JSON: {Colors.GREEN}{len(json_files)}{Colors.RESET} ({total_size_json:.1f} MB)")
            print(f"   📊 Arquivos CSV: {Colors.GREEN}{len(csv_files)}{Colors.RESET} ({total_size_csv:.1f} MB)")
            print(f"   💾 Tamanho total: {Colors.YELLOW}{total_size_json + total_size_csv:.1f} MB{Colors.RESET}")
        else:
            print(f"   {Colors.RED}❌ Diretório de resultados não encontrado{Colors.RESET}")
    
    def _show_cache_statistics(self) -> None:
        """Mostra estatísticas de cache"""
        cache_dir = Path("data/cache")
        
        print(f"\n{Colors.BOLD}⚡ ESTATÍSTICAS DE CACHE{Colors.RESET}")
        
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.json"))
            total_cache_size = sum(f.stat().st_size for f in cache_files) / (1024*1024)  # MB
            
            # Verificar idade dos arquivos de cache
            if cache_files:
                newest_cache = max(cache_files, key=lambda f: f.stat().st_mtime)
                oldest_cache = min(cache_files, key=lambda f: f.stat().st_mtime)
                
                newest_date = datetime.fromtimestamp(newest_cache.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                oldest_date = datetime.fromtimestamp(oldest_cache.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                
                print(f"   📦 Arquivos em cache: {Colors.GREEN}{len(cache_files)}{Colors.RESET}")
                print(f"   💾 Tamanho do cache: {Colors.YELLOW}{total_cache_size:.1f} MB{Colors.RESET}")
                print(f"   🆕 Cache mais recente: {Colors.CYAN}{newest_date}{Colors.RESET}")
                print(f"   🗓️ Cache mais antigo: {Colors.DIM}{oldest_date}{Colors.RESET}")
            else:
                print(f"   {Colors.YELLOW}⚠️ Nenhum arquivo de cache encontrado{Colors.RESET}")
        else:
            print(f"   {Colors.RED}❌ Diretório de cache não encontrado{Colors.RESET}")
    
    def _show_system_statistics(self) -> None:
        """Mostra estatísticas do sistema"""
        print(f"\n{Colors.BOLD}🖥️ ESTATÍSTICAS DO SISTEMA{Colors.RESET}")
        
        # Estatísticas de configuração
        config_dir = Path("config")
        if config_dir.exists():
            config_files = list(config_dir.glob("*.json"))
            print(f"   ⚙️ Arquivos de configuração: {Colors.GREEN}{len(config_files)}{Colors.RESET}")
        
        # Estatísticas de CV
        cv_dir = Path("data/cv_input")
        if cv_dir.exists():
            cv_files = list(cv_dir.glob("*"))
            cv_types = {}
            for f in cv_files:
                ext = f.suffix.lower()
                cv_types[ext] = cv_types.get(ext, 0) + 1
            
            print(f"   📄 Currículos disponíveis: {Colors.GREEN}{len(cv_files)}{Colors.RESET}")
            if cv_types:
                for ext, count in cv_types.items():
                    print(f"     • {ext or 'sem extensão'}: {count}")
        
        # Tempo de execução estimado
        print(f"   ⏱️ Sistema ativo desde: {Colors.CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")