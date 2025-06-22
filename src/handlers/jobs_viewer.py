"""
Visualizador de Vagas Salvas

Sistema para explorar, pesquisar e analisar as vagas já coletadas
e armazenadas no sistema.
"""

import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from ..utils.menu_system import Colors


class JobsViewer:
    """Visualizador e explorador de vagas salvas"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.results_dir = self.data_dir / "resultados"
        self.cache_dir = self.data_dir / "cache"
        
    async def show_jobs_dashboard(self) -> None:
        """Interface principal do visualizador"""
        while True:
            print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}")
            print(f"{Colors.CYAN}║{Colors.RESET}                        📋 VISUALIZADOR DE VAGAS                          {Colors.CYAN}║{Colors.RESET}")
            print(f"{Colors.CYAN}║{Colors.RESET}                     Explore suas vagas coletadas                        {Colors.CYAN}║{Colors.RESET}")
            print(f"{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}")
            
            # Estatísticas rápidas
            stats = self._get_quick_stats()
            print(f"\n📊 RESUMO RÁPIDO:")
            print(f"   📁 Arquivos de vagas: {stats['files_count']}")
            print(f"   📋 Total de vagas: {stats['total_jobs']}")
            print(f"   📅 Última coleta: {stats['last_collection']}")
            print(f"   💾 Espaço usado: {stats['storage_size']}")
            
            print(f"\n{Colors.YELLOW}📋 O QUE DESEJA FAZER?{Colors.RESET}")
            print(f"  {Colors.CYAN}[1]{Colors.RESET} 📋 Ver todas as vagas (lista completa)")
            print(f"  {Colors.CYAN}[2]{Colors.RESET} 🔍 Buscar vagas por palavra-chave")
            print(f"  {Colors.CYAN}[3]{Colors.RESET} 📊 Estatísticas detalhadas")
            print(f"  {Colors.CYAN}[4]{Colors.RESET} 🏢 Ver vagas por empresa")
            print(f"  {Colors.CYAN}[5]{Colors.RESET} 💻 Ver vagas por tecnologia")
            print(f"  {Colors.CYAN}[6]{Colors.RESET} 📅 Ver vagas por data de coleta")
            print(f"  {Colors.CYAN}[7]{Colors.RESET} 🔗 Exportar vagas selecionadas")
            print(f"  {Colors.CYAN}[8]{Colors.RESET} 🧹 Gerenciar arquivos de dados")
            print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar ao menu principal")
            
            choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (0-8): {Colors.RESET}").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                await self._show_all_jobs()
            elif choice == "2":
                await self._search_jobs()
            elif choice == "3":
                await self._show_detailed_stats()
            elif choice == "4":
                await self._show_jobs_by_company()
            elif choice == "5":
                await self._show_jobs_by_technology()
            elif choice == "6":
                await self._show_jobs_by_date()
            elif choice == "7":
                await self._export_selected_jobs()
            elif choice == "8":
                await self._manage_data_files()
            else:
                print(f"{Colors.RED}❌ Opção inválida.{Colors.RESET}")
    
    def _get_quick_stats(self) -> Dict:
        """Estatísticas rápidas do sistema"""
        stats = {
            'files_count': 0,
            'total_jobs': 0,
            'last_collection': 'Nunca',
            'storage_size': '0 MB'
        }
        
        try:
            # Contar arquivos JSON de resultados
            json_files = list(self.results_dir.glob("json/*.json"))
            stats['files_count'] = len(json_files)
            
            # Contar total de vagas
            total_jobs = 0
            latest_file = None
            latest_time = 0
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            total_jobs += len(data)
                    
                    # Verificar se é o arquivo mais recente
                    file_time = json_file.stat().st_mtime
                    if file_time > latest_time:
                        latest_time = file_time
                        latest_file = json_file
                except:
                    continue
            
            stats['total_jobs'] = total_jobs
            
            # Data da última coleta
            if latest_file:
                latest_date = datetime.fromtimestamp(latest_time)
                stats['last_collection'] = latest_date.strftime("%d/%m/%Y às %H:%M")
            
            # Tamanho do armazenamento
            total_size = 0
            for file_path in self.data_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            stats['storage_size'] = f"{total_size / (1024*1024):.1f} MB"
            
        except Exception as e:
            print(f"Erro ao calcular estatísticas: {e}")
        
        return stats
    
    def _load_all_jobs(self) -> List[Dict]:
        """Carrega todas as vagas de todos os arquivos"""
        all_jobs = []
        
        try:
            # Carregar de arquivos JSON de resultados
            json_files = list(self.results_dir.glob("json/*.json"))
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            # Adicionar metadados do arquivo
                            for job in data:
                                job['_arquivo_origem'] = json_file.name
                                job['_data_arquivo'] = datetime.fromtimestamp(
                                    json_file.stat().st_mtime
                                ).strftime("%d/%m/%Y")
                            
                            all_jobs.extend(data)
                except Exception as e:
                    print(f"Erro ao carregar {json_file}: {e}")
                    continue
            
            print(f"📊 Carregadas {len(all_jobs)} vagas de {len(json_files)} arquivos")
            
        except Exception as e:
            print(f"Erro geral ao carregar vagas: {e}")
        
        return all_jobs
    
    async def _show_all_jobs(self) -> None:
        """Mostra todas as vagas do sistema"""
        print(f"\n{Colors.CYAN}📋 CARREGANDO TODAS AS VAGAS...{Colors.RESET}")
        
        all_jobs = self._load_all_jobs()
        
        if not all_jobs:
            print(f"{Colors.YELLOW}⚠️ Nenhuma vaga encontrada no sistema.{Colors.RESET}")
            return
        
        print(f"\n{Colors.GREEN}✅ {len(all_jobs)} vagas carregadas!{Colors.RESET}")
        
        # Opções de visualização
        print(f"\n{Colors.YELLOW}📋 COMO DESEJA VER AS VAGAS?{Colors.RESET}")
        print(f"  {Colors.CYAN}[1]{Colors.RESET} 📝 Lista compacta (título + empresa)")
        print(f"  {Colors.CYAN}[2]{Colors.RESET} 📄 Lista detalhada (todas as informações)")
        print(f"  {Colors.CYAN}[3]{Colors.RESET} 📊 Agrupar por empresa")
        print(f"  {Colors.CYAN}[4]{Colors.RESET} 📅 Agrupar por data de coleta")
        print(f"  {Colors.CYAN}[0]{Colors.RESET} ⬅️  Voltar")
        
        view_choice = input(f"\n{Colors.YELLOW}➤ Sua escolha (0-4): {Colors.RESET}").strip()
        
        if view_choice == "1":
            self._show_jobs_compact(all_jobs)
        elif view_choice == "2":
            self._show_jobs_detailed(all_jobs)
        elif view_choice == "3":
            self._show_jobs_grouped_by_company(all_jobs)
        elif view_choice == "4":
            self._show_jobs_grouped_by_date(all_jobs)
    
    def _show_jobs_compact(self, jobs: List[Dict]) -> None:
        """Exibe vagas em formato compacto"""
        print(f"\n{Colors.CYAN}📝 LISTA COMPACTA ({len(jobs)} vagas){Colors.RESET}")
        print(f"{Colors.GRAY}{'─' * 80}{Colors.RESET}")
        
        for i, job in enumerate(jobs, 1):
            title = job.get('titulo', 'Título não disponível')[:50]
            company = job.get('empresa', 'Empresa não identificada')[:30]
            location = job.get('localizacao', job.get('regime', 'N/A'))
            date_collected = job.get('_data_arquivo', 'N/A')
            
            print(f"{Colors.YELLOW}{i:4d}.{Colors.RESET} {title}")
            print(f"      🏢 {company} | 📍 {location} | 📅 {date_collected}")
            
            # Pausar a cada 20 vagas
            if i % 20 == 0 and i < len(jobs):
                try:
                    response = input(f"\n{Colors.GRAY}[Enter] Continuar | [Q] Parar | [D] Ver detalhes da vaga {i}: {Colors.RESET}").strip().upper()
                    if response == 'Q':
                        print(f"{Colors.GRAY}... e mais {len(jobs) - i} vagas{Colors.RESET}")
                        break
                    elif response == 'D':
                        self._show_single_job_details(jobs[i-1])
                except (KeyboardInterrupt, EOFError):
                    break
        
        print(f"\n{Colors.GREEN}✅ Exibição concluída!{Colors.RESET}")
        input(f"{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    def _show_jobs_detailed(self, jobs: List[Dict]) -> None:
        """Exibe vagas em formato detalhado"""
        print(f"\n{Colors.CYAN}📄 LISTA DETALHADA ({len(jobs)} vagas){Colors.RESET}")
        print(f"{Colors.GRAY}{'═' * 80}{Colors.RESET}")
        
        for i, job in enumerate(jobs, 1):
            print(f"\n{Colors.YELLOW}▶ VAGA {i}{Colors.RESET}")
            self._show_single_job_details(job)
            
            # Pausar a cada 5 vagas
            if i % 5 == 0 and i < len(jobs):
                try:
                    response = input(f"\n{Colors.GRAY}[Enter] Continuar | [Q] Parar: {Colors.RESET}").strip().upper()
                    if response == 'Q':
                        break
                except (KeyboardInterrupt, EOFError):
                    break
        
        print(f"\n{Colors.GREEN}✅ Exibição concluída!{Colors.RESET}")
        input(f"{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    def _show_single_job_details(self, job: Dict) -> None:
        """Mostra detalhes de uma única vaga"""
        print(f"📋 {Colors.BOLD}{job.get('titulo', 'Título não disponível')}{Colors.RESET}")
        print(f"🏢 Empresa: {job.get('empresa', 'Não identificada')}")
        print(f"📍 Local: {job.get('localizacao', 'Não informado')}")
        print(f"💰 Salário: {job.get('salario', 'Não informado')}")
        print(f"📊 Nível: {job.get('nivel', 'Não especificado')}")
        print(f"🏠 Regime: {job.get('regime', job.get('modalidade_trabalho', 'Não especificado'))}")
        
        if job.get('tecnologias_detectadas'):
            techs = ', '.join(job['tecnologias_detectadas'])
            print(f"💻 Tecnologias: {techs}")
        
        print(f"📅 Coletada em: {job.get('data_coleta', job.get('_data_arquivo', 'N/A'))}")
        print(f"📁 Arquivo: {job.get('_arquivo_origem', 'N/A')}")
        
        if job.get('link'):
            print(f"🔗 Link: {job['link']}")
        
        print(f"{Colors.GRAY}{'─' * 60}{Colors.RESET}")
    
    async def _search_jobs(self) -> None:
        """Busca vagas por palavra-chave"""
        print(f"\n{Colors.CYAN}🔍 BUSCA DE VAGAS{Colors.RESET}")
        
        keyword = input(f"{Colors.YELLOW}Digite a palavra-chave (título, empresa, tecnologia): {Colors.RESET}").strip()
        
        if not keyword:
            print(f"{Colors.RED}❌ Palavra-chave não pode estar vazia.{Colors.RESET}")
            return
        
        print(f"{Colors.GRAY}🔍 Buscando por '{keyword}'...{Colors.RESET}")
        
        all_jobs = self._load_all_jobs()
        
        # Buscar em múltiplos campos
        matching_jobs = []
        keyword_lower = keyword.lower()
        
        for job in all_jobs:
            # Campos para buscar
            search_fields = [
                job.get('titulo', ''),
                job.get('empresa', ''),
                job.get('localizacao', ''),
                ' '.join(job.get('tecnologias_detectadas', [])),
                job.get('nivel', ''),
                job.get('salario', '')
            ]
            
            # Verificar se a palavra-chave está em algum campo
            if any(keyword_lower in field.lower() for field in search_fields):
                matching_jobs.append(job)
        
        if matching_jobs:
            print(f"\n{Colors.GREEN}✅ Encontradas {len(matching_jobs)} vagas com '{keyword}'{Colors.RESET}")
            self._show_jobs_compact(matching_jobs)
        else:
            print(f"\n{Colors.YELLOW}⚠️ Nenhuma vaga encontrada com '{keyword}'{Colors.RESET}")
            
            # Sugerir palavras similares
            print(f"\n{Colors.GRAY}💡 Sugestões:{Colors.RESET}")
            suggestions = self._get_search_suggestions(keyword, all_jobs)
            if suggestions:
                for suggestion in suggestions[:5]:
                    print(f"   • {suggestion}")
            else:
                print("   • Tente termos mais gerais (ex: 'python', 'junior', 'remoto')")
    
    def _get_search_suggestions(self, keyword: str, jobs: List[Dict]) -> List[str]:
        """Gera sugestões de busca baseado nas vagas existentes"""
        suggestions = set()
        keyword_lower = keyword.lower()
        
        # Coletar termos similares
        for job in jobs:
            # Verificar títulos
            title_words = job.get('titulo', '').lower().split()
            for word in title_words:
                if len(word) > 3 and keyword_lower in word and word != keyword_lower:
                    suggestions.add(word)
            
            # Verificar empresas
            company = job.get('empresa', '')
            if len(company) > 3 and keyword_lower in company.lower():
                suggestions.add(company)
            
            # Verificar tecnologias
            for tech in job.get('tecnologias_detectadas', []):
                if keyword_lower in tech.lower() and tech.lower() != keyword_lower:
                    suggestions.add(tech)
        
        return sorted(list(suggestions))
    
    async def _show_detailed_stats(self) -> None:
        """Mostra estatísticas detalhadas do sistema"""
        print(f"\n{Colors.CYAN}📊 ESTATÍSTICAS DETALHADAS{Colors.RESET}")
        print(f"{Colors.GRAY}Carregando dados...{Colors.RESET}")
        
        all_jobs = self._load_all_jobs()
        
        if not all_jobs:
            print(f"{Colors.YELLOW}⚠️ Nenhuma vaga para analisar.{Colors.RESET}")
            return
        
        # Calcular estatísticas
        stats = self._calculate_detailed_stats(all_jobs)
        
        print(f"\n{Colors.GREEN}📊 RELATÓRIO COMPLETO ({len(all_jobs)} vagas){Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
        
        # Estatísticas gerais
        print(f"📋 Total de vagas: {stats['total']}")
        print(f"📁 Arquivos de dados: {stats['files_count']}")
        print(f"📅 Período: {stats['date_range']}")
        
        # Top empresas
        print(f"\n🏢 TOP EMPRESAS:")
        for company, count in stats['top_companies'][:10]:
            print(f"   • {company}: {count} vagas")
        
        # Top tecnologias
        if stats['top_technologies']:
            print(f"\n💻 TOP TECNOLOGIAS:")
            for tech, count in stats['top_technologies'][:10]:
                print(f"   • {tech}: {count} vagas")
        
        # Distribuição por modalidade
        if stats['work_modes']:
            print(f"\n🏠 MODALIDADES DE TRABALHO:")
            for mode, count in stats['work_modes'].items():
                percentage = (count / stats['total']) * 100
                print(f"   • {mode}: {count} vagas ({percentage:.1f}%)")
        
        # Níveis de experiência
        if stats['experience_levels']:
            print(f"\n📊 NÍVEIS DE EXPERIÊNCIA:")
            for level, count in stats['experience_levels'].items():
                percentage = (count / stats['total']) * 100
                print(f"   • {level}: {count} vagas ({percentage:.1f}%)")
        
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    def _calculate_detailed_stats(self, jobs: List[Dict]) -> Dict:
        """Calcula estatísticas detalhadas"""
        from collections import Counter
        
        stats = {
            'total': len(jobs),
            'files_count': len(set(job.get('_arquivo_origem', 'unknown') for job in jobs)),
            'top_companies': [],
            'top_technologies': [],
            'work_modes': {},
            'experience_levels': {},
            'date_range': 'N/A'
        }
        
        # Empresas
        companies = [job.get('empresa', 'Não identificada') for job in jobs]
        company_counts = Counter(companies)
        stats['top_companies'] = company_counts.most_common()
        
        # Tecnologias
        all_techs = []
        for job in jobs:
            all_techs.extend(job.get('tecnologias_detectadas', []))
        if all_techs:
            tech_counts = Counter(all_techs)
            stats['top_technologies'] = tech_counts.most_common()
        
        # Modalidades de trabalho
        modes = [job.get('regime', job.get('modalidade_trabalho', 'Não especificado')) for job in jobs]
        stats['work_modes'] = dict(Counter(modes))
        
        # Níveis
        levels = [job.get('nivel', 'Não especificado') for job in jobs]
        stats['experience_levels'] = dict(Counter(levels))
        
        # Período
        dates = [job.get('_data_arquivo', '') for job in jobs if job.get('_data_arquivo')]
        if dates:
            unique_dates = sorted(set(dates))
            if len(unique_dates) == 1:
                stats['date_range'] = unique_dates[0]
            else:
                stats['date_range'] = f"{unique_dates[0]} até {unique_dates[-1]}"
        
        return stats
    
    async def _show_jobs_by_company(self) -> None:
        """Mostra vagas agrupadas por empresa"""
        print(f"\n{Colors.CYAN}🏢 VAGAS POR EMPRESA{Colors.RESET}")
        
        all_jobs = self._load_all_jobs()
        
        # Agrupar por empresa
        companies = {}
        for job in all_jobs:
            company = job.get('empresa', 'Empresa não identificada')
            if company not in companies:
                companies[company] = []
            companies[company].append(job)
        
        # Ordenar por número de vagas
        sorted_companies = sorted(companies.items(), key=lambda x: len(x[1]), reverse=True)
        
        print(f"\n{Colors.GREEN}📊 {len(sorted_companies)} empresas encontradas{Colors.RESET}")
        
        for i, (company, company_jobs) in enumerate(sorted_companies, 1):
            print(f"\n{Colors.YELLOW}{i:3d}. {company}{Colors.RESET} ({len(company_jobs)} vagas)")
            
            # Mostrar primeiras 3 vagas da empresa
            for j, job in enumerate(company_jobs[:3], 1):
                title = job.get('titulo', 'Título não disponível')[:50]
                print(f"     {j}. {title}")
            
            if len(company_jobs) > 3:
                print(f"     ... e mais {len(company_jobs) - 3} vagas")
            
            # Pausar a cada 10 empresas
            if i % 10 == 0 and i < len(sorted_companies):
                try:
                    response = input(f"\n{Colors.GRAY}[Enter] Continuar | [Q] Parar | [D] Ver detalhes da empresa {i}: {Colors.RESET}").strip().upper()
                    if response == 'Q':
                        break
                    elif response == 'D':
                        print(f"\n{Colors.CYAN}📋 TODAS AS VAGAS DA {company.upper()}:{Colors.RESET}")
                        self._show_jobs_compact(company_jobs)
                except (KeyboardInterrupt, EOFError):
                    break
        
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_jobs_by_technology(self) -> None:
        """Mostra vagas agrupadas por tecnologia"""
        print(f"\n{Colors.CYAN}💻 VAGAS POR TECNOLOGIA{Colors.RESET}")
        
        all_jobs = self._load_all_jobs()
        
        # Agrupar por tecnologia
        technologies = {}
        for job in all_jobs:
            for tech in job.get('tecnologias_detectadas', []):
                if tech not in technologies:
                    technologies[tech] = []
                technologies[tech].append(job)
        
        if not technologies:
            print(f"{Colors.YELLOW}⚠️ Nenhuma tecnologia foi detectada nas vagas.{Colors.RESET}")
            return
        
        # Ordenar por número de vagas
        sorted_techs = sorted(technologies.items(), key=lambda x: len(x[1]), reverse=True)
        
        print(f"\n{Colors.GREEN}📊 {len(sorted_techs)} tecnologias encontradas{Colors.RESET}")
        
        for i, (tech, tech_jobs) in enumerate(sorted_techs, 1):
            print(f"\n{Colors.YELLOW}{i:3d}. {tech}{Colors.RESET} ({len(tech_jobs)} vagas)")
            
            # Mostrar empresas que usam essa tecnologia
            companies = list(set(job.get('empresa', 'N/A') for job in tech_jobs))[:5]
            print(f"     🏢 Empresas: {', '.join(companies)}")
            
            # Pausar a cada 15 tecnologias
            if i % 15 == 0 and i < len(sorted_techs):
                try:
                    response = input(f"\n{Colors.GRAY}[Enter] Continuar | [Q] Parar | [D] Ver vagas de {tech}: {Colors.RESET}").strip().upper()
                    if response == 'Q':
                        break
                    elif response == 'D':
                        print(f"\n{Colors.CYAN}📋 TODAS AS VAGAS COM {tech.upper()}:{Colors.RESET}")
                        self._show_jobs_compact(tech_jobs)
                except (KeyboardInterrupt, EOFError):
                    break
        
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _show_jobs_by_date(self) -> None:
        """Mostra vagas agrupadas por data de coleta"""
        print(f"\n{Colors.CYAN}📅 VAGAS POR DATA DE COLETA{Colors.RESET}")
        
        all_jobs = self._load_all_jobs()
        
        # Agrupar por data
        dates = {}
        for job in all_jobs:
            date = job.get('_data_arquivo', 'Data desconhecida')
            if date not in dates:
                dates[date] = []
            dates[date].append(job)
        
        # Ordenar por data (mais recente primeiro)
        try:
            sorted_dates = sorted(dates.items(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y") if x[0] != 'Data desconhecida' else datetime.min, reverse=True)
        except:
            sorted_dates = sorted(dates.items(), reverse=True)
        
        print(f"\n{Colors.GREEN}📊 Vagas coletadas em {len(sorted_dates)} datas diferentes{Colors.RESET}")
        
        for date, date_jobs in sorted_dates:
            print(f"\n{Colors.YELLOW}📅 {date}{Colors.RESET} ({len(date_jobs)} vagas)")
            
            # Estatísticas da data
            companies = set(job.get('empresa', 'N/A') for job in date_jobs)
            print(f"     🏢 {len(companies)} empresas diferentes")
            
            # Tecnologias mais comuns nesta data
            all_techs = []
            for job in date_jobs:
                all_techs.extend(job.get('tecnologias_detectadas', []))
            
            if all_techs:
                from collections import Counter
                top_techs = Counter(all_techs).most_common(3)
                tech_names = [tech for tech, count in top_techs]
                print(f"     💻 Top tecnologias: {', '.join(tech_names)}")
        
        input(f"\n{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _export_selected_jobs(self) -> None:
        """Exporta vagas selecionadas"""
        print(f"\n{Colors.CYAN}🔗 EXPORTAR VAGAS{Colors.RESET}")
        print("Esta funcionalidade será implementada em breve!")
        input(f"{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")
    
    async def _manage_data_files(self) -> None:
        """Gerencia arquivos de dados"""
        print(f"\n{Colors.CYAN}🧹 GERENCIAR ARQUIVOS{Colors.RESET}")
        print("Esta funcionalidade será implementada em breve!")
        input(f"{Colors.GRAY}Pressione Enter para continuar...{Colors.RESET}")


# Função para usar no menu principal
async def show_jobs_viewer():
    """Função principal do visualizador de vagas"""
    viewer = JobsViewer()
    await viewer.show_jobs_dashboard()