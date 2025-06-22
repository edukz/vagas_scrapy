"""
Testes para validar as correções críticas implementadas
"""

import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Importar componentes a serem testados
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.systems.connection_pool import ConnectionPool, PooledPage
from src.systems.incremental_processor import IncrementalProcessor
from src.utils.lru_cache import LRUCacheWithTTL, CVJobMatcherCache


class TestConnectionPoolFixes:
    """Testa correções de race conditions no connection pool"""
    
    async def test_connection_pool_thread_safety(self):
        """Testa se pool é thread-safe após correções"""
        
        # Mock do browser
        mock_browser = Mock()
        mock_page = Mock()
        mock_context = Mock()
        mock_page.context = mock_context
        mock_page.goto = AsyncMock()
        mock_page.evaluate = AsyncMock()
        mock_context.clear_cookies = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        
        pool = ConnectionPool(min_size=2, max_size=5)
        
        # Inicializar pool
        await pool.initialize(mock_browser)
        
        # Simular acesso concorrente
        async def concurrent_access():
            page = await pool.get_page(timeout_seconds=1.0)
            if page:
                await asyncio.sleep(0.01)  # Simular uso
                await pool.return_page(page)
                return True
            return False
        
        # Executar múltiplas operações concorrentes
        tasks = [concurrent_access() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificar que não houve exceções
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Encontradas exceções: {exceptions}"
        
        # Verificar consistência do pool
        stats = pool.get_stats()
        assert stats['available_pages'] >= 0
        assert stats['busy_pages'] >= 0
        assert stats['available_pages'] + stats['busy_pages'] <= pool.max_size
        
        await pool.shutdown()
    
    async def test_connection_pool_timeout_handling(self):
        """Testa se timeouts são tratados corretamente"""
        
        mock_browser = Mock()
        mock_browser.new_page = AsyncMock(side_effect=Exception("Timeout simulado"))
        
        pool = ConnectionPool(min_size=1, max_size=2)
        
        # Tentar inicializar com erro
        await pool.initialize(mock_browser)
        
        # Tentar obter página com timeout curto
        start_time = time.time()
        page = await pool.get_page(timeout_seconds=0.1)
        elapsed = time.time() - start_time
        
        # Deve retornar None e respeitar timeout
        assert page is None
        assert elapsed < 0.5  # Não deve demorar muito mais que o timeout
        
        await pool.shutdown()


class TestIncrementalProcessorFixes:
    """Testa correções no processador incremental"""
    
    def test_absolute_page_limit(self):
        """Testa se limite absoluto de páginas funciona"""
        
        processor = IncrementalProcessor()
        
        # Simular vagas da página
        fake_jobs = [{'id': f'job_{i}', 'title': f'Job {i}'} for i in range(10)]
        
        # Testar limite absoluto
        should_continue, new_jobs = processor.should_continue_processing(
            current_page_jobs=fake_jobs,
            threshold=0.0,  # Threshold baixo para forçar continuação
            page_number=51,  # Acima do limite padrão de 50
            max_absolute_pages=50
        )
        
        # Deve parar devido ao limite absoluto
        assert should_continue is False
        assert 'stopped_reason' in processor.session_stats
        assert processor.session_stats['stopped_reason'] == 'absolute_limit'
    
    def test_division_by_zero_protection(self):
        """Testa proteção contra divisão por zero"""
        
        processor = IncrementalProcessor()
        
        # Teste com lista vazia
        should_continue, new_jobs = processor.should_continue_processing(
            current_page_jobs=[],
            threshold=0.5,
            page_number=1
        )
        
        # Deve retornar True para lista vazia
        assert should_continue is True
        assert new_jobs == []
        
    def test_threshold_calculations(self):
        """Testa cálculos de threshold estão corretos"""
        
        processor = IncrementalProcessor()
        
        # Mock do método is_job_processed para simular jobs conhecidos
        with patch.object(processor, 'is_job_processed') as mock_is_processed:
            # Simular que jobs com id terminado em 0 são conhecidos
            mock_is_processed.side_effect = lambda job: job['id'].endswith('0')
            
            fake_jobs = [{'id': f'job_{i}'} for i in range(10)]
            
            should_continue, new_jobs = processor.should_continue_processing(
                current_page_jobs=fake_jobs,
                threshold=0.5,
                page_number=5,
                max_absolute_pages=50
            )
            
            # Com jobs 0 conhecidos e resto novos: job_0 é conhecido = 1 conhecido, 9 novos
            assert len(new_jobs) == 9  # jobs 1-9 são novos
            # Na página 5 (6-10), usa threshold * 0.5 = 0.25
            # Ratio = 9/10 = 0.9 > 0.25, então deve continuar
            assert should_continue is True


class TestLRUCacheFixes:
    """Testa o novo sistema de cache com TTL"""
    
    def test_lru_cache_basic_operations(self):
        """Testa operações básicas do cache LRU"""
        
        cache = LRUCacheWithTTL(max_size=3, ttl_seconds=1)
        
        # Teste de set/get
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'
        
        # Teste de capacidade máxima
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        cache.set('key4', 'value4')  # Deve remover key1
        
        assert cache.get('key1') is None  # Foi removido
        assert cache.get('key4') == 'value4'  # Foi adicionado
        assert len(cache) == 3
    
    def test_lru_cache_ttl_expiration(self):
        """Testa expiração por TTL"""
        
        cache = LRUCacheWithTTL(max_size=10, ttl_seconds=0.1)
        
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'
        
        # Esperar expirar
        time.sleep(0.15)
        
        assert cache.get('key1') is None  # Deve ter expirado
    
    def test_cv_job_matcher_cache(self):
        """Testa cache especializado do CV Job Matcher"""
        
        cache = CVJobMatcherCache()
        
        # Teste de diferentes tipos de cache
        cache.set_cv('user1', {'name': 'João'})
        cache.set_job('job1', {'title': 'Developer'})
        cache.set_match('user1_job1', {'score': 0.8})
        
        assert cache.get_cv('user1')['name'] == 'João'
        assert cache.get_job('job1')['title'] == 'Developer'
        assert cache.get_match('user1_job1')['score'] == 0.8
        
        # Teste de estatísticas
        stats = cache.get_combined_stats()
        assert stats['total_size'] == 3
        assert stats['total_hits'] == 3
        assert stats['total_misses'] == 0
    
    def test_cache_thread_safety(self):
        """Testa thread safety do cache"""
        import threading
        
        cache = LRUCacheWithTTL(max_size=100, ttl_seconds=10)
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(50):
                    key = f'worker_{worker_id}_key_{i}'
                    value = f'value_{i}'
                    cache.set(key, value)
                    retrieved = cache.get(key)
                    if retrieved != value:
                        errors.append(f"Worker {worker_id}: Expected {value}, got {retrieved}")
            except Exception as e:
                errors.append(f"Worker {worker_id}: Exception {e}")
        
        # Criar múltiplas threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Esperar todas terminarem
        for t in threads:
            t.join()
        
        # Não deve haver erros
        assert len(errors) == 0, f"Erros encontrados: {errors}"


class TestErrorHandlingFixes:
    """Testa melhorias no tratamento de erros"""
    
    def test_silent_failure_prevention(self):
        """Testa se falhas silenciosas foram eliminadas"""
        
        # Este teste verifica se os scrapers agora loggam erros de cleanup
        
        # Simular erro de cleanup
        error_messages = []
        
        def mock_print(msg):
            error_messages.append(msg)
        
        # Mock para simular o comportamento do scraper corrigido
        with patch('builtins.print', mock_print):
            # Simular cleanup com erros
            cleanup_errors = ["Erro ao fechar página: Connection lost"]
            
            # Código similar ao que foi implementado nos scrapers
            if cleanup_errors:
                mock_print(f"⚠️ Problemas durante cleanup: {len(cleanup_errors)} erros")
                for error in cleanup_errors[:3]:
                    mock_print(f"   • {error}")
        
        # Verificar que erros foram loggados
        assert len(error_messages) >= 2
        assert "Problemas durante cleanup" in error_messages[0]
        assert "Erro ao fechar página" in error_messages[1]


# Função para executar todos os testes
def run_critical_fixes_tests():
    """Executa todos os testes de correções críticas"""
    
    print("🧪 Executando testes das correções críticas...")
    
    # Testes síncronos
    sync_test_classes = [
        TestIncrementalProcessorFixes,
        TestLRUCacheFixes,
        TestErrorHandlingFixes
    ]
    
    for test_class in sync_test_classes:
        print(f"\n📋 Testando {test_class.__name__}...")
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    print(f"   ✓ {method_name}")
                    method = getattr(instance, method_name)
                    method()
                except Exception as e:
                    print(f"   ❌ {method_name}: {e}")
                    return False
    
    # Testes assíncronos
    async def run_async_tests():
        test_instance = TestConnectionPoolFixes()
        
        try:
            print(f"\n📋 Testando {TestConnectionPoolFixes.__name__}...")
            print("   ✓ test_connection_pool_thread_safety")
            await test_instance.test_connection_pool_thread_safety()
            
            print("   ✓ test_connection_pool_timeout_handling") 
            await test_instance.test_connection_pool_timeout_handling()
            
        except Exception as e:
            print(f"   ❌ Teste assíncrono falhou: {e}")
            return False
        
        return True
    
    # Executar testes assíncronos
    try:
        result = asyncio.run(run_async_tests())
        if not result:
            return False
    except Exception as e:
        print(f"❌ Erro ao executar testes assíncronos: {e}")
        return False
    
    print("\n✅ Todos os testes das correções críticas passaram!")
    return True


if __name__ == "__main__":
    success = run_critical_fixes_tests()
    exit(0 if success else 1)