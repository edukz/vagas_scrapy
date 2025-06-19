"""
Testes para o Sistema de Índices do Cache

Este módulo testa todas as funcionalidades do sistema de indexação,
incluindo busca, estatísticas e performance.
"""

import os
import sys
import tempfile
import shutil
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.cache_index import CacheIndex, CacheIndexEntry
from src.compressed_cache import CompressedCache


def create_sample_jobs_data():
    """Cria dados de exemplo para testes"""
    return [
        {
            'titulo': 'Desenvolvedor Python Senior',
            'empresa': 'TechCorp',
            'localizacao': 'São Paulo, SP',
            'salario': 'R$ 8.000 - R$ 12.000',
            'nivel': 'Senior',
            'tecnologias_detectadas': ['Python', 'Django', 'PostgreSQL'],
            'data_coleta': '2024-01-15'
        },
        {
            'titulo': 'Frontend Developer',
            'empresa': 'WebStudio',
            'localizacao': 'Rio de Janeiro, RJ', 
            'salario': 'R$ 5.000 - R$ 8.000',
            'nivel': 'Pleno',
            'tecnologias_detectadas': ['React', 'JavaScript', 'CSS'],
            'data_coleta': '2024-01-15'
        },
        {
            'titulo': 'DevOps Engineer',
            'empresa': 'CloudTech',
            'localizacao': 'Remoto',
            'salario': 'R$ 10.000 - R$ 15.000', 
            'nivel': 'Senior',
            'tecnologias_detectadas': ['Docker', 'Kubernetes', 'AWS'],
            'data_coleta': '2024-01-15'
        }
    ]


def test_cache_index_basic_operations():
    """Testa operações básicas do índice"""
    print("🧪 Testando operações básicas do CacheIndex...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index = CacheIndex(temp_dir)
        
        # Criar entrada de teste
        jobs_data = create_sample_jobs_data()
        
        # Adicionar entrada
        index.add_entry(
            cache_key="test_key_1",
            file_path=f"{temp_dir}/test_key_1.json.gz",
            url="https://example.com/page1",
            jobs_data=jobs_data,
            original_size=1000,
            compressed_size=300
        )
        
        # Verificar se foi adicionada
        assert len(index.entries) == 1
        assert "test_key_1" in index.entries
        
        entry = index.entries["test_key_1"]
        assert entry.job_count == 3
        assert "TechCorp" in entry.companies
        assert "Python" in entry.technologies
        assert "São Paulo, SP" in entry.locations
        
        # Testar remoção
        removed = index.remove_entry("test_key_1")
        assert removed is True
        assert len(index.entries) == 0
        
        print("✅ Operações básicas: OK")


def test_cache_index_search():
    """Testa funcionalidades de busca"""
    print("🧪 Testando funcionalidades de busca...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index = CacheIndex(temp_dir)
        
        # Adicionar múltiplas entradas
        jobs1 = create_sample_jobs_data()
        jobs2 = [
            {
                'titulo': 'Java Developer',
                'empresa': 'JavaCorp', 
                'localizacao': 'Belo Horizonte, MG',
                'salario': 'R$ 6.000 - R$ 9.000',
                'nivel': 'Pleno',
                'tecnologias_detectadas': ['Java', 'Spring', 'MySQL'],
                'data_coleta': '2024-01-16'
            }
        ]
        
        index.add_entry("key1", f"{temp_dir}/key1.json.gz", "https://example.com/1", jobs1, 1000, 300)
        index.add_entry("key2", f"{temp_dir}/key2.json.gz", "https://example.com/2", jobs2, 500, 150)
        
        # Buscar por empresa
        results = index.search({'companies': ['TechCorp']})
        assert len(results) == 1
        assert results[0].cache_key == "key1"
        
        # Buscar por tecnologia
        results = index.search({'technologies': ['Python']})
        assert len(results) == 1
        assert results[0].cache_key == "key1"
        
        # Buscar por localização
        results = index.search({'locations': ['Belo Horizonte, MG']})
        assert len(results) == 1
        assert results[0].cache_key == "key2"
        
        # Buscar sem critérios (todas)
        results = index.search({})
        assert len(results) == 2
        
        # Buscar por número mínimo de jobs
        results = index.search({'min_jobs': 2})
        assert len(results) == 1
        assert results[0].cache_key == "key1"
        
        print("✅ Funcionalidades de busca: OK")


def test_cache_index_statistics():
    """Testa funcionalidades de estatísticas"""
    print("🧪 Testando funcionalidades de estatísticas...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index = CacheIndex(temp_dir)
        
        # Adicionar dados
        jobs_data = create_sample_jobs_data()
        index.add_entry("key1", f"{temp_dir}/key1.json.gz", "https://example.com/1", jobs_data, 1000, 300)
        
        # Testar estatísticas
        stats = index.get_stats()
        assert stats['total_entries'] == 1
        assert stats['total_jobs'] == 3
        assert stats['total_file_size'] == 1000
        assert stats['total_compressed_size'] == 300
        assert stats['average_compression_ratio'] == 70.0  # (1000-300)/1000 * 100
        
        # Testar top empresas
        top_companies = index.get_top_companies(5)
        assert len(top_companies) == 3  # TechCorp, WebStudio, CloudTech
        company_names = [name for name, count in top_companies]
        assert 'TechCorp' in company_names
        
        # Testar top tecnologias
        top_techs = index.get_top_technologies(5)
        tech_names = [name for name, count in top_techs]
        print(f"Debug - tech_names: {tech_names}")
        print(f"Debug - top_techs: {top_techs}")
        assert len(tech_names) > 0  # Pelo menos algumas tecnologias devem existir
        
        print("✅ Funcionalidades de estatísticas: OK")


def test_cache_index_persistence():
    """Testa persistência do índice em disco"""
    print("🧪 Testando persistência do índice...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Criar e popular índice
        index1 = CacheIndex(temp_dir)
        jobs_data = create_sample_jobs_data()
        index1.add_entry("key1", f"{temp_dir}/key1.json.gz", "https://example.com/1", jobs_data, 1000, 300)
        
        # Criar novo índice no mesmo diretório (deve carregar dados)
        index2 = CacheIndex(temp_dir)
        assert len(index2.entries) == 1
        assert "key1" in index2.entries
        
        entry = index2.entries["key1"]
        assert entry.job_count == 3
        assert "TechCorp" in entry.companies
        
        print("✅ Persistência do índice: OK")


async def test_compressed_cache_integration():
    """Testa integração com CompressedCache"""
    print("🧪 Testando integração com CompressedCache...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = CompressedCache(temp_dir, max_age_hours=24)
        
        # Criar dados de teste
        jobs_data = create_sample_jobs_data()
        test_data = {
            'jobs': jobs_data,
            'timestamp': datetime.now().timestamp(),
            'page_info': {'total': 3}
        }
        
        # Adicionar ao cache (deve indexar automaticamente)
        await cache.set("https://example.com/test", test_data)
        
        # Verificar se foi indexado
        assert len(cache.index.entries) == 1
        
        # Testar busca integrada
        results = cache.search_cache({'companies': ['TechCorp']})
        assert len(results) == 1
        
        # Testar estatísticas integradas
        stats = cache.get_cache_stats()
        assert 'compression' in stats
        assert 'index' in stats
        
        # Testar top empresas integrado
        top_companies = cache.get_top_companies(5)
        assert len(top_companies) > 0
        
        print("✅ Integração com CompressedCache: OK")


def test_cache_index_rebuild():
    """Testa reconstrução do índice"""
    print("🧪 Testando reconstrução do índice...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Criar arquivo de cache manualmente
        cache_data = {
            'data': {
                'jobs': create_sample_jobs_data(),
                'timestamp': datetime.now().timestamp()
            },
            'url': 'https://example.com/manual',
            'timestamp': datetime.now().isoformat(),
            'hash_key': 'manual_key'
        }
        
        import gzip
        cache_file = Path(temp_dir) / "manual_key.json.gz"
        with gzip.open(cache_file, 'wt', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        # Criar índice e reconstruir
        index = CacheIndex(temp_dir)
        count = index.rebuild_index()
        
        assert count == 1
        assert len(index.entries) == 1
        assert "manual_key" in index.entries
        
        print("✅ Reconstrução do índice: OK")


def run_performance_benchmark():
    """Benchmark de performance do sistema de índices"""
    print("🚀 Executando benchmark de performance...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        index = CacheIndex(temp_dir)
        
        # Criar muitas entradas para teste
        import time
        start_time = time.time()
        
        for i in range(100):
            jobs_data = [
                {
                    'titulo': f'Desenvolvedor {i}',
                    'empresa': f'Empresa{i % 10}',  # 10 empresas diferentes
                    'localizacao': f'Cidade{i % 5}, Estado',  # 5 localizações
                    'tecnologias_detectadas': [f'Tech{i % 3}', f'Framework{i % 4}'],  # Várias tecnologias
                    'nivel': ['Junior', 'Pleno', 'Senior'][i % 3],
                    'data_coleta': '2024-01-15'
                }
            ]
            
            index.add_entry(f"key_{i}", f"{temp_dir}/key_{i}.json.gz", f"https://example.com/{i}", 
                          jobs_data, 1000, 300)
        
        creation_time = time.time() - start_time
        
        # Testar busca
        start_time = time.time()
        results = index.search({'companies': ['Empresa5']})
        search_time = time.time() - start_time
        
        # Testar estatísticas
        start_time = time.time()
        stats = index.get_stats()
        stats_time = time.time() - start_time
        
        print(f"⚡ Performance Results:")
        print(f"   📝 Criação de 100 entradas: {creation_time:.3f}s ({creation_time/100*1000:.1f}ms por entrada)")
        print(f"   🔍 Busca em 100 entradas: {search_time:.3f}s")
        print(f"   📊 Cálculo de estatísticas: {stats_time:.3f}s")
        print(f"   📋 Resultados encontrados: {len(results)}")
        print(f"   💼 Total de vagas indexadas: {stats['total_jobs']}")


def main():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES DO SISTEMA DE ÍNDICES DO CACHE")
    print("=" * 60)
    
    try:
        # Testes unitários
        test_cache_index_basic_operations()
        test_cache_index_search()
        test_cache_index_statistics()
        test_cache_index_persistence()
        test_cache_index_rebuild()
        
        # Testes de integração
        asyncio.run(test_compressed_cache_integration())
        
        # Benchmark de performance
        run_performance_benchmark()
        
        print("\n" + "=" * 60)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("🚀 Sistema de Índices do Cache está funcionando perfeitamente!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)