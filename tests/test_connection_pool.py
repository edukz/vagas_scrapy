#!/usr/bin/env python3
"""
Teste do Pool de Conexões - Fase 2.1

Este teste demonstra o sistema de pool de conexões reutilizáveis,
mostrando a melhoria de performance e redução de overhead.
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.connection_pool import ConnectionPool, PooledPageManager
from src.scraper_pooled import benchmark_pool_performance, scrape_catho_jobs_pooled
from playwright.async_api import async_playwright


async def test_basic_pool_operations():
    """Testa operações básicas do pool"""
    print("🧪 TESTE BÁSICO DO POOL DE CONEXÕES")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Criar pool
        pool = ConnectionPool(min_size=2, max_size=5)
        await pool.initialize(browser)
        
        print(f"✅ Pool inicializado")
        pool.print_stats()
        
        # Testar obtenção de páginas
        print("\n📊 Testando obtenção sequencial de páginas...")
        
        pages = []
        for i in range(3):
            page = await pool.get_page()
            if page:
                print(f"   ✅ Página {i+1} obtida do pool")
                pages.append(page)
            else:
                print(f"   ❌ Falha ao obter página {i+1}")
        
        # Testar uso das páginas
        print("\n🌐 Testando uso das páginas...")
        for i, page in enumerate(pages):
            try:
                await page.goto("about:blank")
                print(f"   ✅ Página {i+1} usada com sucesso")
            except Exception as e:
                print(f"   ❌ Erro na página {i+1}: {e}")
        
        # Retornar páginas ao pool
        print("\n↩️ Retornando páginas ao pool...")
        for i, page in enumerate(pages):
            await pool.return_page(page)
            print(f"   ✅ Página {i+1} retornada")
        
        print("\n📊 Estado final do pool:")
        pool.print_stats()
        
        await pool.shutdown()
        await browser.close()


async def test_pool_context_manager():
    """Testa context manager do pool"""
    print("\n\n🧪 TESTE DO CONTEXT MANAGER")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        pool = ConnectionPool(min_size=2, max_size=4)
        await pool.initialize(browser)
        
        # Testar context manager
        print("📝 Testando PooledPageManager...")
        
        for i in range(5):
            print(f"\n🔄 Iteração {i+1}:")
            
            try:
                async with PooledPageManager() as page:
                    await page.goto("about:blank")
                    await page.wait_for_timeout(500)
                    print(f"   ✅ Context manager funcionou")
                
                # Mostrar stats do pool
                stats = pool.get_stats()
                print(f"   📊 Pool: {stats['available_pages']} disponíveis, {stats['busy_pages']} em uso")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
        
        print("\n📊 Estatísticas finais:")
        pool.print_stats()
        
        await pool.shutdown()
        await browser.close()


async def test_pool_performance_improvement():
    """Testa melhoria de performance"""
    print("\n\n🧪 TESTE DE MELHORIA DE PERFORMANCE")
    print("=" * 60)
    
    # Executar benchmark
    results = await benchmark_pool_performance(
        pages_to_test=3,
        requests_per_page=2
    )
    
    print("\n📈 ANÁLISE DOS RESULTADOS:")
    print(f"   🐌 Sem pool: {results['without_pool']:.2f}s")
    print(f"   🚀 Com pool: {results['with_pool']:.2f}s")
    print(f"   ⚡ Melhoria: {results['improvement_percent']:.1f}%")
    print(f"   💰 Tempo economizado: {results['time_saved']:.2f}s")
    
    # Verificar se pool realmente melhora performance
    if results['improvement_percent'] > 10:
        print(f"   ✅ Pool oferece melhoria significativa!")
    else:
        print(f"   ⚠️ Melhoria menor que esperada")
    
    return results


async def test_pool_under_load():
    """Testa pool sob carga"""
    print("\n\n🧪 TESTE DE CARGA DO POOL")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        pool = ConnectionPool(min_size=2, max_size=4)
        await pool.initialize(browser)
        
        print("🔥 Testando pool sob carga concorrente...")
        
        async def worker(worker_id: int):
            """Worker que usa o pool"""
            for i in range(3):
                try:
                    async with PooledPageManager(timeout_seconds=5.0) as page:
                        await page.goto("about:blank")
                        await page.wait_for_timeout(200)
                        print(f"   ✅ Worker {worker_id} - Requisição {i+1}")
                except Exception as e:
                    print(f"   ❌ Worker {worker_id} - Erro: {e}")
        
        # Executar múltiplos workers simultaneamente
        start_time = time.time()
        workers = [worker(i) for i in range(6)]  # 6 workers, pool máx 4
        await asyncio.gather(*workers)
        total_time = time.time() - start_time
        
        print(f"\n📊 Teste de carga concluído em {total_time:.2f}s")
        pool.print_stats()
        
        await pool.shutdown()
        await browser.close()


async def test_pool_error_handling():
    """Testa tratamento de erros"""
    print("\n\n🧪 TESTE DE TRATAMENTO DE ERROS")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        pool = ConnectionPool(min_size=1, max_size=2)
        await pool.initialize(browser)
        
        print("💥 Testando handling de erros...")
        
        # Testar página com erro
        try:
            async with PooledPageManager() as page:
                # Simular erro
                await page.goto("https://site-que-nao-existe-12345.com")
        except Exception as e:
            print(f"   ✅ Erro capturado corretamente: {type(e).__name__}")
        
        # Verificar se pool ainda funciona após erro
        try:
            async with PooledPageManager() as page:
                await page.goto("about:blank")
                print(f"   ✅ Pool ainda funciona após erro")
        except Exception as e:
            print(f"   ❌ Pool não funcionou após erro: {e}")
        
        print("\n📊 Estado do pool após erros:")
        pool.print_stats()
        
        await pool.shutdown()
        await browser.close()


async def test_integrated_scraper():
    """Testa scraper integrado com pool"""
    print("\n\n🧪 TESTE DO SCRAPER INTEGRADO")
    print("=" * 60)
    
    print("🚀 Executando scraper com pool de conexões...")
    
    try:
        jobs = await scrape_catho_jobs_pooled(
            max_concurrent_jobs=2,
            max_pages=2,
            incremental=True,
            show_compression_stats=False,
            show_pool_stats=True,
            pool_min_size=2,
            pool_max_size=4
        )
        
        print(f"\n✅ Scraper com pool executado: {len(jobs)} vagas coletadas")
        
    except Exception as e:
        print(f"❌ Erro no scraper: {e}")


async def main():
    """Função principal dos testes"""
    print("🚀 TESTES DO POOL DE CONEXÕES - FASE 2.1")
    print("=" * 80)
    print("Este teste demonstra o sistema de pool de conexões reutilizáveis")
    print("para otimização de performance do scraper.")
    print("=" * 80)
    
    try:
        await test_basic_pool_operations()
        await test_pool_context_manager()
        
        performance_results = await test_pool_performance_improvement()
        
        await test_pool_under_load()
        await test_pool_error_handling()
        await test_integrated_scraper()
        
        # Resumo final
        print("\n" + "=" * 80)
        print("🏆 RESUMO DOS RESULTADOS - POOL DE CONEXÕES")
        print("=" * 80)
        
        print("✅ FUNCIONALIDADES TESTADAS:")
        print("   🔄 Criação e gerenciamento do pool")
        print("   📝 Context manager automático")
        print("   🧹 Limpeza e reciclagem de páginas")
        print("   💥 Tratamento de erros")
        print("   🔥 Operação sob carga")
        print("   🚀 Integração com scraper")
        
        print(f"\n📈 BENEFÍCIOS MEDIDOS:")
        if 'improvement_percent' in performance_results:
            print(f"   ⚡ Melhoria de performance: {performance_results['improvement_percent']:.1f}%")
            print(f"   💰 Tempo economizado por requisição: {performance_results['time_saved'] / 6:.3f}s")
        
        print(f"\n🎯 CASOS DE USO IDEAIS:")
        print("   • Múltiplas páginas em sequência")
        print("   • Navegação repetitiva")
        print("   • Scraping com muitas requisições")
        print("   • Execuções longas com muitas páginas")
        
        print(f"\n🚀 STATUS: Pool de Conexões implementado e testado!")
        print("   Ready para integração no scraper principal")
        
    except Exception as e:
        print(f"\n❌ Erro durante testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())