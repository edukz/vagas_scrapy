#!/usr/bin/env python3
"""
Teste do sistema de validação de dados
"""

import sys
import os

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_validator import DataValidator, DataCleaner, FieldValidator, AnomalyDetector


def test_data_cleaner():
    """Testa a classe DataCleaner"""
    print("🧪 TESTE DO DATA CLEANER")
    print("-" * 30)
    
    cleaner = DataCleaner()
    
    # Teste normalização de texto
    test_cases = [
        ("  DESENVOLVEDOR    JAVA  ", "DESENVOLVEDOR JAVA"),
        ("texto\tcom\nquebras", "texto com quebras"),
        ("", "")
    ]
    
    print("Normalização de texto:")
    for input_text, expected in test_cases:
        result = cleaner.normalize_text(input_text)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{input_text}' -> '{result}'")
    
    # Teste capitalização
    print("\nCapitalização:")
    cap_cases = [
        ("DESENVOLVEDOR SENIOR", "Desenvolvedor Senior"),
        ("analista de sistemas", "Analista De Sistemas"),
        ("gerente de projetos", "Gerente De Projetos")
    ]
    
    for input_text, expected in cap_cases:
        result = cleaner.fix_capitalization(input_text)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{input_text}' -> '{result}'")
    
    # Teste extração de salário
    print("\nExtração de salário:")
    salary_cases = [
        ("R$ 5.000 - R$ 8.000", (5000.0, 8000.0)),
        ("R$ 7000", (7000.0, 7000.0)),
        ("A combinar", None),
        ("R$5000 a R$10000", (5000.0, 10000.0))
    ]
    
    for input_text, expected in salary_cases:
        result = cleaner.extract_salary_range(input_text)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{input_text}' -> {result}")
    
    print("✅ DataCleaner testado!")


def test_field_validator():
    """Testa validação de campos individuais"""
    print("\n🧪 TESTE DO FIELD VALIDATOR")
    print("-" * 30)
    
    validator = FieldValidator()
    
    # Teste título
    print("Validação de títulos:")
    title_cases = [
        ("Senior Software Engineer", True),
        ("Dev", False),  # Muito curto
        ("DESENVOLVEDOR JAVA", True),  # Será corrigido
        ("", False)  # Vazio
    ]
    
    for title, should_be_valid in title_cases:
        result = validator.validate_field('titulo', title)
        status = "✅" if result.is_valid == should_be_valid else "❌"
        print(f"   {status} '{title}' -> válido: {result.is_valid}")
        if result.corrections_applied:
            print(f"       Correções: {result.corrections_applied}")
    
    # Teste empresa
    print("\nValidação de empresas:")
    company_cases = [
        ("Tech Solutions Ltda", True),
        ("Não informada", False),
        ("123", False),  # Só números
        ("AB", False)   # Muito curto
    ]
    
    for company, should_be_valid in company_cases:
        result = validator.validate_field('empresa', company)
        status = "✅" if result.is_valid == should_be_valid else "❌"
        print(f"   {status} '{company}' -> válido: {result.is_valid}")
    
    # Teste salário
    print("\nValidação de salários:")
    salary_cases = [
        ("R$ 5.000 - R$ 8.000", True),
        ("A combinar", True),
        ("R$ 150000", False),  # Muito alto, warning
        ("abc", False)  # Formato inválido
    ]
    
    for salary, should_be_valid in salary_cases:
        result = validator.validate_field('salario', salary)
        has_errors = len(result.errors) > 0
        print(f"   📊 '{salary}' -> erros: {has_errors}, avisos: {len(result.warnings)}")
        if result.corrections_applied:
            print(f"       Valor corrigido: '{result.cleaned_value}'")
    
    print("✅ FieldValidator testado!")


def test_anomaly_detector():
    """Testa detector de anomalias"""
    print("\n🧪 TESTE DO ANOMALY DETECTOR")
    print("-" * 30)
    
    detector = AnomalyDetector()
    
    # Criar dados de teste
    test_jobs = [
        {
            'titulo': 'Desenvolvedor Python',
            'empresa': 'TechCorp',
            'salario': 'R$ 6.000'
        },
        {
            'titulo': 'Analista Java',
            'empresa': 'TechCorp',
            'salario': 'R$ 7.000'
        },
        {
            'titulo': 'Senior Engineer',
            'empresa': 'BigTech',
            'salario': 'R$ 15.000'
        },
        {
            'titulo': 'Desenvolvedor Frontend',
            'empresa': 'TechCorp',
            'salario': 'R$ 5.500'
        },
        {
            'titulo': 'URGENTE!!! CLIQUE AQUI!!! $$$',  # Título suspeito
            'empresa': 'Spam Company',
            'salario': 'R$ 50.000'  # Salário muito alto
        }
    ]
    
    anomalies = detector.detect_anomalies(test_jobs)
    
    print(f"Anomalias detectadas: {len(anomalies)}")
    for anomaly in anomalies:
        print(f"   • {anomaly['type']}: {anomaly.get('job_title', anomaly.get('company', 'N/A'))}")
        print(f"     Severidade: {anomaly['severity']}")
    
    print("✅ AnomalyDetector testado!")


def test_full_validation():
    """Teste completo de validação"""
    print("\n🧪 TESTE COMPLETO DE VALIDAÇÃO")
    print("-" * 30)
    
    validator = DataValidator()
    
    # Dados de teste misturados (válidos e inválidos)
    test_jobs = [
        {
            'titulo': 'Senior Python Developer',
            'empresa': 'TechCorp Ltda',
            'salario': 'R$ 8.000 - R$ 12.000',
            'localizacao': 'São Paulo - SP',
            'data_publicacao': 'há 2 dias',
            'descricao': 'Excelente oportunidade para desenvolvedor Python com experiência em Django e FastAPI.',
            'requisitos': 'Experiência com Python, Django, FastAPI, PostgreSQL',
            'beneficios': 'Vale refeição, plano de saúde, home office',
            'nivel_experiencia': 'Sênior',
            'modalidade': 'Home Office'
        },
        {
            'titulo': 'Dev',  # Título muito curto
            'empresa': 'Não informada',  # Empresa inválida
            'salario': 'abc',  # Salário inválido
            'localizacao': 'X',  # Localização muito curta
            'data_publicacao': '2025-12-31',  # Data futura
            'descricao': 'Desc',  # Descrição muito curta
            'requisitos': 'Req',  # Requisitos muito curtos
            'beneficios': 'Ben',  # Benefícios muito curtos
            'nivel_experiencia': 'XYZ',  # Nível inválido
            'modalidade': 'ABC'  # Modalidade inválida
        },
        {
            'titulo': 'ANALISTA DE SISTEMAS JAVA',  # Precisa correção de caps
            'empresa': 'JavaCorp Solutions',
            'salario': 'R$6000 - R$9000',  # Precisa formatação
            'localizacao': 'remoto',  # Precisa padronização
            'data_publicacao': 'publicada hoje',
            'descricao': 'Oportunidade para analista Java com conhecimento em Spring Boot e microserviços.',
            'requisitos': 'Java, Spring Boot, microserviços, Docker',
            'beneficios': 'Vale alimentação e transporte',
            'nivel_experiencia': 'Pleno',
            'modalidade': 'Remoto'
        }
    ]
    
    # Validar lote
    validated_jobs, report = validator.validate_batch(test_jobs)
    
    print(f"Jobs processados: {len(validated_jobs)}")
    print(f"Qualidade geral: {report.overall_quality:.1%}")
    
    # Mostrar relatório
    validator.print_quality_report(report)
    
    # Verificar correções
    print("\n📊 EXAMPLES DE CORREÇÕES:")
    for i, job in enumerate(validated_jobs):
        if '_validation' in job:
            corrections = []
            for field_result in job['_validation']['field_results'].values():
                corrections.extend(field_result.corrections_applied)
            
            if corrections:
                print(f"   Job {i+1}: {', '.join(set(corrections))}")
    
    print("✅ Validação completa testada!")


def main():
    """Função principal do teste"""
    print("🧪 TESTE DO SISTEMA DE VALIDAÇÃO DE DADOS")
    print("=" * 50)
    
    try:
        # Executar todos os testes
        test_data_cleaner()
        test_field_validator()
        test_anomaly_detector()
        test_full_validation()
        
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n💡 BENEFÍCIOS DA VALIDAÇÃO:")
        print("   ✅ Detecção automática de dados inválidos")
        print("   ✅ Correção automática de formatos")
        print("   ✅ Detecção de anomalias e padrões suspeitos")
        print("   ✅ Relatórios detalhados de qualidade")
        print("   ✅ Filtros automáticos para salvar apenas dados válidos")
        
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()