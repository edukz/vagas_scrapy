"""
Testes para o Sistema de Deduplicação

Este módulo testa todas as funcionalidades do sistema de deduplicação,
incluindo detecção de duplicatas, limpeza de arquivos e performance.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.deduplicator import JobDeduplicator, deduplicate_file


def create_sample_jobs_with_duplicates():
    """Cria dados de exemplo com duplicatas intencionais"""
    return [
        # Job original
        {
            'titulo': 'Desenvolvedor Python Senior',
            'empresa': 'TechCorp',
            'localizacao': 'São Paulo, SP',
            'link': 'https://example.com/job/1',
            'salario': 'R$ 8.000 - R$ 12.000',
            'tecnologias_detectadas': ['Python', 'Django']
        },
        # Duplicata por URL exata
        {
            'titulo': 'Desenvolvedor Python Senior',
            'empresa': 'TechCorp',
            'localizacao': 'São Paulo, SP',
            'link': 'https://example.com/job/1',  # Mesma URL
            'salario': 'R$ 8.000 - R$ 12.000',
            'tecnologias_detectadas': ['Python', 'Django']
        },
        # Duplicata por título + empresa
        {
            'titulo': 'Desenvolvedor Python Senior',  # Mesmo título
            'empresa': 'TechCorp',  # Mesma empresa
            'localizacao': 'Rio de Janeiro, RJ',  # Local diferente
            'link': 'https://example.com/job/2',  # URL diferente
            'salario': 'R$ 9.000 - R$ 13.000',  # Salário diferente
            'tecnologias_detectadas': ['Python', 'Flask']  # Techs diferentes
        },
        # Job único
        {
            'titulo': 'Frontend Developer',
            'empresa': 'WebStudio',
            'localizacao': 'Remoto',
            'link': 'https://example.com/job/3',
            'salario': 'R$ 5.000 - R$ 8.000',
            'tecnologias_detectadas': ['React', 'JavaScript']
        },
        # Duplicata por similaridade de título
        {
            'titulo': 'Desenvolvedor   Python   Sênior',  # Título similar (espaços extras)
            'empresa': 'TechCorp',
            'localizacao': 'Belo Horizonte, MG',
            'link': 'https://example.com/job/4',
            'salario': 'R$ 7.000 - R$ 11.000',
            'tecnologias_detectadas': ['Python', 'FastAPI']
        },
        # Job único 2
        {
            'titulo': 'DevOps Engineer',
            'empresa': 'CloudTech',
            'localizacao': 'Remoto',
            'link': 'https://example.com/job/5',
            'salario': 'R$ 10.000 - R$ 15.000',
            'tecnologias_detectadas': ['Docker', 'Kubernetes']
        }
    ]


def test_basic_deduplication():
    """Testa deduplicação básica"""
    print("🧪 Testando deduplicação básica...")
    
    deduplicator = JobDeduplicator()
    jobs = create_sample_jobs_with_duplicates()
    
    print(f"   📊 Jobs originais: {len(jobs)}")
    
    # Aplicar deduplicação
    unique_jobs = deduplicator.deduplicate_jobs(jobs, verbose=False)
    
    print(f"   ✅ Jobs únicos: {len(unique_jobs)}")
    print(f"   ❌ Duplicatas removidas: {len(jobs) - len(unique_jobs)}")
    
    # Deve remover pelo menos 2 duplicatas
    assert len(unique_jobs) < len(jobs), "Deveria ter removido duplicatas"
    assert len(unique_jobs) >= 3, "Deveria manter pelo menos 3 jobs únicos"
    
    print("✅ Deduplicação básica: OK")


def test_duplicate_detection_methods():
    """Testa diferentes métodos de detecção de duplicatas"""
    print("🧪 Testando métodos de detecção...")
    
    deduplicator = JobDeduplicator()
    
    # URL duplicada
    job1 = {'titulo': 'Job A', 'empresa': 'Corp A', 'link': 'https://example.com/1'}
    job2 = {'titulo': 'Job B', 'empresa': 'Corp B', 'link': 'https://example.com/1'}  # Mesma URL
    
    is_dup, reason = deduplicator.is_duplicate(job1)
    assert not is_dup, "Primeiro job não deveria ser duplicata"
    
    deduplicator.add_job(job1)
    
    is_dup, reason = deduplicator.is_duplicate(job2)
    assert is_dup, f"Deveria detectar URL duplicada: {reason}"
    assert "URL duplicada" in reason
    
    print("   ✅ Detecção por URL: OK")
    
    # Título + empresa duplicados
    deduplicator = JobDeduplicator()  # Reset
    job3 = {'titulo': 'Python Developer', 'empresa': 'TechCorp', 'link': 'https://example.com/3'}
    job4 = {'titulo': 'Python Developer', 'empresa': 'TechCorp', 'link': 'https://example.com/4'}
    
    deduplicator.add_job(job3)
    is_dup, reason = deduplicator.is_duplicate(job4)
    assert is_dup, f"Deveria detectar duplicata: {reason}"
    print(f"   Debug - reason: {reason}")
    # Pode detectar por hash de conteúdo ou título+empresa
    assert "duplicado" in reason.lower() or "duplicada" in reason.lower()
    
    print("   ✅ Detecção por título+empresa: OK")
    
    print("✅ Métodos de detecção: OK")


def test_file_deduplication():
    """Testa deduplicação de arquivos"""
    print("🧪 Testando deduplicação de arquivos...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Criar arquivo com duplicatas
        jobs_with_dups = create_sample_jobs_with_duplicates()
        test_file = os.path.join(temp_dir, "test_jobs.json")
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(jobs_with_dups, f, ensure_ascii=False, indent=2)
        
        print(f"   📁 Arquivo criado: {len(jobs_with_dups)} jobs")
        
        # Aplicar deduplicação no arquivo
        removed = deduplicate_file(test_file, backup=False)
        
        print(f"   🧹 Duplicatas removidas: {removed}")
        
        # Verificar resultado
        with open(test_file, 'r', encoding='utf-8') as f:
            cleaned_jobs = json.load(f)
        
        print(f"   ✅ Jobs finais: {len(cleaned_jobs)}")
        
        assert len(cleaned_jobs) < len(jobs_with_dups), "Deveria ter removido duplicatas"
        assert removed > 0, "Deveria ter removido pelo menos uma duplicata"
    
    print("✅ Deduplicação de arquivos: OK")


def test_directory_cleaning():
    """Testa limpeza de diretório completo"""
    print("🧪 Testando limpeza de diretório...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Criar múltiplos arquivos com duplicatas
        
        # Arquivo 1: formato lista
        jobs1 = create_sample_jobs_with_duplicates()[:4]
        file1 = os.path.join(temp_dir, "results_2024_01_15.json")
        with open(file1, 'w', encoding='utf-8') as f:
            json.dump(jobs1, f, ensure_ascii=False, indent=2)
        
        # Arquivo 2: formato dict com 'vagas'
        jobs2 = create_sample_jobs_with_duplicates()[2:]
        file2 = os.path.join(temp_dir, "vagas_home_office.json")
        data2 = {
            'metadata': {'total': len(jobs2)},
            'vagas': jobs2
        }
        with open(file2, 'w', encoding='utf-8') as f:
            json.dump(data2, f, ensure_ascii=False, indent=2)
        
        print(f"   📁 Arquivos criados: 2 arquivos")
        print(f"   📊 Total de jobs: {len(jobs1) + len(jobs2)}")
        
        # Aplicar limpeza
        deduplicator = JobDeduplicator()
        total_removed = deduplicator.clean_existing_files(temp_dir)
        
        print(f"   🧹 Total removidas: {total_removed}")
        
        # Verificar resultados
        with open(file1, 'r', encoding='utf-8') as f:
            cleaned1 = json.load(f)
        
        with open(file2, 'r', encoding='utf-8') as f:
            cleaned2 = json.load(f)['vagas']
        
        final_count = len(cleaned1) + len(cleaned2)
        original_count = len(jobs1) + len(jobs2)
        
        print(f"   ✅ Jobs finais: {final_count} (era {original_count})")
        
        assert final_count < original_count, "Deveria ter removido duplicatas"
        assert total_removed > 0, "Deveria ter removido pelo menos uma duplicata"
    
    print("✅ Limpeza de diretório: OK")


def test_performance_with_large_dataset():
    """Testa performance com dataset grande"""
    print("🚀 Testando performance...")
    
    import time
    
    # Criar dataset grande com duplicatas distribuídas
    large_dataset = []
    
    # 500 jobs únicos
    for i in range(500):
        job = {
            'titulo': f'Desenvolvedor {i}',
            'empresa': f'Empresa {i % 50}',  # 50 empresas diferentes
            'link': f'https://example.com/job/{i}',
            'localizacao': f'Cidade {i % 10}',  # 10 cidades
            'tecnologias_detectadas': [f'Tech{i % 20}']  # 20 tecnologias
        }
        large_dataset.append(job)
    
    # Adicionar 200 duplicatas
    for i in range(200):
        # Duplicar jobs existentes com pequenas variações
        original_idx = i % 500
        duplicate = large_dataset[original_idx].copy()
        duplicate['link'] = f"https://example.com/job/{original_idx}_dup_{i}"  # URL ligeiramente diferente
        large_dataset.append(duplicate)
    
    print(f"   📊 Dataset criado: {len(large_dataset)} jobs")
    
    # Testar performance
    deduplicator = JobDeduplicator()
    start_time = time.time()
    
    unique_jobs = deduplicator.deduplicate_jobs(large_dataset, verbose=False)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    removed = len(large_dataset) - len(unique_jobs)
    
    print(f"   ⏱️  Tempo de processamento: {processing_time:.3f}s")
    print(f"   🧹 Duplicatas removidas: {removed}")
    print(f"   ✅ Jobs únicos: {len(unique_jobs)}")
    print(f"   📈 Performance: {len(large_dataset)/processing_time:.0f} jobs/s")
    
    # Verificações
    assert processing_time < 5.0, f"Processamento muito lento: {processing_time}s"
    assert removed > 100, f"Deveria ter removido mais duplicatas: {removed}"
    assert len(unique_jobs) <= 500, "Não deveria ter mais que 500 jobs únicos"
    
    print("✅ Performance: OK")


def test_edge_cases():
    """Testa casos extremos"""
    print("🧪 Testando casos extremos...")
    
    deduplicator = JobDeduplicator()
    
    # Lista vazia
    empty_result = deduplicator.deduplicate_jobs([])
    assert len(empty_result) == 0, "Lista vazia deveria retornar lista vazia"
    
    # Job sem campos obrigatórios
    incomplete_jobs = [
        {'titulo': 'Job sem empresa'},
        {'empresa': 'Empresa sem título'},
        {},  # Job completamente vazio
        {'titulo': 'Job completo', 'empresa': 'Corp', 'link': 'https://example.com/1'}
    ]
    
    result = deduplicator.deduplicate_jobs(incomplete_jobs, verbose=False)
    assert len(result) >= 1, "Deveria manter pelo menos jobs válidos"
    
    # Textos com caracteres especiais
    special_jobs = [
        {
            'titulo': 'Développeur Senior (França)',
            'empresa': 'Société Française',
            'link': 'https://example.com/special/1'
        },
        {
            'titulo': 'Desenvolvedor Pleno - São Paulo/SP',
            'empresa': 'Empresa & Cia',
            'link': 'https://example.com/special/2'
        }
    ]
    
    result = deduplicator.deduplicate_jobs(special_jobs, verbose=False)
    assert len(result) == 2, "Deveria manter jobs com caracteres especiais"
    
    print("✅ Casos extremos: OK")


def run_all_tests():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES DO SISTEMA DE DEDUPLICAÇÃO")
    print("=" * 60)
    
    try:
        test_basic_deduplication()
        test_duplicate_detection_methods()
        test_file_deduplication()
        test_directory_cleaning()
        test_performance_with_large_dataset()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("🧹 Sistema de Deduplicação está funcionando perfeitamente!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)