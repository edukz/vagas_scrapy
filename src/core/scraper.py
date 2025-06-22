import asyncio
import re
import time
from typing import List, Dict
from playwright.async_api import async_playwright
from ..systems.cache import IntelligentCache
from ..utils.utils import RateLimiter, PerformanceMonitor
from ..systems.navigation import PageNavigatorFixed as PageNavigator
from ..systems.retry_system import RetrySystem, STRATEGIES
from ..systems.selector_fallback import fallback_selector
from ..systems.data_validator import data_validator
from ..systems.structured_logger import structured_logger, Component, LogLevel
from ..systems.circuit_breaker import circuit_breaker_manager, CIRCUIT_CONFIGS, CircuitBreakerError
from ..systems.metrics_tracker import metrics_tracker, setup_default_alerts, TimerContext
from ..systems.alert_system import alert_system, setup_default_alert_rules, integrate_with_metrics


async def scrape_catho_jobs(max_concurrent_jobs: int = 3, max_pages: int = 5) -> List[Dict]:
    """
    Função principal de scraping - versão com robustez enterprise
    """
    base_url = "https://www.catho.com.br/vagas/home-office/"
    
    # Inicializar sistemas de robustez
    cache = IntelligentCache()
    rate_limiter = RateLimiter(requests_per_second=2.0, burst_limit=5, adaptive=True)
    performance_monitor = PerformanceMonitor()
    navigator = PageNavigator(max_pages=max_pages)
    retry_system = RetrySystem(default_strategy=STRATEGIES['standard'])
    
    print("📊 Monitoramento de performance iniciado")
    print("🛡️ Sistema de retry ativado para maior robustez")
    print("🔧 Circuit Breakers configurados para proteção automática")
    print("📊 Sistema de métricas ativado para monitoramento em tempo real")
    
    # Configurar alertas e métricas
    setup_default_alerts()
    setup_default_alert_rules()
    integrate_with_metrics()
    alert_system.start_background_monitoring()
    
    print("🚨 Sistema de alertas automáticos configurado e ativo")
    
    try:
        with TimerContext("scraper.total_duration"):
            async with async_playwright() as p:
                print("🚀 Iniciando navegador otimizado com navegação multi-página...")
                browser = await p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--no-sandbox'
                    ]
                )
                
                page = await browser.new_page()
                detail_pages = []
                for i in range(max_concurrent_jobs):
                    detail_page = await browser.new_page()
                    detail_pages.append(detail_page)
                
                try:
                    print(f"🌐 Iniciando coleta de múltiplas páginas (máx: {max_pages} páginas)")
                    
                    all_jobs = []
                    seen_urls = set()
                    current_page = 1
                    
                    # Primeira página
                    print(f"\n📄 === PÁGINA {current_page} ===")
                    await page.goto(base_url, wait_until='networkidle', timeout=60000)
                    await page.wait_for_timeout(3000)
                    
                    title = await page.title()
                    print(f"Título da página: {title}")
                    
                    # Detectar tipo de paginação
                    pagination_type = await navigator.detect_pagination_type(page)
                    print(f"🔍 Tipo de paginação detectado: {pagination_type}")
                    
                    # Processar primeira página
                    try:
                        page_jobs = await extract_jobs_from_current_page(page, seen_urls, retry_system)
                        all_jobs.extend(page_jobs)
                        print(f"✅ Página {current_page}: {len(page_jobs)} vagas coletadas")
                        
                        metrics_tracker.increment_counter("scraper.pages_processed")
                        metrics_tracker.increment_counter("scraper.jobs_found", len(page_jobs))
                        
                    except Exception as e:
                        print(f"🔴 Erro na página {current_page}: {e}")
                        metrics_tracker.increment_counter("scraper.pages_failed")
                        return []
                    
                    # Navegar pelas páginas restantes
                    if pagination_type != "single_page" and max_pages > 1:
                        if pagination_type == "traditional":
                            # Detectar número total de páginas
                            page_numbers = await navigator.get_page_numbers(page)
                            
                            if page_numbers:
                                # Usar max_pages do usuário, independente de quantas páginas o site tem
                                print(f"📊 Páginas disponíveis no site: {max(page_numbers)}")
                                print(f"📋 Páginas a processar (configurado): {max_pages}")
                                pages_to_try = list(range(2, max_pages + 1))
                            else:
                                print("⚠ Números de páginas não detectados, tentando navegação forçada...")
                                pages_to_try = list(range(2, max_pages + 1))
                            
                            for page_num in pages_to_try:
                                print(f"\n📄 === PÁGINA {page_num} ===")
                                
                                try:
                                    # Navegação para próxima página
                                    success = await navigator.navigate_to_page(page, page_num, base_url)
                                    
                                    if success:
                                        # Extração da página
                                        page_jobs = await extract_jobs_from_current_page(page, seen_urls, retry_system)
                                        all_jobs.extend(page_jobs)
                                        print(f"✅ Página {page_num}: {len(page_jobs)} vagas coletadas")
                                        
                                        # Registrar métricas da página
                                        metrics_tracker.increment_counter("scraper.pages_processed")
                                        metrics_tracker.increment_counter("scraper.jobs_found", len(page_jobs))
                                        
                                        # Rate limiting entre páginas
                                        await rate_limiter.acquire()
                                        
                                    else:
                                        print(f"❌ Falha ao navegar para página {page_num}")
                                        metrics_tracker.increment_counter("scraper.pages_failed")
                                        break
                                        
                                except Exception as e:
                                    print(f"🔴 Erro na página {page_num}: {e}")
                                    metrics_tracker.increment_counter("scraper.pages_failed")
                                    continue
                        
                        elif pagination_type == "next_button":
                            print("🔄 Navegação por botão 'próxima página' detectada")
                            current_page = 1
                            
                            while current_page < max_pages:
                                next_page = current_page + 1
                                print(f"\n📄 === PÁGINA {next_page} ===")
                                
                                try:
                                    # Tentar clicar no botão "próximo"
                                    success = await navigator.try_next_page_button(page)
                                    
                                    if success:
                                        page_jobs = await extract_jobs_from_current_page(page, seen_urls, retry_system)
                                        all_jobs.extend(page_jobs)
                                        print(f"✅ Página {next_page}: {len(page_jobs)} vagas coletadas")
                                        
                                        metrics_tracker.increment_counter("scraper.pages_processed")
                                        metrics_tracker.increment_counter("scraper.jobs_found", len(page_jobs))
                                        
                                        current_page = next_page
                                        await rate_limiter.acquire()
                                    else:
                                        print("❌ Não foi possível navegar para próxima página")
                                        break
                                        
                                except Exception as e:
                                    print(f"🔴 Erro na navegação por botão: {e}")
                                    break
                        
                        elif pagination_type == "infinite_scroll":
                            print("📜 Scroll infinito detectado - simulando múltiplas páginas")
                            
                            for scroll_attempt in range(2, min(max_pages + 1, 6)):  # Limitar scrolls
                                print(f"\n📄 === SCROLL {scroll_attempt} ===")
                                
                                try:
                                    # Simular scroll para carregar mais conteúdo
                                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                    await page.wait_for_timeout(3000)  # Aguardar carregamento
                                    
                                    page_jobs = await extract_jobs_from_current_page(page, seen_urls, retry_system)
                                    
                                    if page_jobs:
                                        all_jobs.extend(page_jobs)
                                        print(f"✅ Scroll {scroll_attempt}: {len(page_jobs)} novas vagas coletadas")
                                        
                                        metrics_tracker.increment_counter("scraper.pages_processed")
                                        metrics_tracker.increment_counter("scraper.jobs_found", len(page_jobs))
                                        
                                        await rate_limiter.acquire()
                                    else:
                                        print("❌ Nenhuma vaga nova encontrada após scroll")
                                        break
                                        
                                except Exception as e:
                                    print(f"🔴 Erro no scroll infinito: {e}")
                                    break
                    
                    print(f"\n✅ Coleta concluída! Total: {len(all_jobs)} vagas encontradas")
                    
                    # Cleanup
                    alert_system.stop_background_monitoring()
                    for detail_page in detail_pages:
                        await detail_page.close()
                    
                    print("🔄 Fechando navegador automaticamente...")
                    return all_jobs
                    
                except Exception as e:
                    print(f"Erro durante o scraping: {e}")
                    
                    # Cleanup em caso de erro com logging adequado
                    cleanup_errors = []
                    for detail_page in detail_pages:
                        try:
                            await detail_page.close()
                        except Exception as cleanup_error:
                            cleanup_errors.append(f"Erro ao fechar página: {cleanup_error}")
                    
                    if cleanup_errors:
                        print(f"⚠️ Problemas durante cleanup: {len(cleanup_errors)} erros")
                        for error in cleanup_errors[:3]:  # Mostrar apenas os 3 primeiros
                            print(f"   • {error}")
                        if len(cleanup_errors) > 3:
                            print(f"   • ... e mais {len(cleanup_errors) - 3} erros")
                    
                    return []
                
    except Exception as e:
        if "Executable doesn't exist" in str(e):
            print("❌ ERRO: Navegadores do Playwright não encontrados!")
            print("📋 SOLUÇÃO:")
            print("   1. Abra o prompt do Windows (cmd)")
            print("   2. Execute: python -m playwright install")
            print("   3. Aguarde a instalação dos navegadores")
            print("   4. Execute o script novamente")
            print("\n💡 Isso só precisa ser feito uma vez.")
            return []
        else:
            print(f"❌ Erro inesperado: {e}")
            return []


# Extract jobs function from current page (simplified version)
async def extract_jobs_from_current_page(page, seen_urls: set, retry_system: RetrySystem = None) -> List[Dict]:
    """Extract jobs from current page with simplified logic"""
    jobs = []
    
    try:
        # Find job links
        job_elements = await page.query_selector_all('h2 a[href*="/vagas/"]')
        
        for element in job_elements[:10]:  # Limit to first 10 for testing
            try:
                link = await element.get_attribute('href')
                title_text = await element.text_content()
                
                if link and link not in seen_urls:
                    seen_urls.add(link)
                    
                    job = {
                        'titulo': title_text or 'Título não encontrado',
                        'link': link,
                        'empresa': 'Empresa não identificada',
                        'localizacao': 'Home Office',
                        'salario': 'Não informado',
                        'regime': 'Home Office',
                        'nivel': 'Não especificado',
                        'tecnologias_detectadas': [],
                        'data_coleta': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    jobs.append(job)
                    
            except Exception as e:
                print(f"Erro ao processar elemento: {e}")
                continue
    
    except Exception as e:
        print(f"Erro na extração: {e}")
    
    return jobs