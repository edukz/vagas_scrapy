"""
Handler para Sistema Integrado de Recomendações CV-Vagas
========================================================

Interface que integra análise de CV com recomendações personalizadas
de vagas usando Machine Learning e feedback do usuário.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..utils.menu_system import MenuSystem, Colors


class RecommendationHandler:
    """
    Handler para sistema integrado de recomendações
    
    Funcionalidades:
    - Análise de CV com recomendações automáticas
    - Sistema de feedback e aprendizado
    - Recomendações personalizadas
    - Interface interativa para matching
    """
    
    def __init__(self):
        self.menu = MenuSystem()
        self.colors = Colors()
        
        # Lazy loading dos sistemas
        self._matcher_loaded = False
        self._feedback_loaded = False
        self.matcher = None
        self.feedback_system = None
        
        # Dados de sessão
        self.current_user_id = None
        self.current_jobs = []
        self.last_recommendations = []
    
    def _ensure_systems_loaded(self):
        """Carrega sistemas de ML apenas quando necessário"""
        if not self._matcher_loaded:
            try:
                from src.ml.cv_job_matcher import cv_job_matcher
                self.matcher = cv_job_matcher
                self._matcher_loaded = True
                print(f"{self.colors.GREEN}✅ Sistema de matching carregado{self.colors.RESET}")
            except ImportError as e:
                print(f"{self.colors.RED}❌ Erro ao carregar matcher: {e}{self.colors.RESET}")
                return False
        
        if not self._feedback_loaded:
            try:
                from src.ml.user_feedback_system import user_feedback_system
                self.feedback_system = user_feedback_system
                self._feedback_loaded = True
                print(f"{self.colors.GREEN}✅ Sistema de feedback carregado{self.colors.RESET}")
            except ImportError as e:
                print(f"{self.colors.RED}❌ Erro ao carregar feedback: {e}{self.colors.RESET}")
                return False
        
        return True
    
    def _load_available_jobs(self) -> List[Dict]:
        """Carrega vagas disponíveis dos resultados de scraping"""
        jobs = []
        
        # Procurar arquivos de resultados mais recentes
        results_dir = Path("data/resultados/json")
        if results_dir.exists():
            json_files = list(results_dir.glob("*.json"))
            if json_files:
                # Pegar arquivo mais recente
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        jobs = data.get('vagas', [])
                        print(f"{self.colors.CYAN}📂 Carregadas {len(jobs)} vagas de {latest_file.name}{self.colors.RESET}")
                except Exception as e:
                    print(f"{self.colors.YELLOW}⚠️ Erro ao carregar vagas: {e}{self.colors.RESET}")
        
        # Se não há vagas reais, usar vagas de exemplo
        if not jobs:
            jobs = self._get_sample_jobs()
            print(f"{self.colors.YELLOW}📋 Usando {len(jobs)} vagas de exemplo{self.colors.RESET}")
        
        return jobs
    
    def _get_sample_jobs(self) -> List[Dict]:
        """Retorna vagas de exemplo para demonstração"""
        return [
            {
                'id': 'job_001',
                'titulo': 'Desenvolvedor Python Sênior',
                'empresa': 'TechCorp Brasil',
                'localizacao': 'São Paulo - SP (Remoto)',
                'salario': 'R$ 12.000 - R$ 18.000',
                'descricao': 'Desenvolvedor Python experiente para trabalhar com Django, FastAPI, PostgreSQL e AWS',
                'requisitos': 'Python, Django, FastAPI, PostgreSQL, AWS, Docker, 5+ anos experiência',
                'tecnologias_detectadas': ['python', 'django', 'fastapi', 'postgresql', 'aws', 'docker'],
                'nivel_categorizado': 'senior',
                'data_coleta': datetime.now().isoformat()
            },
            {
                'id': 'job_002', 
                'titulo': 'Analista de Dados Pleno',
                'empresa': 'DataCorp Analytics',
                'localizacao': 'Rio de Janeiro - RJ',
                'salario': 'R$ 8.000 - R$ 12.000',
                'descricao': 'Análise de dados com Python, pandas, SQL e Power BI',
                'requisitos': 'Python, pandas, SQL, Power BI, estatística, 3+ anos',
                'tecnologias_detectadas': ['python', 'pandas', 'sql', 'power bi', 'estatistica'],
                'nivel_categorizado': 'pleno',
                'data_coleta': datetime.now().isoformat()
            },
            {
                'id': 'job_003',
                'titulo': 'Engenheiro DevOps',
                'empresa': 'CloudTech Solutions',
                'localizacao': 'Belo Horizonte - MG (Híbrido)',
                'salario': 'R$ 15.000 - R$ 22.000',
                'descricao': 'DevOps engineer para automatização com Docker, Kubernetes, Terraform',
                'requisitos': 'Docker, Kubernetes, Terraform, AWS, Jenkins, Linux, 4+ anos',
                'tecnologias_detectadas': ['docker', 'kubernetes', 'terraform', 'aws', 'jenkins', 'linux'],
                'nivel_categorizado': 'senior',
                'data_coleta': datetime.now().isoformat()
            },
            {
                'id': 'job_004',
                'titulo': 'Desenvolvedor Full Stack Júnior',
                'empresa': 'StartupBR',
                'localizacao': 'Remoto',
                'salario': 'R$ 4.500 - R$ 7.000',
                'descricao': 'Desenvolvimento full stack com React, Node.js e MongoDB',
                'requisitos': 'React, Node.js, MongoDB, JavaScript, HTML, CSS, 1+ ano',
                'tecnologias_detectadas': ['react', 'nodejs', 'mongodb', 'javascript', 'html', 'css'],
                'nivel_categorizado': 'junior',
                'data_coleta': datetime.now().isoformat()
            },
            {
                'id': 'job_005',
                'titulo': 'Cientista de Dados',
                'empresa': 'AI Research Lab',
                'localizacao': 'São Paulo - SP',
                'salario': 'R$ 16.000 - R$ 25.000',
                'descricao': 'Machine Learning e Data Science com Python, TensorFlow, PyTorch',
                'requisitos': 'Python, TensorFlow, PyTorch, scikit-learn, pandas, numpy, estatística avançada',
                'tecnologias_detectadas': ['python', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy'],
                'nivel_categorizado': 'senior',
                'data_coleta': datetime.now().isoformat()
            }
        ]
    
    async def handle_recommendation_system(self):
        """Interface principal do sistema de recomendações"""
        try:
            if not self._ensure_systems_loaded():
                self.menu.print_error_message("Sistemas de ML não disponíveis")
                return
            
            while True:
                self._clear_screen()
                self._print_recommendation_header()
                
                options = [
                    "1. 🔍 Analisar CV e Obter Recomendações",
                    "2. 📋 Ver Recomendações Salvas",
                    "3. 👍 Dar Feedback sobre Vagas",
                    "4. 📊 Meu Perfil de Preferências",
                    "5. 🎯 Recomendações Personalizadas",
                    "6. 📈 Estatísticas do Sistema",
                    "0. ⬅️ Voltar ao Menu Principal"
                ]
                
                for option in options:
                    print(f"   {option}")
                
                print()
                choice = self._safe_input(f"{self.colors.BLUE}Escolha uma opção: {self.colors.RESET}")
                
                if choice == "1":
                    await self._analyze_cv_with_recommendations()
                elif choice == "2":
                    self._view_saved_recommendations()
                elif choice == "3":
                    self._feedback_interface()
                elif choice == "4":
                    self._show_user_profile()
                elif choice == "5":
                    self._personalized_recommendations()
                elif choice == "6":
                    self._show_system_statistics()
                elif choice == "0":
                    break
                else:
                    self.menu.print_error_message("Opção inválida!")
                    self._safe_input_continue()
                    
        except (KeyboardInterrupt, EOFError):
            print(f"\n{self.colors.YELLOW}👋 Saindo do sistema de recomendações...{self.colors.RESET}")
    
    def _print_recommendation_header(self):
        """Imprime cabeçalho do sistema de recomendações"""
        user_info = f"Usuário: {self.current_user_id}" if self.current_user_id else "Nenhum usuário ativo"
        jobs_info = f"Vagas carregadas: {len(self.current_jobs)}"
        
        print(f"""
{self.colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║               🤖 SISTEMA DE RECOMENDAÇÕES CV-VAGAS          ║
║                  Machine Learning Personalizado             ║  
╚══════════════════════════════════════════════════════════════╝{self.colors.RESET}

{self.colors.YELLOW}🚀 Funcionalidades Avançadas:{self.colors.RESET}
   • Matching semântico CV-Vagas com ML
   • Aprendizado baseado em suas interações
   • Recomendações personalizadas e explicáveis
   • Sistema de feedback inteligente

{self.colors.CYAN}📊 Status:{self.colors.RESET}
   • {user_info}
   • {jobs_info}
   • Sistema de ML: {'✅ Ativo' if self._matcher_loaded else '❌ Inativo'}
   • Feedback: {'✅ Ativo' if self._feedback_loaded else '❌ Inativo'}

""")
    
    async def _analyze_cv_with_recommendations(self):
        """Analisa CV e gera recomendações automáticas"""
        self._clear_screen()
        print(f"{self.colors.CYAN}🔍 ANÁLISE DE CV COM RECOMENDAÇÕES{self.colors.RESET}")
        print("=" * 50)
        
        # Selecionar CV
        cv_file = self._select_cv_file()
        if not cv_file:
            return
        
        # Solicitar ID do usuário
        user_id = self._safe_input(f"{self.colors.BLUE}ID do usuário (para personalização): {self.colors.RESET}")
        if not user_id:
            user_id = f"user_{hash(cv_file)}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        self.current_user_id = user_id
        
        try:
            print(f"\n{self.colors.YELLOW}🔄 Analisando CV...{self.colors.RESET}")
            
            # Analisar CV para matching
            cv_data = self.matcher.analyze_cv_for_matching(cv_file, user_id)
            
            print(f"{self.colors.GREEN}✅ CV analisado com sucesso!{self.colors.RESET}")
            
            # Carregar vagas disponíveis
            print(f"{self.colors.YELLOW}📂 Carregando vagas disponíveis...{self.colors.RESET}")
            self.current_jobs = self._load_available_jobs()
            
            # Gerar recomendações
            print(f"{self.colors.YELLOW}🎯 Gerando recomendações personalizadas...{self.colors.RESET}")
            recommendations = self.matcher.get_job_recommendations(
                user_id, self.current_jobs, top_n=10
            )
            
            self.last_recommendations = recommendations
            
            # Exibir resultados
            self._display_cv_analysis_summary(cv_data)
            self._display_recommendations(recommendations, user_id)
            
            # Salvar recomendações
            self._save_recommendations(user_id, cv_data, recommendations)
            
        except Exception as e:
            self.menu.print_error_message(f"Erro na análise: {e}")
        
        self._safe_input_continue()
    
    def _select_cv_file(self) -> Optional[str]:
        """Interface para seleção de arquivo de CV"""
        cv_dir = Path("data/cv_input")
        if not cv_dir.exists():
            self.menu.print_error_message("Diretório de CVs não encontrado: data/cv_input/")
            return None
        
        cv_files = list(cv_dir.glob("*.*"))
        if not cv_files:
            self.menu.print_error_message("Nenhum CV encontrado em data/cv_input/")
            return None
        
        print(f"\n{self.colors.CYAN}📂 CVs disponíveis:{self.colors.RESET}")
        for i, file_path in enumerate(cv_files, 1):
            print(f"   {i}. {file_path.name}")
        
        choice = self._safe_input(f"\n{self.colors.BLUE}Escolha o CV (1-{len(cv_files)}): {self.colors.RESET}")
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(cv_files):
                return str(cv_files[choice_num - 1])
        except ValueError:
            pass
        
        self.menu.print_error_message("Seleção inválida!")
        return None
    
    def _display_cv_analysis_summary(self, cv_data: Dict):
        """Exibe resumo da análise do CV"""
        print(f"\n{self.colors.GREEN}📊 RESUMO DA ANÁLISE DO CV{self.colors.RESET}")
        print("=" * 40)
        
        personal_info = cv_data.get('personal_info', {})
        skills = cv_data.get('skills', {})
        
        print(f"\n{self.colors.CYAN}👤 Perfil:{self.colors.RESET}")
        print(f"   Nome: {personal_info.get('name', 'N/A')}")
        print(f"   Senioridade: {cv_data.get('seniority', 'N/A').title()}")
        
        technical_skills = skills.get('technical', [])
        if technical_skills:
            print(f"   Skills técnicas: {len(technical_skills)} identificadas")
            print(f"   Principais: {', '.join(technical_skills[:8])}")
        
        salary_range = cv_data.get('salary_range', {})
        if salary_range:
            print(f"   Faixa salarial: R$ {salary_range.get('min', 0):,.0f} - R$ {salary_range.get('max', 0):,.0f}")
        
        print(f"   Confiança: {cv_data.get('confidence', 0):.1%}")
    
    def _display_recommendations(self, recommendations: List, user_id: str):
        """Exibe recomendações de vagas"""
        print(f"\n{self.colors.GREEN}🎯 TOP RECOMENDAÇÕES PERSONALIZADAS{self.colors.RESET}")
        print("=" * 50)
        
        if not recommendations:
            print(f"{self.colors.YELLOW}Nenhuma recomendação encontrada{self.colors.RESET}")
            return
        
        for i, rec in enumerate(recommendations[:5], 1):
            # Cor baseada no score
            if rec.overall_score >= 0.8:
                score_color = self.colors.GREEN
            elif rec.overall_score >= 0.6:
                score_color = self.colors.YELLOW
            else:
                score_color = self.colors.RED
            
            print(f"\n{i}. {self.colors.BOLD}{rec.job_title}{self.colors.RESET}")
            print(f"   🏢 {rec.company}")
            print(f"   🎯 Compatibilidade: {score_color}{rec.overall_score:.1%}{self.colors.RESET}")
            
            # Skills em comum
            if rec.matched_skills:
                print(f"   ✅ Skills compatíveis: {', '.join(rec.matched_skills[:5])}")
            
            # Skills para aprender
            if rec.missing_skills:
                print(f"   📚 Oportunidade de aprender: {', '.join(rec.missing_skills[:3])}")
            
            # Explicação personalizada se disponível
            if self.feedback_system:
                explanation = self.feedback_system.get_recommendation_explanation(
                    user_id, {'job_id': rec.job_id}, 0.5, rec.overall_score
                )
                print(f"   💡 {explanation}")
            
            print(f"   💰 Compatibilidade salarial: {rec.salary_compatibility:.1%}")
        
        # Oferecer análise detalhada
        print(f"\n{self.colors.CYAN}💡 Quer ver análise detalhada de uma recomendação?{self.colors.RESET}")
        choice = self._safe_input(f"{self.colors.BLUE}Digite o número da vaga (1-{len(recommendations[:5])}) ou Enter para continuar: {self.colors.RESET}")
        
        if choice and choice.isdigit():
            rec_idx = int(choice) - 1
            if 0 <= rec_idx < len(recommendations[:5]):
                self._show_detailed_analysis(recommendations[rec_idx], user_id)
    
    def _feedback_interface(self):
        """Interface para feedback sobre recomendações"""
        self._clear_screen()
        print(f"{self.colors.CYAN}👍 FEEDBACK SOBRE VAGAS{self.colors.RESET}")
        print("=" * 35)
        
        if not self.last_recommendations:
            print(f"\n{self.colors.YELLOW}Nenhuma recomendação disponível para feedback{self.colors.RESET}")
            print("Faça uma análise de CV primeiro para obter recomendações")
            self._safe_input_continue()
            return
        
        if not self.current_user_id:
            print(f"\n{self.colors.YELLOW}Nenhum usuário ativo{self.colors.RESET}")
            self._safe_input_continue()
            return
        
        # Mostrar recomendações para feedback
        print(f"\n{self.colors.GREEN}Recomendações recentes para {self.current_user_id}:{self.colors.RESET}")
        
        for i, rec in enumerate(self.last_recommendations[:5], 1):
            print(f"\n{i}. {rec.job_title} - {rec.company}")
            print(f"   Compatibilidade: {rec.overall_score:.1%}")
        
        print(f"\n{self.colors.BLUE}Tipos de feedback:{self.colors.RESET}")
        print("   👁️ view - Visualizou a vaga")
        print("   👍 like - Gostou da vaga")
        print("   👎 dislike - Não gostou")
        print("   📝 apply - Se candidatou")
        print("   🎤 interview - Foi chamado para entrevista")
        print("   ✅ hired - Foi contratado")
        
        # Solicitar feedback
        job_choice = self._safe_input(f"\n{self.colors.BLUE}Escolha a vaga (1-{len(self.last_recommendations[:5])}): {self.colors.RESET}")
        
        try:
            job_idx = int(job_choice) - 1
            if 0 <= job_idx < len(self.last_recommendations):
                selected_rec = self.last_recommendations[job_idx]
                
                feedback_type = self._safe_input(f"{self.colors.BLUE}Tipo de feedback: {self.colors.RESET}")
                
                if feedback_type in ['view', 'like', 'dislike', 'apply', 'interview', 'hired']:
                    # Buscar dados completos da vaga
                    job_data = next(
                        (job for job in self.current_jobs if job.get('id') == selected_rec.job_id),
                        {'job_id': selected_rec.job_id, 'title': selected_rec.job_title}
                    )
                    
                    # Registrar feedback
                    self.feedback_system.record_interaction(
                        self.current_user_id,
                        job_data,
                        feedback_type,
                        selected_rec.overall_score,
                        selected_rec.matched_skills
                    )
                    
                    print(f"\n{self.colors.GREEN}✅ Feedback registrado! O sistema aprenderá com sua escolha.{self.colors.RESET}")
                else:
                    print(f"\n{self.colors.RED}Tipo de feedback inválido{self.colors.RESET}")
            else:
                print(f"\n{self.colors.RED}Seleção inválida{self.colors.RESET}")
                
        except ValueError:
            print(f"\n{self.colors.RED}Por favor, digite um número válido{self.colors.RESET}")
        
        self._safe_input_continue()
    
    def _show_user_profile(self):
        """Mostra perfil de preferências aprendidas do usuário"""
        self._clear_screen()
        print(f"{self.colors.CYAN}📊 PERFIL DE PREFERÊNCIAS{self.colors.RESET}")
        print("=" * 40)
        
        if not self.current_user_id:
            print(f"\n{self.colors.YELLOW}Nenhum usuário ativo{self.colors.RESET}")
            self._safe_input_continue()
            return
        
        # Analisar comportamento do usuário
        behavior_analysis = self.feedback_system.analyze_user_behavior(self.current_user_id)
        
        if behavior_analysis['status'] == 'insufficient_data':
            print(f"\n{self.colors.YELLOW}Dados insuficientes para análise de perfil{self.colors.RESET}")
            print("Interaja com mais recomendações para que o sistema aprenda suas preferências")
            self._safe_input_continue()
            return
        
        print(f"\n{self.colors.GREEN}📈 Análise comportamental para {self.current_user_id}:{self.colors.RESET}")
        print(f"   Total de interações: {behavior_analysis['total_interactions']}")
        print(f"   Taxa de conversão: {behavior_analysis['conversion_rate']:.1%}")
        print(f"   Score médio de compatibilidade: {behavior_analysis['avg_match_score']:.1%}")
        
        # Breakdown de interações
        if behavior_analysis['interaction_breakdown']:
            print(f"\n{self.colors.CYAN}💬 Tipos de interação:{self.colors.RESET}")
            for interaction_type, count in behavior_analysis['interaction_breakdown'].items():
                emoji = {'view': '👁️', 'like': '👍', 'dislike': '👎', 'apply': '📝'}.get(interaction_type, '📌')
                print(f"   {emoji} {interaction_type}: {count}")
        
        # Skills populares
        if behavior_analysis['popular_skills']:
            print(f"\n{self.colors.CYAN}🛠️ Skills mais interagidas:{self.colors.RESET}")
            for skill, count in behavior_analysis['popular_skills']:
                print(f"   • {skill}: {count} vezes")
        
        # Preferências aprendidas
        preferences = self.feedback_system.get_user_preferences(self.current_user_id)
        if preferences:
            print(f"\n{self.colors.CYAN}🎯 Preferências aprendidas:{self.colors.RESET}")
            print(f"   Confiança do aprendizado: {preferences.learning_confidence:.1%}")
            
            if preferences.preferred_skills:
                top_skills = sorted(
                    preferences.preferred_skills.items(), 
                    key=lambda x: x[1], reverse=True
                )[:5]
                print(f"   Skills preferidas: {', '.join([skill for skill, score in top_skills])}")
        
        # Período de atividade
        activity = behavior_analysis.get('activity_period', {})
        if activity:
            print(f"\n{self.colors.CYAN}📅 Período de atividade:{self.colors.RESET}")
            print(f"   Primeira interação: {activity.get('first_interaction', 'N/A')[:10]}")
            print(f"   Última interação: {activity.get('last_interaction', 'N/A')[:10]}")
            print(f"   Dias ativo: {activity.get('days_active', 0)}")
        
        self._safe_input_continue()
    
    def _personalized_recommendations(self):
        """Gera recomendações personalizadas baseadas no perfil"""
        self._clear_screen()
        print(f"{self.colors.CYAN}🎯 RECOMENDAÇÕES PERSONALIZADAS{self.colors.RESET}")
        print("=" * 45)
        
        if not self.current_user_id:
            print(f"\n{self.colors.YELLOW}Nenhum usuário ativo{self.colors.RESET}")
            self._safe_input_continue()
            return
        
        # Verificar se há preferências aprendidas
        preferences = self.feedback_system.get_user_preferences(self.current_user_id)
        if not preferences or preferences.learning_confidence < 0.2:
            print(f"\n{self.colors.YELLOW}Sistema ainda aprendendo suas preferências{self.colors.RESET}")
            print("Interaja com mais recomendações para personalização avançada")
            self._safe_input_continue()
            return
        
        # Carregar vagas se necessário
        if not self.current_jobs:
            self.current_jobs = self._load_available_jobs()
        
        print(f"\n{self.colors.GREEN}🤖 Gerando recomendações com IA personalizada...{self.colors.RESET}")
        
        try:
            # Obter pesos ajustados para o usuário
            base_weights = self.matcher.weights.copy()
            adjusted_weights = self.feedback_system.adjust_matching_weights(
                self.current_user_id, base_weights
            )
            
            # Temporariamente usar pesos ajustados
            original_weights = self.matcher.weights.copy()
            self.matcher.weights = adjusted_weights
            
            # Gerar recomendações
            recommendations = self.matcher.get_job_recommendations(
                self.current_user_id, self.current_jobs, top_n=8
            )
            
            # Restaurar pesos originais
            self.matcher.weights = original_weights
            
            # Exibir recomendações personalizadas
            print(f"\n{self.colors.GREEN}🎆 RECOMENDAÇÕES ULTRA-PERSONALIZADAS{self.colors.RESET}")
            print(f"Baseadas em {preferences.learning_confidence:.1%} de confiança do seu perfil")
            print("=" * 55)
            
            for i, rec in enumerate(recommendations[:5], 1):
                # Calcular boost personalizado
                personal_boost = self.feedback_system.get_personalized_skill_boost(
                    self.current_user_id, rec.matched_skills
                )
                
                # Cor baseada no score + boost
                final_score = min(1.0, rec.overall_score + personal_boost)
                if final_score >= 0.8:
                    score_color = self.colors.GREEN
                elif final_score >= 0.6:
                    score_color = self.colors.YELLOW
                else:
                    score_color = self.colors.RED
                
                print(f"\n{i}. {self.colors.BOLD}{rec.job_title}{self.colors.RESET}")
                print(f"   🏢 {rec.company}")
                print(f"   🎯 Compatibilidade: {score_color}{final_score:.1%}{self.colors.RESET}")
                
                if personal_boost > 0.1:
                    print(f"   ⭐ Boost pessoal: +{personal_boost:.1%}")
                
                # Explicação personalizada
                explanation = self.feedback_system.get_recommendation_explanation(
                    self.current_user_id, 
                    {'job_id': rec.job_id, 'skills': rec.matched_skills},
                    rec.overall_score,
                    final_score
                )
                print(f"   💡 {explanation}")
                
                if rec.matched_skills:
                    print(f"   ✅ {', '.join(rec.matched_skills[:4])}")
            
            self.last_recommendations = recommendations
            
        except Exception as e:
            self.menu.print_error_message(f"Erro ao gerar recomendações: {e}")
        
        self._safe_input_continue()
    
    def _show_system_statistics(self):
        """Exibe estatísticas do sistema de ML"""
        self._clear_screen()
        print(f"{self.colors.CYAN}📈 ESTATÍSTICAS DO SISTEMA{self.colors.RESET}")
        print("=" * 40)
        
        # Estatísticas do matcher
        if self.matcher:
            matcher_stats = self.matcher.get_matching_statistics()
            print(f"\n{self.colors.GREEN}🎯 Sistema de Matching:{self.colors.RESET}")
            print(f"   CVs processados: {matcher_stats['cvs_processed']}")
            print(f"   Vagas processadas: {matcher_stats['jobs_processed']}")
            print(f"   Interações registradas: {matcher_stats['interactions_recorded']}")
        
        # Estatísticas do feedback
        if self.feedback_system:
            learning_stats = self.feedback_system.get_learning_stats()
            print(f"\n{self.colors.GREEN}🧠 Sistema de Aprendizado:{self.colors.RESET}")
            print(f"   Total de interações: {learning_stats['total_interactions']}")
            print(f"   Usuários com dados: {learning_stats['users_with_data']}")
            print(f"   Usuários com aprendizado confiável: {learning_stats['confident_users']}")
            print(f"   Efetividade do aprendizado: {learning_stats['learning_effectiveness']:.1%}")
            
            if learning_stats['interaction_breakdown']:
                print(f"\n{self.colors.CYAN}💬 Breakdown de interações:{self.colors.RESET}")
                for interaction_type, count in learning_stats['interaction_breakdown'].items():
                    print(f"   {interaction_type}: {count}")
        
        # Estatísticas das vagas
        print(f"\n{self.colors.GREEN}📊 Dados de Vagas:{self.colors.RESET}")
        print(f"   Vagas carregadas na sessão: {len(self.current_jobs)}")
        
        if self.current_jobs:
            # Análise das vagas carregadas
            tech_counts = {}
            seniority_counts = {}
            
            for job in self.current_jobs:
                # Contar tecnologias
                techs = job.get('tecnologias_detectadas', [])
                for tech in techs:
                    tech_counts[tech] = tech_counts.get(tech, 0) + 1
                
                # Contar senioridade
                seniority = job.get('nivel_categorizado', 'não classificado')
                seniority_counts[seniority] = seniority_counts.get(seniority, 0) + 1
            
            if tech_counts:
                print(f"\n{self.colors.CYAN}🛠️ Top 5 tecnologias nas vagas:{self.colors.RESET}")
                sorted_techs = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)
                for tech, count in sorted_techs[:5]:
                    print(f"   {tech}: {count} vagas")
            
            if seniority_counts:
                print(f"\n{self.colors.CYAN}📊 Distribuição por senioridade:{self.colors.RESET}")
                for seniority, count in sorted(seniority_counts.items()):
                    percentage = (count / len(self.current_jobs)) * 100
                    print(f"   {seniority.title()}: {count} ({percentage:.1f}%)")
        
        self._safe_input_continue()
    
    def _save_recommendations(self, user_id: str, cv_data: Dict, recommendations: List):
        """Salva recomendações para visualização posterior"""
        try:
            save_dir = Path("data/recommendations")
            save_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{user_id}_recommendations_{timestamp}.json"
            
            data = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'cv_summary': {
                    'name': cv_data.get('personal_info', {}).get('name', ''),
                    'seniority': cv_data.get('seniority', ''),
                    'skills_count': len(cv_data.get('skills', {}).get('technical', [])),
                    'confidence': cv_data.get('confidence', 0)
                },
                'recommendations': [
                    {
                        'job_id': rec.job_id,
                        'job_title': rec.job_title,
                        'company': rec.company,
                        'overall_score': rec.overall_score,
                        'matched_skills': rec.matched_skills,
                        'missing_skills': rec.missing_skills,
                        'recommendation_reason': rec.recommendation_reason
                    }
                    for rec in recommendations
                ]
            }
            
            with open(save_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n{self.colors.GREEN}💾 Recomendações salvas em: {filename}{self.colors.RESET}")
            
        except Exception as e:
            print(f"\n{self.colors.YELLOW}⚠️ Erro ao salvar recomendações: {e}{self.colors.RESET}")
    
    def _view_saved_recommendations(self):
        """Visualiza recomendações salvas"""
        self._clear_screen()
        print(f"{self.colors.CYAN}📋 RECOMENDAÇÕES SALVAS{self.colors.RESET}")
        print("=" * 35)
        
        recommendations_dir = Path("data/recommendations")
        if not recommendations_dir.exists():
            print(f"\n{self.colors.YELLOW}Nenhuma recomendação salva encontrada{self.colors.RESET}")
            self._safe_input_continue()
            return
        
        rec_files = list(recommendations_dir.glob("*.json"))
        if not rec_files:
            print(f"\n{self.colors.YELLOW}Nenhuma recomendação salva encontrada{self.colors.RESET}")
            self._safe_input_continue()
            return
        
        # Listar arquivos de recomendações
        print(f"\n{self.colors.GREEN}Recomendações salvas:{self.colors.RESET}")
        for i, file_path in enumerate(rec_files, 1):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                user_id = data.get('user_id', 'N/A')
                timestamp = data.get('timestamp', '')[:19].replace('T', ' ')
                rec_count = len(data.get('recommendations', []))
                
                print(f"   {i}. {user_id} - {timestamp} ({rec_count} recomendações)")
                
            except Exception:
                print(f"   {i}. {file_path.name} (erro ao ler)")
        
        # Permitir visualização detalhada
        choice = self._safe_input(f"\n{self.colors.BLUE}Ver detalhes (1-{len(rec_files)}, 0 para voltar): {self.colors.RESET}")
        
        try:
            choice_num = int(choice)
            if choice_num == 0:
                return
            elif 1 <= choice_num <= len(rec_files):
                self._show_recommendation_details(rec_files[choice_num - 1])
        except ValueError:
            pass
        
        self._safe_input_continue()
    
    def _show_recommendation_details(self, file_path: Path):
        """Exibe detalhes de uma recomendação salva"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._clear_screen()
            print(f"{self.colors.CYAN}📄 DETALHES DA RECOMENDAÇÃO{self.colors.RESET}")
            print("=" * 40)
            
            cv_summary = data.get('cv_summary', {})
            recommendations = data.get('recommendations', [])
            user_id = data.get('user_id', 'N/A')
            
            print(f"\n{self.colors.YELLOW}👤 Perfil:{self.colors.RESET}")
            print(f"   Usuário: {user_id}")
            print(f"   Nome: {cv_summary.get('name', 'N/A')}")
            print(f"   Senioridade: {cv_summary.get('seniority', 'N/A').title()}")
            print(f"   Skills: {cv_summary.get('skills_count', 0)}")
            print(f"   Data: {data.get('timestamp', '')[:19].replace('T', ' ')}")
            
            print(f"\n{self.colors.GREEN}🎯 Top 5 Recomendações:{self.colors.RESET}")
            for i, rec in enumerate(recommendations[:5], 1):
                # Cor baseada no score
                score = rec['overall_score']
                if score >= 0.8:
                    score_color = self.colors.GREEN
                elif score >= 0.6:
                    score_color = self.colors.YELLOW
                else:
                    score_color = self.colors.RED
                
                print(f"\n   {i}. {self.colors.BOLD}{rec['job_title']}{self.colors.RESET}")
                print(f"      🏢 {rec['company']}")
                print(f"      🎯 Compatibilidade: {score_color}{score:.1%}{self.colors.RESET}")
                
                if rec['matched_skills']:
                    print(f"      ✅ Skills: {', '.join(rec['matched_skills'][:3])}")
                
                if rec.get('missing_skills'):
                    print(f"      📚 Para aprender: {', '.join(rec['missing_skills'][:2])}")
                
                if rec.get('recommendation_reason'):
                    print(f"      💡 {rec['recommendation_reason']}")
            
            # 🆕 NOVA FUNCIONALIDADE: Análise detalhada para recomendações salvas
            print(f"\n{self.colors.CYAN}💡 Quer ver análise PROFUNDA de uma recomendação?{self.colors.RESET}")
            choice = self._safe_input(f"{self.colors.BLUE}Digite o número da vaga (1-{len(recommendations[:5])}) ou Enter para voltar: {self.colors.RESET}")
            
            if choice and choice.isdigit():
                rec_idx = int(choice) - 1
                if 0 <= rec_idx < len(recommendations[:5]):
                    selected_rec = recommendations[rec_idx]
                    self._show_detailed_analysis_from_saved(selected_rec, user_id, data)
            
        except Exception as e:
            print(f"{self.colors.RED}Erro ao carregar detalhes: {e}{self.colors.RESET}")
    
    def _show_detailed_analysis_from_saved(self, recommendation_data: Dict, user_id: str, full_data: Dict):
        """
        Mostra análise detalhada a partir de recomendação salva
        Reconstrói os dados necessários para gerar análise completa
        """
        try:
            self._clear_screen()
            print(f"{self.colors.CYAN}🔍 Preparando análise detalhada...{self.colors.RESET}")
            
            # Carregar vagas atuais se necessário
            if not self.current_jobs:
                self.current_jobs = self._load_available_jobs()
            
            # Tentar encontrar vaga correspondente nas vagas atuais
            job_data = None
            job_id = recommendation_data.get('job_id')
            
            for job in self.current_jobs:
                if job.get('id') == job_id:
                    job_data = self.matcher.prepare_job_for_matching(job)
                    break
            
            # Se não encontrar nas vagas atuais, criar dados simulados baseados na recomendação salva
            if not job_data:
                print(f"{self.colors.YELLOW}⚠️ Vaga original não encontrada, usando dados salvos...{self.colors.RESET}")
                job_data = self._reconstruct_job_data_from_recommendation(recommendation_data)
            
            # Reconstruir dados do CV a partir do resumo salvo
            cv_data = self._reconstruct_cv_data_from_summary(full_data.get('cv_summary', {}), user_id)
            
            # Criar objeto MatchResult a partir dos dados salvos
            from src.ml.cv_job_matcher import MatchResult
            
            match_result = MatchResult(
                job_id=recommendation_data.get('job_id', ''),
                job_title=recommendation_data.get('job_title', ''),
                company=recommendation_data.get('company', ''),
                overall_score=recommendation_data.get('overall_score', 0.0),
                breakdown_scores=recommendation_data.get('breakdown_scores', {}),
                matched_skills=recommendation_data.get('matched_skills', []),
                missing_skills=recommendation_data.get('missing_skills', []),
                salary_compatibility=recommendation_data.get('salary_compatibility', 0.0),
                recommendation_reason=recommendation_data.get('recommendation_reason', '')
            )
            
            # Gerar análise detalhada
            print(f"{self.colors.GREEN}✅ Gerando análise detalhada...{self.colors.RESET}")
            analysis = self.matcher.print_detailed_recommendation(match_result, cv_data, job_data)
            
            print(f"\n{self.colors.BOLD}{self.colors.YELLOW}🤔 AÇÕES SUGERIDAS:{self.colors.RESET}")
            print(f"   1️⃣ Buscar esta vaga novamente")
            print(f"   2️⃣ Procurar vagas similares")
            print(f"   3️⃣ Estudar skills recomendadas")
            print(f"   4️⃣ Atualizar CV com novas skills")
            
            # Permitir feedback
            print(f"\n{self.colors.CYAN}💬 Como você avalia esta análise retrospectiva?{self.colors.RESET}")
            feedback_choice = self._safe_input(f"{self.colors.BLUE}Feedback (útil/pouco-útil/excelente): {self.colors.RESET}")
            
            if feedback_choice:
                if feedback_choice.lower() in ['útil', 'util', 'pouco-útil', 'pouco-util', 'excelente']:
                    print(f"\n{self.colors.GREEN}✅ Obrigado pelo feedback! Isso nos ajuda a melhorar o sistema.{self.colors.RESET}")
            
        except Exception as e:
            print(f"{self.colors.RED}❌ Erro na análise detalhada: {e}{self.colors.RESET}")
            import traceback
            traceback.print_exc()
        
        self._safe_input_continue()
    
    def _reconstruct_job_data_from_recommendation(self, recommendation_data: Dict) -> Dict:
        """Reconstrói dados da vaga a partir da recomendação salva"""
        return {
            'job_id': recommendation_data.get('job_id', ''),
            'title': recommendation_data.get('job_title', ''),
            'company': recommendation_data.get('company', ''),
            'location': 'Não especificado',
            'description': f"Vaga para {recommendation_data.get('job_title', '')}",
            'requirements': 'Conforme análise original',
            
            # Dados inferidos
            'skills': recommendation_data.get('matched_skills', []) + recommendation_data.get('missing_skills', []),
            'seniority': self._infer_seniority_from_title(recommendation_data.get('job_title', '')),
            'location_info': {'is_remote': False, 'is_hybrid': False, 'city': 'Não especificado', 'state': 'Não especificado'},
            'salary_info': {'min': 5000, 'max': 15000, 'median': 10000},  # Estimativa padrão
            
            # Textos para análise
            'skills_text': ' '.join(recommendation_data.get('matched_skills', []) + recommendation_data.get('missing_skills', [])),
            'full_text': f"{recommendation_data.get('job_title', '')} {recommendation_data.get('company', '')}",
            'requirements_text': f"Skills requeridas: {', '.join(recommendation_data.get('missing_skills', []))}"
        }
    
    def _reconstruct_cv_data_from_summary(self, cv_summary: Dict, user_id: str) -> Dict:
        """Reconstrói dados básicos do CV a partir do resumo salvo"""
        return {
            'user_id': user_id,
            'personal_info': {
                'name': cv_summary.get('name', 'Usuário'),
            },
            'skills': {
                'technical': ['python', 'javascript', 'sql'],  # Skills padrão, pode ser melhorado
                'soft': ['comunicação', 'trabalho em equipe'],
                'by_category': {'programming': ['python', 'javascript'], 'database': ['sql']}
            },
            'experience': {
                'current_position': 'Desenvolvedor',
                'companies': ['Empresa Anterior'],
                'total_years': 5
            },
            'seniority': cv_summary.get('seniority', 'pleno'),
            'salary_range': {'min': 8000, 'max': 15000, 'median': 11500},
            'preferences': {},
            'confidence': cv_summary.get('confidence', 0.8),
            
            # Textos para análise
            'skills_text': 'python javascript sql comunicação trabalho em equipe',
            'experience_text': 'Desenvolvedor 5 anos experiencia',
            'full_profile_text': f"python javascript sql {cv_summary.get('seniority', 'pleno')} desenvolvedor 5 anos"
        }
    
    def _infer_seniority_from_title(self, title: str) -> str:
        """Infere senioridade a partir do título da vaga"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['junior', 'jr', 'trainee', 'estagiario']):
            return 'junior'
        elif any(word in title_lower for word in ['senior', 'sr', 'especialista', 'lead']):
            return 'senior'
        elif any(word in title_lower for word in ['pleno', 'mid', 'middle']):
            return 'pleno'
        else:
            return 'pleno'  # Default
    
    # Utility methods
    def _safe_input(self, prompt: str) -> Optional[str]:
        """Input seguro que trata interrupções"""
        try:
            return input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            return None
    
    def _safe_input_continue(self, message: str = "Pressione Enter para continuar..."):
        """Input de continuação seguro"""
        try:
            input(f"\n{message}")
        except (KeyboardInterrupt, EOFError):
            pass
    
    def _show_detailed_analysis(self, recommendation, user_id: str):
        """Mostra análise detalhada de uma recomendação específica"""
        try:
            self._clear_screen()
            
            # Buscar dados completos da vaga e do CV
            job_data = None
            for job in self.current_jobs:
                if job.get('id') == recommendation.job_id:
                    job_data = self.matcher.prepare_job_for_matching(job)
                    break
            
            if not job_data:
                print(f"{self.colors.RED}❌ Dados da vaga não encontrados{self.colors.RESET}")
                self._safe_input_continue()
                return
            
            # Obter dados do CV
            cv_data = self.matcher.cv_cache.get(user_id)
            if not cv_data:
                print(f"{self.colors.RED}❌ Dados do CV não encontrados{self.colors.RESET}")
                self._safe_input_continue()
                return
            
            # Gerar e exibir análise detalhada
            print(f"{self.colors.CYAN}🔍 Gerando análise detalhada...{self.colors.RESET}")
            analysis = self.matcher.print_detailed_recommendation(recommendation, cv_data, job_data)
            
            print(f"\n{self.colors.BOLD}{self.colors.YELLOW}🤔 AÇÕES SUGERIDAS:{self.colors.RESET}")
            print(f"   1️⃣ Se candidatar à vaga")
            print(f"   2️⃣ Salvar para candidatura futura")
            print(f"   3️⃣ Estudar skills faltantes primeiro")
            print(f"   4️⃣ Buscar vagas similares")
            
            # Permitir feedback direto
            print(f"\n{self.colors.CYAN}💬 Dar feedback sobre esta análise:{self.colors.RESET}")
            feedback_choice = self._safe_input(f"{self.colors.BLUE}Como você avalia esta vaga? (like/dislike/apply/interessante): {self.colors.RESET}")
            
            if feedback_choice and self.feedback_system:
                if feedback_choice.lower() in ['like', 'dislike', 'apply', 'interessante']:
                    self.feedback_system.record_interaction(
                        user_id,
                        job_data,
                        feedback_choice.lower(),
                        recommendation.overall_score,
                        recommendation.matched_skills
                    )
                    print(f"\n{self.colors.GREEN}✅ Feedback registrado! O sistema está aprendendo suas preferências.{self.colors.RESET}")
            
        except Exception as e:
            print(f"{self.colors.RED}❌ Erro na análise detalhada: {e}{self.colors.RESET}")
        
        self._safe_input_continue()
    
    def _clear_screen(self):
        """Limpa a tela"""
        os.system('cls' if os.name == 'nt' else 'clear')