from typing import List, Dict
import re


class JobFilter:
    """
    Sistema de filtragem avançada para vagas
    """
    def __init__(self):
        # Tecnologias comuns
        self.tecnologias_comuns = [
            'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node',
            'django', 'flask', 'fastapi', 'sql', 'mysql', 'postgresql', 'mongodb',
            'aws', 'azure', 'docker', 'kubernetes', 'git', 'html', 'css',
            'typescript', 'php', 'c#', 'c++', 'golang', 'rust', 'scala',
            'spring', 'hibernate', 'redis', 'elasticsearch', 'jenkins', 'ci/cd'
        ]
        
        # Níveis de experiência
        self.niveis_experiencia = [
            'júnior', 'junior', 'pleno', 'sênior', 'senior', 'especialista',
            'trainee', 'estagiário', 'coordenador', 'líder', 'gerente'
        ]
        
        # Tipos de empresa
        self.tipos_empresa = [
            'startup', 'multinacional', 'consultoria', 'banco', 'fintech',
            'e-commerce', 'saúde', 'educação', 'governo', 'ong', 'agência'
        ]

    def extract_technologies(self, job):
        """
        Extrai tecnologias mencionadas na vaga
        """
        technologies = set()
        
        # Textos para analisar
        texts_to_analyze = [
            job.get('titulo', '').lower(),
            job.get('descricao', '').lower(),
            job.get('requisitos', '').lower()
        ]
        
        full_text = ' '.join(texts_to_analyze)
        
        for tech in self.tecnologias_comuns:
            if tech.lower() in full_text:
                technologies.add(tech.lower())
        
        return list(technologies)

    def extract_salary_range(self, job):
        """
        Extrai e padroniza informações de salário
        """
        salary_text = job.get('salario', '').lower()
        
        if not salary_text or salary_text in ['a combinar', 'não informado']:
            return None
        
        # Procurar por valores numéricos
        numbers = re.findall(r'(\d+\.?\d*)', salary_text.replace('.', '').replace(',', '.'))
        
        if numbers:
            try:
                # Assumir que valores acima de 1000 são salários mensais
                values = [float(n) for n in numbers if float(n) > 1000]
                if values:
                    return {
                        'min': min(values),
                        'max': max(values) if len(values) > 1 else min(values),
                        'original': job.get('salario', '')
                    }
            except:
                pass
        
        return {'original': job.get('salario', '')}

    def categorize_experience_level(self, job):
        """
        Categoriza o nível de experiência
        """
        texts_to_analyze = [
            job.get('titulo', '').lower(),
            job.get('nivel_experiencia', '').lower(),
            job.get('requisitos', '').lower()
        ]
        
        full_text = ' '.join(texts_to_analyze)
        
        if any(nivel in full_text for nivel in ['trainee', 'estagiário', 'estágio']):
            return 'trainee'
        elif any(nivel in full_text for nivel in ['júnior', 'junior']):
            return 'junior'
        elif any(nivel in full_text for nivel in ['pleno']):
            return 'pleno'
        elif any(nivel in full_text for nivel in ['sênior', 'senior', 'sr']):
            return 'senior'
        elif any(nivel in full_text for nivel in ['especialista', 'expert']):
            return 'especialista'
        elif any(nivel in full_text for nivel in ['coordenador', 'líder', 'lead']):
            return 'lideranca'
        elif any(nivel in full_text for nivel in ['gerente', 'diretor']):
            return 'gestao'
        else:
            return 'nao_especificado'

    def categorize_company_type(self, job):
        """
        Categoriza o tipo de empresa
        """
        empresa = job.get('empresa', '').lower()
        descricao = job.get('descricao', '').lower()
        
        full_text = f"{empresa} {descricao}"
        
        if any(tipo in full_text for tipo in ['startup', 'scale-up']):
            return 'startup'
        elif any(tipo in full_text for tipo in ['banco', 'financeira', 'fintech']):
            return 'financeiro'
        elif any(tipo in full_text for tipo in ['consultoria', 'consulting']):
            return 'consultoria'
        elif any(tipo in full_text for tipo in ['saúde', 'hospital', 'medicina']):
            return 'saude'
        elif any(tipo in full_text for tipo in ['educação', 'universidade', 'ensino']):
            return 'educacao'
        elif any(tipo in full_text for tipo in ['e-commerce', 'marketplace', 'varejo']):
            return 'ecommerce'
        elif any(tipo in full_text for tipo in ['governo', 'público', 'municipal']):
            return 'governo'
        else:
            return 'nao_categorizado'

    def apply_filters(self, jobs, filters_config):
        """
        Aplica filtros às vagas baseado na configuração
        """
        filtered_jobs = []
        
        for job in jobs:
            # Enriquecer job com dados de análise
            job['tecnologias_detectadas'] = self.extract_technologies(job)
            job['faixa_salarial'] = self.extract_salary_range(job)
            job['nivel_categorizado'] = self.categorize_experience_level(job)
            job['tipo_empresa'] = self.categorize_company_type(job)
            
            # Aplicar filtros
            if self._job_matches_filters(job, filters_config):
                filtered_jobs.append(job)
        
        return filtered_jobs

    def _job_matches_filters(self, job, filters_config):
        """
        Verifica se uma vaga atende aos filtros
        """
        # Filtro por tecnologias
        if filters_config.get('tecnologias'):
            required_techs = [tech.lower() for tech in filters_config['tecnologias']]
            job_techs = job.get('tecnologias_detectadas', [])
            if not any(tech in job_techs for tech in required_techs):
                return False
        
        # Filtro por salário mínimo
        if filters_config.get('salario_minimo'):
            job_salary = job.get('faixa_salarial')
            if not job_salary or not job_salary.get('min'):
                return False
            if job_salary['min'] < filters_config['salario_minimo']:
                return False
        
        # Filtro por nível de experiência
        if filters_config.get('niveis_experiencia'):
            if job.get('nivel_categorizado') not in filters_config['niveis_experiencia']:
                return False
        
        # Filtro por tipo de empresa
        if filters_config.get('tipos_empresa'):
            if job.get('tipo_empresa') not in filters_config['tipos_empresa']:
                return False
        
        # Filtro por palavras-chave no título/descrição
        if filters_config.get('palavras_chave'):
            full_text = f"{job.get('titulo', '')} {job.get('descricao', '')}".lower()
            keywords = [kw.lower() for kw in filters_config['palavras_chave']]
            if not any(kw in full_text for kw in keywords):
                return False
        
        return True


def get_filter_configuration():
    """
    Interface para configurar filtros
    """
    print("\n=== CONFIGURAÇÃO DE FILTROS AVANÇADOS ===\n")
    
    filters = {}
    
    # Filtro por tecnologias
    print("1. FILTRO POR TECNOLOGIAS")
    print("Tecnologias disponíveis: python, javascript, react, angular, node, java, etc.")
    tech_input = input("Digite as tecnologias desejadas (separadas por vírgula, ou ENTER para pular): ").strip()
    if tech_input:
        filters['tecnologias'] = [tech.strip() for tech in tech_input.split(',')]
        print(f"✓ Filtro aplicado: {filters['tecnologias']}")
    
    # Filtro por salário
    print("\n2. FILTRO POR SALÁRIO MÍNIMO")
    salary_input = input("Digite o salário mínimo desejado (ou ENTER para pular): ").strip()
    if salary_input:
        try:
            filters['salario_minimo'] = float(salary_input)
            print(f"✓ Salário mínimo: R$ {filters['salario_minimo']}")
        except:
            print("⚠ Valor inválido, filtro ignorado")
    
    # Filtro por nível
    print("\n3. FILTRO POR NÍVEL DE EXPERIÊNCIA")
    print("Opções: trainee, junior, pleno, senior, especialista, lideranca, gestao")
    level_input = input("Digite os níveis desejados (separados por vírgula, ou ENTER para pular): ").strip()
    if level_input:
        filters['niveis_experiencia'] = [level.strip() for level in level_input.split(',')]
        print(f"✓ Níveis: {filters['niveis_experiencia']}")
    
    # Filtro por tipo de empresa
    print("\n4. FILTRO POR TIPO DE EMPRESA")
    print("Opções: startup, financeiro, consultoria, saude, educacao, ecommerce, governo")
    company_input = input("Digite os tipos desejados (separados por vírgula, ou ENTER para pular): ").strip()
    if company_input:
        filters['tipos_empresa'] = [tipo.strip() for tipo in company_input.split(',')]
        print(f"✓ Tipos de empresa: {filters['tipos_empresa']}")
    
    # Filtro por palavras-chave
    print("\n5. FILTRO POR PALAVRAS-CHAVE")
    keyword_input = input("Digite palavras-chave para buscar no título/descrição (separadas por vírgula, ou ENTER para pular): ").strip()
    if keyword_input:
        filters['palavras_chave'] = [kw.strip() for kw in keyword_input.split(',')]
        print(f"✓ Palavras-chave: {filters['palavras_chave']}")
    
    print(f"\n✓ Configuração de filtros concluída!")
    if filters:
        print("Filtros ativos:")
        for key, value in filters.items():
            print(f"  - {key}: {value}")
    else:
        print("Nenhum filtro será aplicado (todas as vagas serão retornadas)")
    
    return filters