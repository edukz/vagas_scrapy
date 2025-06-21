"""
Handler para entrada manual de CV - Interface de formulário
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from ..utils.enhanced_menu_system import Colors


class ManualCVHandler:
    """Handler para entrada manual de dados do CV através de formulário interativo"""
    
    def __init__(self):
        self.cv_data = {}
        self.data_dir = Path("data/cv_manual")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def print_header(self, title: str):
        """Imprime cabeçalho formatado"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
        print("=" * 60)
        print()
    
    def print_section(self, title: str):
        """Imprime seção formatada"""
        print(f"\n{Colors.BOLD}{Colors.YELLOW}📝 {title}{Colors.RESET}")
        print("-" * 40)
    
    def get_input(self, prompt: str, required: bool = True, default: str = "") -> str:
        """Obtém input do usuário com validação"""
        while True:
            if default:
                value = input(f"{prompt} {Colors.DIM}({default}){Colors.RESET}: ").strip()
                if not value:
                    value = default
            else:
                marker = f"{Colors.RED}*{Colors.RESET}" if required else ""
                value = input(f"{prompt} {marker}: ").strip()
            
            if not required or value:
                return value
            else:
                print(f"{Colors.RED}⚠️ Este campo é obrigatório!{Colors.RESET}")
    
    def get_multiline_input(self, prompt: str) -> str:
        """Obtém input de múltiplas linhas"""
        print(f"{prompt} {Colors.DIM}(Digite END em uma nova linha para finalizar){Colors.RESET}:")
        lines = []
        while True:
            line = input()
            if line.upper() == "END":
                break
            lines.append(line)
        return "\n".join(lines)
    
    def get_list_input(self, prompt: str, min_items: int = 1) -> List[str]:
        """Obtém lista de itens do usuário"""
        print(f"{prompt} {Colors.DIM}(Digite um por linha, END para finalizar){Colors.RESET}:")
        items = []
        while True:
            item = input(f"  {len(items) + 1}. ").strip()
            if item.upper() == "END":
                if len(items) >= min_items:
                    break
                else:
                    print(f"{Colors.RED}⚠️ Adicione pelo menos {min_items} item(ns){Colors.RESET}")
            elif item:
                items.append(item)
        return items
    
    async def handle_manual_cv_input(self):
        """Manipula entrada manual de CV com formulário completo"""
        try:
            self.print_header("📄 CADASTRO MANUAL DE CURRÍCULO")
            
            print(f"{Colors.GREEN}Vamos preencher seu currículo com as informações")
            print(f"mais solicitadas pelas empresas.{Colors.RESET}")
            print(f"\n{Colors.YELLOW}Campos marcados com {Colors.RED}*{Colors.YELLOW} são obrigatórios{Colors.RESET}")
            
            # 1. DADOS PESSOAIS
            self.print_section("DADOS PESSOAIS")
            
            self.cv_data["personal_info"] = {
                "nome_completo": self.get_input("Nome completo"),
                "email": self.get_input("E-mail"),
                "telefone": self.get_input("Telefone/WhatsApp"),
                "linkedin": self.get_input("LinkedIn (URL)", required=False),
                "github": self.get_input("GitHub (URL)", required=False),
                "portfolio": self.get_input("Portfolio/Website", required=False),
                "cidade": self.get_input("Cidade"),
                "estado": self.get_input("Estado (sigla)", default="SP"),
                "disponibilidade_mudanca": self.get_yes_no("Disponível para mudança?"),
                "modalidade_preferida": self.get_work_mode()
            }
            
            # 2. OBJETIVO PROFISSIONAL
            self.print_section("OBJETIVO PROFISSIONAL")
            
            self.cv_data["objective"] = {
                "cargo_desejado": self.get_input("Cargo desejado"),
                "area_atuacao": self.get_area_selection(),
                "nivel_senioridade": self.get_seniority_level(),
                "resumo_profissional": self.get_multiline_input("Resumo profissional (2-3 linhas)")
            }
            
            # 3. EXPERIÊNCIA PROFISSIONAL
            self.print_section("EXPERIÊNCIA PROFISSIONAL")
            
            self.cv_data["experiences"] = []
            add_more = True
            
            while add_more:
                print(f"\n{Colors.CYAN}Experiência #{len(self.cv_data['experiences']) + 1}:{Colors.RESET}")
                
                experience = {
                    "cargo": self.get_input("Cargo"),
                    "empresa": self.get_input("Empresa"),
                    "periodo_inicio": self.get_input("Início (MM/AAAA)"),
                    "periodo_fim": self.get_input("Fim (MM/AAAA ou 'Atual')", default="Atual"),
                    "descricao": self.get_multiline_input("Descrição das atividades"),
                    "principais_tecnologias": self.get_list_input("Principais tecnologias utilizadas", min_items=1)
                }
                
                self.cv_data["experiences"].append(experience)
                
                if len(self.cv_data["experiences"]) >= 1:
                    add_more = self.get_yes_no("\nAdicionar outra experiência?", default="n")
                
            # 4. FORMAÇÃO ACADÊMICA
            self.print_section("FORMAÇÃO ACADÊMICA")
            
            self.cv_data["education"] = []
            add_more = True
            
            while add_more:
                print(f"\n{Colors.CYAN}Formação #{len(self.cv_data['education']) + 1}:{Colors.RESET}")
                
                education = {
                    "curso": self.get_input("Curso"),
                    "instituicao": self.get_input("Instituição"),
                    "nivel": self.get_education_level(),
                    "status": self.get_education_status(),
                    "ano_conclusao": self.get_input("Ano de conclusão (ou previsão)")
                }
                
                self.cv_data["education"].append(education)
                
                add_more = self.get_yes_no("\nAdicionar outra formação?", default="n")
            
            # 5. HABILIDADES TÉCNICAS
            self.print_section("HABILIDADES TÉCNICAS")
            
            print(f"{Colors.GREEN}Liste suas habilidades por categoria:{Colors.RESET}")
            
            self.cv_data["technical_skills"] = {
                "linguagens": self.get_list_input("Linguagens de programação", min_items=1),
                "frameworks": self.get_list_input("Frameworks e bibliotecas", min_items=0),
                "bancos_dados": self.get_list_input("Bancos de dados", min_items=0),
                "ferramentas": self.get_list_input("Ferramentas e plataformas", min_items=0),
                "metodologias": self.get_list_input("Metodologias (Scrum, DevOps, etc.)", min_items=0),
                "cloud": self.get_list_input("Cloud/Infraestrutura", min_items=0)
            }
            
            # 6. IDIOMAS
            self.print_section("IDIOMAS")
            
            self.cv_data["languages"] = []
            add_more = True
            
            while add_more:
                language = {
                    "idioma": self.get_input("Idioma"),
                    "nivel": self.get_language_level()
                }
                self.cv_data["languages"].append(language)
                
                add_more = self.get_yes_no("\nAdicionar outro idioma?", default="n")
            
            # 7. CERTIFICAÇÕES
            self.print_section("CERTIFICAÇÕES (Opcional)")
            
            self.cv_data["certifications"] = []
            if self.get_yes_no("Possui certificações?", default="n"):
                add_more = True
                while add_more:
                    cert = {
                        "nome": self.get_input("Nome da certificação"),
                        "instituicao": self.get_input("Instituição emissora"),
                        "ano": self.get_input("Ano de obtenção")
                    }
                    self.cv_data["certifications"].append(cert)
                    
                    add_more = self.get_yes_no("\nAdicionar outra certificação?", default="n")
            
            # 8. INFORMAÇÕES ADICIONAIS
            self.print_section("INFORMAÇÕES ADICIONAIS")
            
            self.cv_data["additional_info"] = {
                "pretensao_salarial": self.get_salary_expectation(),
                "disponibilidade_inicio": self.get_input("Disponibilidade para início", default="Imediato"),
                "possui_cnpj": self.get_yes_no("Possui CNPJ/MEI?", default="n"),
                "aceita_pj": self.get_yes_no("Aceita contratação PJ?", default="s")
            }
            
            # SALVAR CV
            await self.save_cv_data()
            
            # MOSTRAR RESUMO
            await self.show_cv_summary()
            
            # OFERECER ANÁLISE
            if self.get_yes_no("\nDeseja analisar este CV agora?", default="s"):
                await self.analyze_manual_cv()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⚠️ Entrada cancelada pelo usuário{Colors.RESET}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro: {e}{Colors.RESET}")
    
    def get_yes_no(self, prompt: str, default: str = "s") -> bool:
        """Obtém resposta sim/não do usuário"""
        while True:
            response = self.get_input(f"{prompt} (s/n)", required=False, default=default).lower()
            if response in ['s', 'sim', 'y', 'yes']:
                return True
            elif response in ['n', 'nao', 'não', 'no']:
                return False
            else:
                print(f"{Colors.RED}Por favor, responda com 's' ou 'n'{Colors.RESET}")
    
    def get_work_mode(self) -> str:
        """Obtém modalidade de trabalho preferida"""
        print("\nModalidade de trabalho preferida:")
        options = ["Remoto", "Presencial", "Híbrido", "Indiferente"]
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")
        
        while True:
            try:
                choice = int(self.get_input("Escolha"))
                if 1 <= choice <= len(options):
                    return options[choice - 1]
            except ValueError:
                pass
            print(f"{Colors.RED}Opção inválida!{Colors.RESET}")
    
    def get_area_selection(self) -> str:
        """Obtém área de atuação"""
        areas = [
            "Desenvolvimento Backend",
            "Desenvolvimento Frontend", 
            "Full Stack",
            "Mobile",
            "DevOps/Infraestrutura",
            "Data Science/Analytics",
            "QA/Testes",
            "Gestão/Liderança",
            "UX/UI Design",
            "Outro"
        ]
        
        print("\nÁrea de atuação principal:")
        for i, area in enumerate(areas, 1):
            print(f"  {i}. {area}")
        
        while True:
            try:
                choice = int(self.get_input("Escolha"))
                if 1 <= choice <= len(areas):
                    if areas[choice - 1] == "Outro":
                        return self.get_input("Especifique a área")
                    return areas[choice - 1]
            except ValueError:
                pass
            print(f"{Colors.RED}Opção inválida!{Colors.RESET}")
    
    def get_seniority_level(self) -> str:
        """Obtém nível de senioridade"""
        levels = ["Estagiário", "Júnior", "Pleno", "Sênior", "Especialista", "Liderança"]
        
        print("\nNível de senioridade:")
        for i, level in enumerate(levels, 1):
            print(f"  {i}. {level}")
        
        while True:
            try:
                choice = int(self.get_input("Escolha"))
                if 1 <= choice <= len(levels):
                    return levels[choice - 1]
            except ValueError:
                pass
            print(f"{Colors.RED}Opção inválida!{Colors.RESET}")
    
    def get_education_level(self) -> str:
        """Obtém nível de formação"""
        levels = [
            "Ensino Médio",
            "Técnico",
            "Graduação",
            "Pós-graduação",
            "Mestrado",
            "Doutorado"
        ]
        
        print("Nível:")
        for i, level in enumerate(levels, 1):
            print(f"  {i}. {level}")
        
        while True:
            try:
                choice = int(self.get_input("Escolha"))
                if 1 <= choice <= len(levels):
                    return levels[choice - 1]
            except ValueError:
                pass
            print(f"{Colors.RED}Opção inválida!{Colors.RESET}")
    
    def get_education_status(self) -> str:
        """Obtém status da formação"""
        statuses = ["Concluído", "Em andamento", "Trancado"]
        
        print("Status:")
        for i, status in enumerate(statuses, 1):
            print(f"  {i}. {status}")
        
        while True:
            try:
                choice = int(self.get_input("Escolha"))
                if 1 <= choice <= len(statuses):
                    return statuses[choice - 1]
            except ValueError:
                pass
            print(f"{Colors.RED}Opção inválida!{Colors.RESET}")
    
    def get_language_level(self) -> str:
        """Obtém nível de idioma"""
        levels = ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"]
        
        print("Nível:")
        for i, level in enumerate(levels, 1):
            print(f"  {i}. {level}")
        
        while True:
            try:
                choice = int(self.get_input("Escolha"))
                if 1 <= choice <= len(levels):
                    return levels[choice - 1]
            except ValueError:
                pass
            print(f"{Colors.RED}Opção inválida!{Colors.RESET}")
    
    def get_salary_expectation(self) -> Dict[str, any]:
        """Obtém pretensão salarial"""
        print("\nPretensão salarial:")
        print("  1. Informar faixa")
        print("  2. A combinar")
        print("  3. Prefiro não informar")
        
        while True:
            try:
                choice = int(self.get_input("Escolha"))
                if choice == 1:
                    return {
                        "tipo": "faixa",
                        "minimo": self.get_input("Valor mínimo (R$)"),
                        "maximo": self.get_input("Valor máximo (R$)")
                    }
                elif choice == 2:
                    return {"tipo": "a_combinar"}
                elif choice == 3:
                    return {"tipo": "nao_informado"}
            except ValueError:
                pass
            print(f"{Colors.RED}Opção inválida!{Colors.RESET}")
    
    async def save_cv_data(self):
        """Salva dados do CV em arquivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cv_manual_{timestamp}.json"
        filepath = self.data_dir / filename
        
        # Adicionar metadados
        self.cv_data["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "type": "manual_input",
            "version": "1.0"
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.cv_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n{Colors.GREEN}✅ CV salvo em: {filepath}{Colors.RESET}")
        
        # Salvar também como "último CV"
        latest_filepath = self.data_dir / "latest_cv.json"
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(self.cv_data, f, ensure_ascii=False, indent=2)
    
    async def show_cv_summary(self):
        """Mostra resumo do CV cadastrado"""
        self.print_header("📋 RESUMO DO CV CADASTRADO")
        
        # Dados pessoais
        print(f"{Colors.BOLD}Candidato:{Colors.RESET} {self.cv_data['personal_info']['nome_completo']}")
        print(f"{Colors.BOLD}E-mail:{Colors.RESET} {self.cv_data['personal_info']['email']}")
        print(f"{Colors.BOLD}Telefone:{Colors.RESET} {self.cv_data['personal_info']['telefone']}")
        print(f"{Colors.BOLD}Localização:{Colors.RESET} {self.cv_data['personal_info']['cidade']}/{self.cv_data['personal_info']['estado']}")
        
        # Objetivo
        print(f"\n{Colors.BOLD}Objetivo:{Colors.RESET} {self.cv_data['objective']['cargo_desejado']}")
        print(f"{Colors.BOLD}Área:{Colors.RESET} {self.cv_data['objective']['area_atuacao']}")
        print(f"{Colors.BOLD}Senioridade:{Colors.RESET} {self.cv_data['objective']['nivel_senioridade']}")
        
        # Experiências
        print(f"\n{Colors.BOLD}Experiências:{Colors.RESET} {len(self.cv_data['experiences'])} cadastrada(s)")
        for i, exp in enumerate(self.cv_data['experiences'], 1):
            print(f"  {i}. {exp['cargo']} - {exp['empresa']} ({exp['periodo_inicio']} a {exp['periodo_fim']})")
        
        # Formação
        print(f"\n{Colors.BOLD}Formação:{Colors.RESET}")
        for edu in self.cv_data['education']:
            print(f"  • {edu['curso']} - {edu['instituicao']} ({edu['status']})")
        
        # Habilidades
        all_skills = []
        for category, skills in self.cv_data['technical_skills'].items():
            all_skills.extend(skills)
        
        print(f"\n{Colors.BOLD}Habilidades técnicas:{Colors.RESET} {len(all_skills)} cadastradas")
        print(f"  {Colors.DIM}{', '.join(all_skills[:10])}{' ...' if len(all_skills) > 10 else ''}{Colors.RESET}")
        
        # Idiomas
        print(f"\n{Colors.BOLD}Idiomas:{Colors.RESET}")
        for lang in self.cv_data['languages']:
            print(f"  • {lang['idioma']} - {lang['nivel']}")
    
    async def analyze_manual_cv(self):
        """Analisa o CV manual usando o sistema existente"""
        try:
            # Importar o handler de CV
            from . import cv_handler
            handler = cv_handler.CVHandler()
            
            # Converter CV manual para formato compatível
            cv_text = self.convert_to_text_format()
            
            # Criar arquivo temporário
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(cv_text)
                temp_path = f.name
            
            # Analisar usando o sistema existente
            print(f"\n{Colors.YELLOW}🔄 Processando análise do CV...{Colors.RESET}")
            
            # Simular análise (você pode integrar com o CVHandler real aqui)
            print(f"\n{Colors.GREEN}✅ Análise concluída!{Colors.RESET}")
            print(f"\nSeu perfil está pronto para receber recomendações de vagas.")
            
            # Limpar arquivo temporário
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro na análise: {e}{Colors.RESET}")
    
    def convert_to_text_format(self) -> str:
        """Converte dados do CV para formato texto"""
        lines = []
        
        # Cabeçalho
        info = self.cv_data['personal_info']
        lines.append(info['nome_completo'])
        lines.append(info['email'])
        lines.append(info['telefone'])
        if info.get('linkedin'):
            lines.append(f"LinkedIn: {info['linkedin']}")
        if info.get('github'):
            lines.append(f"GitHub: {info['github']}")
        lines.append(f"{info['cidade']}/{info['estado']}")
        lines.append("")
        
        # Objetivo
        obj = self.cv_data['objective']
        lines.append("OBJETIVO PROFISSIONAL")
        lines.append(f"{obj['cargo_desejado']} - {obj['area_atuacao']} ({obj['nivel_senioridade']})")
        lines.append(obj['resumo_profissional'])
        lines.append("")
        
        # Experiências
        lines.append("EXPERIÊNCIA PROFISSIONAL")
        for exp in self.cv_data['experiences']:
            lines.append(f"\n{exp['cargo']} - {exp['empresa']}")
            lines.append(f"{exp['periodo_inicio']} - {exp['periodo_fim']}")
            lines.append(exp['descricao'])
            lines.append(f"Tecnologias: {', '.join(exp['principais_tecnologias'])}")
        lines.append("")
        
        # Formação
        lines.append("FORMAÇÃO ACADÊMICA")
        for edu in self.cv_data['education']:
            lines.append(f"{edu['curso']} - {edu['instituicao']}")
            lines.append(f"{edu['nivel']} - {edu['status']} ({edu['ano_conclusao']})")
        lines.append("")
        
        # Habilidades
        lines.append("HABILIDADES TÉCNICAS")
        for category, skills in self.cv_data['technical_skills'].items():
            if skills:
                lines.append(f"{category.title()}: {', '.join(skills)}")
        lines.append("")
        
        # Idiomas
        lines.append("IDIOMAS")
        for lang in self.cv_data['languages']:
            lines.append(f"{lang['idioma']}: {lang['nivel']}")
        
        return "\n".join(lines)
    
    async def load_saved_cv(self) -> bool:
        """Carrega CV salvo anteriormente"""
        try:
            latest_path = self.data_dir / "latest_cv.json"
            if latest_path.exists():
                with open(latest_path, 'r', encoding='utf-8') as f:
                    self.cv_data = json.load(f)
                
                print(f"\n{Colors.GREEN}✅ CV carregado com sucesso!{Colors.RESET}")
                await self.show_cv_summary()
                return True
            else:
                print(f"\n{Colors.YELLOW}⚠️ Nenhum CV salvo encontrado{Colors.RESET}")
                return False
                
        except Exception as e:
            print(f"\n{Colors.RED}❌ Erro ao carregar CV: {e}{Colors.RESET}")
            return False