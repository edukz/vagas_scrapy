#!/usr/bin/env python3
"""
Teste de integração do sistema de validação com dados realistas
Simula um scraping real e mostra a validação em ação
"""

import sys
import os
import json

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_validator import data_validator


def create_realistic_test_data():
    """Cria dados de teste realistas baseados em cenários reais"""
    return [
        # ✅ Vaga perfeita
        {
            'titulo': 'Senior Python Developer',
            'empresa': 'TechCorp Solutions Ltda',
            'salario': 'R$ 12.000 - R$ 18.000',
            'localizacao': 'São Paulo - SP',
            'data_publicacao': 'há 3 dias',
            'descricao': 'Buscamos desenvolvedor Python sênior para atuar com Django, FastAPI e microsserviços. Experiência com AWS e Docker são diferenciais.',
            'requisitos': 'Graduação em TI, 5+ anos Python, Django, FastAPI, conhecimento em AWS',
            'beneficios': 'Vale refeição R$ 40/dia, plano de saúde Bradesco, home office flexível',
            'nivel_experiencia': 'Sênior',
            'modalidade': 'Home Office'
        },
        
        # ⚠️ Vaga com problemas menores (corrigíveis)
        {
            'titulo': 'DESENVOLVEDOR JAVA JUNIOR',  # Caps lock
            'empresa': 'JavaSoft',
            'salario': 'R$4500 a R$6000',  # Formato irregular
            'localizacao': 'remoto',  # Não padronizado
            'data_publicacao': 'publicada ontem',
            'descricao': 'Oportunidade para desenvolvedor Java iniciante trabalhar com Spring Boot e microserviços.',
            'requisitos': 'Formação em Ciência da Computação, conhecimento em Java e Spring',
            'beneficios': 'Vale transporte, vale alimentação',
            'nivel_experiencia': 'Júnior',
            'modalidade': 'remoto'  # Não padronizado
        },
        
        # ❌ Vaga com dados inválidos
        {
            'titulo': 'Dev',  # Muito curto
            'empresa': 'Não informada',  # Inválida
            'salario': 'R$ 200.000',  # Muito alto
            'localizacao': 'X',  # Muito curta
            'data_publicacao': '2025-12-31',  # Data futura
            'descricao': 'Job',  # Muito curta
            'requisitos': 'Req',  # Muito curtos
            'beneficios': 'Ben',  # Muito curtos
            'nivel_experiencia': 'Expert Level 999',  # Inválido
            'modalidade': 'Teletransporte'  # Inválido
        },
        
        # 🔍 Vaga suspeita (spam)
        {
            'titulo': 'URGENTE!!! GANHE R$ 50.000!!! CLIQUE AQUI!!!',
            'empresa': 'Empresa Confidencial',
            'salario': 'R$ 50.000',
            'localizacao': 'Todo Brasil',
            'data_publicacao': 'há 1 dia',
            'descricao': 'OPORTUNIDADE ÚNICA!!! Trabalhe de casa e ganhe muito dinheiro!!! CLIQUE AGORA!!!',
            'requisitos': 'Apenas boa vontade e dedicação',
            'beneficios': 'Dinheiro fácil, liberdade total',
            'nivel_experiencia': 'Qualquer nível',
            'modalidade': 'Home Office'
        },
        
        # 📊 Vaga com salário anômalo
        {
            'titulo': 'Estagiário de Desenvolvimento',
            'empresa': 'StartupXYZ',
            'salario': 'R$ 25.000',  # Muito alto para estagiário
            'localizacao': 'São Paulo - SP',
            'data_publicacao': 'há 5 dias',
            'descricao': 'Vaga de estágio em desenvolvimento web com foco em React e Node.js.',
            'requisitos': 'Cursando Ciência da Computação, conhecimento básico em JavaScript',
            'beneficios': 'Vale refeição, vale transporte',
            'nivel_experiencia': 'Estagiário',
            'modalidade': 'Híbrido'
        },
        
        # ✨ Vaga internacional (formato diferente)
        {
            'titulo': 'Full Stack Developer',
            'empresa': 'GlobalTech Inc.',
            'salario': 'USD 8,000 - USD 12,000',  # Formato diferente
            'localizacao': 'Remote',
            'data_publicacao': '2024-06-15',  # Formato de data diferente
            'descricao': 'We are looking for a talented full stack developer to join our international team.',
            'requisitos': 'Bachelor in Computer Science, 3+ years experience with React and Node.js',
            'beneficios': 'Health insurance, stock options, flexible working hours',
            'nivel_experiencia': '3-5 years',
            'modalidade': 'Remote'
        }
    ]


def test_validation_step_by_step():
    """Testa validação passo a passo mostrando cada etapa"""
    print("🧪 TESTE DETALHADO DO SISTEMA DE VALIDAÇÃO")
    print("=" * 60)
    
    # Criar dados de teste
    test_jobs = create_realistic_test_data()
    print(f"📋 Dados de teste criados: {len(test_jobs)} vagas")
    print("   ✅ 1 vaga perfeita")
    print("   ⚠️ 1 vaga com problemas menores")
    print("   ❌ 1 vaga com dados inválidos")
    print("   🔍 1 vaga suspeita (spam)")
    print("   📊 1 vaga com salário anômalo")
    print("   ✨ 1 vaga internacional")
    
    # Testar validação individual
    print(f"\n🔍 VALIDAÇÃO INDIVIDUAL:")
    print("-" * 40)
    
    for i, job in enumerate(test_jobs, 1):
        print(f"\n📄 Vaga {i}: {job['titulo'][:30]}...")
        validated_job = data_validator.validate_job(job)
        
        validation = validated_job['_validation']
        print(f"   Score de qualidade: {validation['quality_score']:.2f}")
        print(f"   Status: {'✅ Válida' if validation['is_valid'] else '❌ Inválida'}")
        
        # Mostrar correções aplicadas
        corrections = []
        for field_result in validation['field_results'].values():
            corrections.extend(field_result.corrections_applied)
        
        if corrections:
            print(f"   🔧 Correções: {', '.join(set(corrections))}")
        
        # Mostrar erros
        errors = []
        for field_result in validation['field_results'].values():
            errors.extend(field_result.errors)
        
        if errors:
            print(f"   ❌ Erros: {len(errors)} encontrados")
            for error in errors[:2]:  # Mostrar apenas os primeiros 2
                print(f"      - {error}")
    
    return test_jobs


def test_batch_validation():
    """Testa validação em lote com relatório completo"""
    print(f"\n\n🔄 VALIDAÇÃO EM LOTE:")
    print("=" * 40)
    
    test_jobs = create_realistic_test_data()
    
    # Executar validação em lote
    validated_jobs, quality_report = data_validator.validate_batch(test_jobs)
    
    # Mostrar relatório completo
    data_validator.print_quality_report(quality_report)
    
    return validated_jobs, quality_report


def test_data_filtering():
    """Testa filtro de dados válidos vs inválidos"""
    print(f"\n\n🎯 TESTE DE FILTRO DE DADOS:")
    print("=" * 40)
    
    test_jobs = create_realistic_test_data()
    validated_jobs, _ = data_validator.validate_batch(test_jobs)
    
    # Separar válidos e inválidos
    valid_jobs = [j for j in validated_jobs if j['_validation']['is_valid']]
    invalid_jobs = [j for j in validated_jobs if not j['_validation']['is_valid']]
    
    print(f"📊 Resultados do filtro:")
    print(f"   ✅ Vagas válidas: {len(valid_jobs)}")
    print(f"   ❌ Vagas inválidas: {len(invalid_jobs)}")
    
    print(f"\n✅ VAGAS APROVADAS:")
    for i, job in enumerate(valid_jobs, 1):
        score = job['_validation']['quality_score']
        print(f"   {i}. {job['titulo'][:40]}... (Score: {score:.2f})")
    
    print(f"\n❌ VAGAS REJEITADAS:")
    for i, job in enumerate(invalid_jobs, 1):
        score = job['_validation']['quality_score']
        print(f"   {i}. {job['titulo'][:40]}... (Score: {score:.2f})")
    
    return valid_jobs, invalid_jobs


def test_corrections_showcase():
    """Mostra exemplos de correções aplicadas"""
    print(f"\n\n🔧 SHOWCASE DE CORREÇÕES AUTOMÁTICAS:")
    print("=" * 50)
    
    test_cases = [
        {
            'titulo': 'DESENVOLVEDOR PYTHON SENIOR',
            'empresa': 'TechCorp',
            'salario': 'R$8000 - R$12000',
            'localizacao': 'sao paulo',
            'data_publicacao': 'há 5 dias'
        }
    ]
    
    for case in test_cases:
        print(f"📋 ANTES da validação:")
        for field, value in case.items():
            print(f"   {field}: '{value}'")
        
        validated = data_validator.validate_job(case)
        
        print(f"\n📋 DEPOIS da validação:")
        for field, value in case.items():
            if field in validated:
                original = case[field]
                corrected = validated[field]
                if original != corrected:
                    print(f"   {field}: '{original}' → '{corrected}' ✅")
                else:
                    print(f"   {field}: '{corrected}'")
        
        print(f"\n🔧 Correções aplicadas:")
        corrections = []
        for field_result in validated['_validation']['field_results'].values():
            corrections.extend(field_result.corrections_applied)
        
        for correction in set(corrections):
            print(f"   • {correction}")


def test_anomaly_detection():
    """Testa detecção de anomalias"""
    print(f"\n\n🚨 TESTE DE DETECÇÃO DE ANOMALIAS:")
    print("=" * 45)
    
    test_jobs = create_realistic_test_data()
    validated_jobs, quality_report = data_validator.validate_batch(test_jobs)
    
    if quality_report.anomalies:
        print(f"🔍 {len(quality_report.anomalies)} anomalias detectadas:")
        
        for i, anomaly in enumerate(quality_report.anomalies, 1):
            print(f"\n{i}. Tipo: {anomaly['type']}")
            print(f"   Severidade: {anomaly['severity']}")
            
            if 'job_title' in anomaly:
                print(f"   Vaga: {anomaly['job_title'][:50]}...")
            elif 'company' in anomaly:
                print(f"   Empresa: {anomaly['company']}")
            
            if 'reason' in anomaly:
                print(f"   Razão: {anomaly['reason']}")
    else:
        print("✅ Nenhuma anomalia detectada")


def test_real_world_simulation():
    """Simula cenário real com dados do scraper"""
    print(f"\n\n🌐 SIMULAÇÃO DE CENÁRIO REAL:")
    print("=" * 40)
    
    # Simular dados como se viessem do scraper
    scraped_data = [
        {
            'titulo': '   Senior Software Engineer   ',  # Espaços extras
            'empresa': 'TECH SOLUTIONS LTDA',
            'salario': 'R$ 10.000,00 - R$ 15.000,00',  # Vírgulas decimais
            'localizacao': 'HOME OFFICE',
            'descricao': 'Excelente oportunidade para desenvolvedor experiente...',
            'requisitos': 'Python, Django, PostgreSQL, 5+ anos experiência',
            'beneficios': 'VR, VT, Plano Saúde',
            'nivel_experiencia': 'Senior',
            'modalidade': 'Home Office',
            'data_publicacao': 'publicada há 2 dias'
        },
        {
            'titulo': 'dev jr',  # Título muito curto e informal
            'empresa': '123 Tech',  # Nome suspeito
            'salario': 'negociável',  # Formato não padrão
            'localizacao': '',  # Vazio
            'descricao': '',  # Vazio
            'requisitos': '',
            'beneficios': '',
            'nivel_experiencia': '',
            'modalidade': '',
            'data_publicacao': ''
        }
    ]
    
    print("📥 Dados como chegam do scraper:")
    for i, job in enumerate(scraped_data, 1):
        print(f"\nVaga {i}:")
        print(f"   Título: '{job['titulo']}'")
        print(f"   Empresa: '{job['empresa']}'")
        print(f"   Salário: '{job['salario']}'")
    
    # Validar
    validated_jobs, report = data_validator.validate_batch(scraped_data)
    
    print(f"\n📤 Dados após validação:")
    valid_count = 0
    for i, job in enumerate(validated_jobs, 1):
        is_valid = job['_validation']['is_valid']
        score = job['_validation']['quality_score']
        
        print(f"\nVaga {i}: {'✅ VÁLIDA' if is_valid else '❌ INVÁLIDA'} (Score: {score:.2f})")
        if is_valid:
            valid_count += 1
            print(f"   Título: '{job['titulo']}'")
            print(f"   Empresa: '{job['empresa']}'")
            print(f"   Salário: '{job['salario']}'")
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   Total processadas: {len(scraped_data)}")
    print(f"   Válidas para salvar: {valid_count}")
    print(f"   Taxa de aprovação: {valid_count/len(scraped_data)*100:.1f}%")


def main():
    """Função principal do teste"""
    print("🧪 TESTE COMPLETO DO SISTEMA DE VALIDAÇÃO")
    print("=" * 60)
    print("Este teste demonstra todas as funcionalidades do sistema de")
    print("validação de dados em cenários realistas.")
    print("=" * 60)
    
    try:
        # Executar todos os testes
        test_validation_step_by_step()
        test_batch_validation()
        test_data_filtering()
        test_corrections_showcase()
        test_anomaly_detection()
        test_real_world_simulation()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("=" * 60)
        
        print("\n💡 RESUMO DOS BENEFÍCIOS DEMONSTRADOS:")
        print("   ✅ Detecção automática de dados inválidos")
        print("   🔧 Correção automática de formatos")
        print("   🚨 Detecção de anomalias e spam")
        print("   📊 Relatórios detalhados de qualidade")
        print("   🎯 Filtro inteligente para salvar apenas dados válidos")
        print("   📈 Métricas de qualidade e tendências")
        
        print("\n🚀 PARA TESTAR COM SCRAPER REAL:")
        print("   Execute: python main.py")
        print("   O sistema de validação será aplicado automaticamente!")
        
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()