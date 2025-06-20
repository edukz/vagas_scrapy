"""
Interface para Análise de Currículos
====================================

Interface de linha de comando para análise de currículos
e geração de recomendações personalizadas
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from ..ml.models.cv_analyzer import CVAnalyzer, CVAnalysisResult
from ..ml.models.job_recommender import JobRecommender
from .colors import Colors


class CVInterface:
    """Interface para análise de currículos e recomendações"""
    
    def __init__(self):
        self.analyzer = CVAnalyzer()
        self.colors = Colors()
        self.results_dir = Path("data/cv_analysis")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def show_main_menu(self):
        """Exibe menu principal da análise de CV"""
        while True:
            self._clear_screen()
            self._print_header()
            
            options = [
                "1. 📄 Analisar Novo Currículo",
                "2. 📋 Ver Análises Salvas", 
                "3. 🎯 Gerar Recomendações",
                "4. 📊 Estatísticas de Perfil",
                "5. ⚙️ Configurações",
                "0. ⬅️ Voltar ao Menu Principal"
            ]
            
            for option in options:
                print(f"   {option}")
            
            print()
            choice = input(f"{self.colors.BLUE}Escolha uma opção: {self.colors.RESET}")
            
            if choice == "1":
                self._analyze_new_cv()
            elif choice == "2":
                self._view_saved_analyses()
            elif choice == "3":
                self._generate_recommendations_menu()
            elif choice == "4":
                self._show_profile_statistics()
            elif choice == "5":
                self._show_settings()
            elif choice == "0":
                break
            else:
                input(f"{self.colors.RED}Opção inválida! Pressione Enter...{self.colors.RESET}")
    
    def _print_header(self):
        """Imprime cabeçalho da interface"""
        print(f"""
{self.colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    🤖 ANÁLISE DE CURRÍCULO                   ║
║              Inteligência Artificial para CVs               ║
╚══════════════════════════════════════════════════════════════╝{self.colors.RESET}

{self.colors.YELLOW}💡 Funcionalidades:{self.colors.RESET}
   • Extração automática de habilidades técnicas
   • Análise de experiência profissional
   • Determinação de nível de senioridade
   • Estimativa de faixa salarial
   • Geração de perfil para recomendações
   • Suporte a PDF, DOCX e TXT

""")
    
    def _analyze_new_cv(self):
        """Analisa um novo currículo"""
        self._clear_screen()
        print(f"{self.colors.CYAN}📄 ANÁLISE DE NOVO CURRÍCULO{self.colors.RESET}")
        print("═" * 50)
        
        # Solicitar arquivo
        file_path = input(f"\n{self.colors.BLUE}Caminho do arquivo (PDF/DOCX/TXT): {self.colors.RESET}")
        
        if not file_path or not Path(file_path).exists():
            print(f"{self.colors.RED}❌ Arquivo não encontrado!{self.colors.RESET}")
            input("Pressione Enter para continuar...")
            return
        
        # Solicitar ID do usuário
        user_id = input(f"{self.colors.BLUE}ID do usuário (opcional): {self.colors.RESET}").strip()
        if not user_id:
            user_id = f"user_{hash(file_path)}_{len(os.listdir(self.results_dir))}"
        
        try:
            print(f"\n{self.colors.YELLOW}🔄 Analisando currículo...{self.colors.RESET}")
            
            # Realizar análise
            result = self.analyzer.analyze_cv(file_path, user_id)
            
            # Salvar resultado
            output_file = self.results_dir / f"{user_id}_analysis.json"
            self.analyzer.save_analysis(result, str(output_file))
            
            # Exibir resultado
            self._display_analysis_result(result)
            
            print(f"\n{self.colors.GREEN}✅ Análise concluída e salva!{self.colors.RESET}")
            
        except Exception as e:
            print(f"{self.colors.RED}❌ Erro na análise: {e}{self.colors.RESET}")
        
        input("\nPressione Enter para continuar...")
    
    def _display_analysis_result(self, result: CVAnalysisResult):
        """Exibe resultado da análise"""
        print(f"\n{self.colors.GREEN}📊 RESULTADO DA ANÁLISE{self.colors.RESET}")
        print("═" * 40)
        
        # Informações pessoais
        print(f"\n{self.colors.CYAN}👤 Informações Pessoais:{self.colors.RESET}")
        print(f"   Nome: {result.personal_info.get('name', 'N/A')}")
        print(f"   Email: {result.personal_info.get('email', 'N/A')}")
        print(f"   Telefone: {result.personal_info.get('phone', 'N/A')}")
        print(f"   Localização: {result.personal_info.get('location', 'N/A')}")
        
        if result.personal_info.get('linkedin'):
            print(f"   LinkedIn: {result.personal_info['linkedin']}")
        if result.personal_info.get('github'):
            print(f"   GitHub: {result.personal_info['github']}")
        
        # Experiência
        print(f"\n{self.colors.CYAN}💼 Experiência Profissional:{self.colors.RESET}")
        print(f"   Anos de experiência: {result.experience['total_years']}")
        print(f"   Nível de senioridade: {self.colors.YELLOW}{result.seniority_level.title()}{self.colors.RESET}")
        print(f"   Posição atual: {result.experience.get('current_position', 'N/A')}")
        
        if result.experience.get('companies'):
            print(f"   Empresas: {', '.join(result.experience['companies'][:3])}")
        
        # Habilidades técnicas
        print(f"\n{self.colors.CYAN}🛠️ Habilidades Técnicas:{self.colors.RESET}")
        tech_skills = result.skills.get('technical', [])
        if tech_skills:
            print(f"   Total encontradas: {len(tech_skills)}")
            print(f"   Principais: {', '.join(tech_skills[:10])}")
            
            # Por categoria
            for category, skills in result.skills.get('by_category', {}).items():
                if skills:
                    print(f"   {category.replace('_', ' ').title()}: {', '.join(skills[:5])}")
        else:
            print("   Nenhuma habilidade técnica detectada")
        
        # Soft skills
        soft_skills = result.skills.get('soft', [])
        if soft_skills:
            print(f"\n{self.colors.CYAN}🧠 Soft Skills:{self.colors.RESET}")
            print(f"   {', '.join(soft_skills[:8])}")
        
        # Educação
        if result.education.get('degree'):
            print(f"\n{self.colors.CYAN}🎓 Educação:{self.colors.RESET}")
            print(f"   Formação: {result.education['degree']}")
            if result.education.get('institution'):
                print(f"   Instituição: {result.education['institution']}")
            if result.education.get('graduation_year'):
                print(f"   Ano de formação: {result.education['graduation_year']}")
        
        # Estimativa salarial
        print(f"\n{self.colors.CYAN}💰 Faixa Salarial Estimada:{self.colors.RESET}")
        salary = result.estimated_salary_range
        print(f"   R$ {salary['min']:,.0f} - R$ {salary['max']:,.0f}")
        print(f"   Mediana: R$ {salary['median']:,.0f}")
        
        # Confiança
        confidence_color = self.colors.GREEN if result.confidence_score > 0.7 else \
                          self.colors.YELLOW if result.confidence_score > 0.5 else self.colors.RED
        
        print(f"\n{self.colors.CYAN}📈 Confiança da Análise:{self.colors.RESET}")
        print(f"   {confidence_color}{result.confidence_score:.1%}{self.colors.RESET}")
    
    def _view_saved_analyses(self):
        """Visualiza análises salvas"""
        self._clear_screen()
        print(f"{self.colors.CYAN}📋 ANÁLISES SALVAS{self.colors.RESET}")
        print("═" * 30)
        
        # Listar arquivos de análise
        analysis_files = list(self.results_dir.glob("*_analysis.json"))
        
        if not analysis_files:
            print(f"\n{self.colors.YELLOW}📁 Nenhuma análise salva encontrada{self.colors.RESET}")
            input("Pressione Enter para continuar...")
            return
        
        print(f"\n{self.colors.GREEN}Encontradas {len(analysis_files)} análises:{self.colors.RESET}")
        
        for i, file_path in enumerate(analysis_files, 1):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                name = data.get('personal_info', {}).get('name', 'N/A')
                seniority = data.get('seniority_level', 'N/A')
                confidence = data.get('confidence_score', 0)
                
                print(f"   {i}. {name} - {seniority.title()} ({confidence:.1%} confiança)")
                print(f"      Arquivo: {file_path.name}")
                
            except Exception as e:
                print(f"   {i}. Erro ao ler {file_path.name}: {e}")
        
        print(f"\n{self.colors.BLUE}Digite o número para ver detalhes (0 para voltar): {self.colors.RESET}", end="")
        choice = input()
        
        try:
            choice_num = int(choice)
            if choice_num == 0:
                return
            elif 1 <= choice_num <= len(analysis_files):
                self._view_analysis_details(analysis_files[choice_num - 1])
            else:
                print(f"{self.colors.RED}Número inválido!{self.colors.RESET}")
        except ValueError:
            print(f"{self.colors.RED}Por favor, digite um número válido!{self.colors.RESET}")
        
        input("Pressione Enter para continuar...")
    
    def _view_analysis_details(self, file_path: Path):
        """Visualiza detalhes de uma análise específica"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruir objeto CVAnalysisResult
            # (simplificado para visualização)
            
            self._clear_screen()
            print(f"{self.colors.CYAN}📄 DETALHES DA ANÁLISE{self.colors.RESET}")
            print("═" * 35)
            
            # Exibir informações principais
            print(f"\n{self.colors.YELLOW}Arquivo:{self.colors.RESET} {file_path.name}")
            
            personal_info = data.get('personal_info', {})
            skills = data.get('skills', {})
            experience = data.get('experience', {})
            
            print(f"{self.colors.YELLOW}Nome:{self.colors.RESET} {personal_info.get('name', 'N/A')}")
            print(f"{self.colors.YELLOW}Senioridade:{self.colors.RESET} {data.get('seniority_level', 'N/A').title()}")
            print(f"{self.colors.YELLOW}Experiência:{self.colors.RESET} {experience.get('total_years', 0)} anos")
            
            tech_skills = skills.get('technical', [])
            if tech_skills:
                print(f"{self.colors.YELLOW}Tecnologias:{self.colors.RESET} {', '.join(tech_skills[:10])}")
            
            salary = data.get('estimated_salary_range', {})
            if salary:
                print(f"{self.colors.YELLOW}Salário estimado:{self.colors.RESET} R$ {salary.get('min', 0):,.0f} - R$ {salary.get('max', 0):,.0f}")
            
            confidence = data.get('confidence_score', 0)
            print(f"{self.colors.YELLOW}Confiança:{self.colors.RESET} {confidence:.1%}")
            
        except Exception as e:
            print(f"{self.colors.RED}Erro ao carregar análise: {e}{self.colors.RESET}")
    
    def _generate_recommendations_menu(self):
        """Menu para gerar recomendações baseadas no CV"""
        self._clear_screen()
        print(f"{self.colors.CYAN}🎯 GERAR RECOMENDAÇÕES{self.colors.RESET}")
        print("═" * 35)
        
        # Listar análises disponíveis
        analysis_files = list(self.results_dir.glob("*_analysis.json"))
        
        if not analysis_files:
            print(f"\n{self.colors.YELLOW}📁 Nenhuma análise encontrada. Analise um currículo primeiro.{self.colors.RESET}")
            input("Pressione Enter para continuar...")
            return
        
        print(f"\n{self.colors.GREEN}Selecione uma análise para gerar recomendações:{self.colors.RESET}")
        
        for i, file_path in enumerate(analysis_files, 1):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name = data.get('personal_info', {}).get('name', 'N/A')
                print(f"   {i}. {name}")
            except:
                print(f"   {i}. {file_path.name}")
        
        print(f"\n{self.colors.BLUE}Digite o número (0 para voltar): {self.colors.RESET}", end="")
        choice = input()
        
        try:
            choice_num = int(choice)
            if choice_num == 0:
                return
            elif 1 <= choice_num <= len(analysis_files):
                self._generate_recommendations(analysis_files[choice_num - 1])
            else:
                print(f"{self.colors.RED}Número inválido!{self.colors.RESET}")
                input("Pressione Enter...")
        except ValueError:
            print(f"{self.colors.RED}Por favor, digite um número válido!{self.colors.RESET}")
            input("Pressione Enter...")
    
    def _generate_recommendations(self, analysis_file: Path):
        """Gera recomendações baseadas na análise"""
        try:
            print(f"\n{self.colors.YELLOW}🔄 Carregando análise e gerando recomendações...{self.colors.RESET}")
            
            # Carregar análise
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Simular algumas vagas para demonstração
            sample_jobs = self._get_sample_jobs()
            
            print(f"\n{self.colors.GREEN}🎯 RECOMENDAÇÕES PERSONALIZADAS{self.colors.RESET}")
            print("═" * 45)
            
            # Exibir informações do perfil
            name = data.get('personal_info', {}).get('name', 'Usuário')
            seniority = data.get('seniority_level', 'pleno')
            tech_skills = data.get('skills', {}).get('technical', [])
            
            print(f"\n{self.colors.CYAN}👤 Perfil: {name} ({seniority.title()}){self.colors.RESET}")
            print(f"{self.colors.CYAN}🛠️ Skills: {', '.join(tech_skills[:5])}{self.colors.RESET}")
            
            print(f"\n{self.colors.YELLOW}📋 Top 5 vagas recomendadas:{self.colors.RESET}")
            
            # Simular scores de compatibilidade
            for i, job in enumerate(sample_jobs[:5], 1):
                # Calcular score simples baseado em overlap de skills
                job_skills = job.get('tecnologias_detectadas', [])
                overlap = len(set(tech_skills) & set(job_skills))
                score = min(95, 60 + overlap * 8)  # Score simulado
                
                score_color = self.colors.GREEN if score > 80 else \
                             self.colors.YELLOW if score > 60 else self.colors.RED
                
                print(f"\n   {i}. {self.colors.BOLD}{job['titulo']}{self.colors.RESET}")
                print(f"      🏢 {job['empresa']}")
                print(f"      📍 {job.get('localizacao', 'N/A')}")
                print(f"      🎯 Compatibilidade: {score_color}{score}%{self.colors.RESET}")
                
                if job_skills:
                    common_skills = list(set(tech_skills) & set(job_skills))
                    if common_skills:
                        print(f"      ✅ Skills em comum: {', '.join(common_skills[:3])}")
            
            print(f"\n{self.colors.GREEN}✨ Recomendações geradas com base no seu perfil!{self.colors.RESET}")
            
        except Exception as e:
            print(f"{self.colors.RED}❌ Erro ao gerar recomendações: {e}{self.colors.RESET}")
        
        input("\nPressione Enter para continuar...")
    
    def _get_sample_jobs(self) -> List[Dict]:
        """Retorna vagas de exemplo para demonstração"""
        return [
            {
                'titulo': 'Desenvolvedor Python Sênior',
                'empresa': 'TechCorp',
                'localizacao': 'São Paulo - SP (Remoto)',
                'tecnologias_detectadas': ['Python', 'Django', 'AWS', 'PostgreSQL', 'Docker']
            },
            {
                'titulo': 'Full Stack Developer',
                'empresa': 'StartupXYZ',
                'localizacao': 'Rio de Janeiro - RJ',
                'tecnologias_detectadas': ['React', 'Node.js', 'MongoDB', 'TypeScript']
            },
            {
                'titulo': 'Engenheiro de Dados',
                'empresa': 'DataCorp',
                'localizacao': 'Remoto',
                'tecnologias_detectadas': ['Python', 'Spark', 'Kafka', 'AWS', 'Airflow']
            },
            {
                'titulo': 'DevOps Engineer',
                'empresa': 'CloudTech',
                'localizacao': 'Belo Horizonte - MG',
                'tecnologias_detectadas': ['Docker', 'Kubernetes', 'Terraform', 'AWS', 'Jenkins']
            },
            {
                'titulo': 'Arquiteto de Software',
                'empresa': 'Enterprise Solutions',
                'localizacao': 'São Paulo - SP',
                'tecnologias_detectadas': ['Java', 'Spring', 'Microservices', 'Kafka', 'Redis']
            }
        ]
    
    def _show_profile_statistics(self):
        """Exibe estatísticas dos perfis analisados"""
        self._clear_screen()
        print(f"{self.colors.CYAN}📊 ESTATÍSTICAS DE PERFIS{self.colors.RESET}")
        print("═" * 40)
        
        analysis_files = list(self.results_dir.glob("*_analysis.json"))
        
        if not analysis_files:
            print(f"\n{self.colors.YELLOW}📁 Nenhuma análise encontrada{self.colors.RESET}")
            input("Pressione Enter para continuar...")
            return
        
        # Coletar estatísticas
        seniority_counts = {}
        tech_counts = {}
        confidence_scores = []
        
        for file_path in analysis_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Senioridade
                seniority = data.get('seniority_level', 'N/A')
                seniority_counts[seniority] = seniority_counts.get(seniority, 0) + 1
                
                # Tecnologias
                tech_skills = data.get('skills', {}).get('technical', [])
                for tech in tech_skills:
                    tech_counts[tech] = tech_counts.get(tech, 0) + 1
                
                # Confiança
                confidence = data.get('confidence_score', 0)
                confidence_scores.append(confidence)
                
            except Exception:
                continue
        
        print(f"\n{self.colors.GREEN}📈 Resumo de {len(analysis_files)} perfis analisados:{self.colors.RESET}")
        
        # Distribuição por senioridade
        print(f"\n{self.colors.CYAN}🎯 Distribuição por Senioridade:{self.colors.RESET}")
        for level, count in sorted(seniority_counts.items()):
            percentage = (count / len(analysis_files)) * 100
            print(f"   {level.title()}: {count} ({percentage:.1f}%)")
        
        # Top tecnologias
        if tech_counts:
            print(f"\n{self.colors.CYAN}🛠️ Top 10 Tecnologias Mais Comuns:{self.colors.RESET}")
            sorted_techs = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)
            for tech, count in sorted_techs[:10]:
                print(f"   {tech}: {count} perfis")
        
        # Confiança média
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            print(f"\n{self.colors.CYAN}📊 Confiança Média das Análises:{self.colors.RESET}")
            print(f"   {avg_confidence:.1%}")
        
        input("\nPressione Enter para continuar...")
    
    def _show_settings(self):
        """Exibe configurações do analisador"""
        self._clear_screen()
        print(f"{self.colors.CYAN}⚙️ CONFIGURAÇÕES{self.colors.RESET}")
        print("═" * 25)
        
        print(f"\n{self.colors.YELLOW}📁 Diretórios:{self.colors.RESET}")
        print(f"   Análises salvas: {self.results_dir}")
        
        print(f"\n{self.colors.YELLOW}🔧 Formatos suportados:{self.colors.RESET}")
        print("   • PDF (.pdf)")
        print("   • Word (.docx, .doc)")
        print("   • Texto (.txt)")
        
        print(f"\n{self.colors.YELLOW}🧠 Tecnologias detectadas:{self.colors.RESET}")
        total_techs = len(self.analyzer.all_technologies)
        print(f"   Total: {total_techs} tecnologias")
        
        categories = list(self.analyzer.tech_categories.keys())
        print(f"   Categorias: {', '.join(categories)}")
        
        print(f"\n{self.colors.YELLOW}💡 Soft Skills detectadas:{self.colors.RESET}")
        print(f"   Total: {len(self.analyzer.soft_skills)} habilidades")
        
        input("\nPressione Enter para continuar...")
    
    def _clear_screen(self):
        """Limpa a tela"""
        os.system('cls' if os.name == 'nt' else 'clear')


# Função para integração com o menu principal
def run_cv_interface():
    """Executa a interface de análise de CV"""
    interface = CVInterface()
    interface.show_main_menu()


if __name__ == "__main__":
    run_cv_interface()