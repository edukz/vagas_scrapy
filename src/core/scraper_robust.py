"""
Scraper Robusto - Versão sem Pool de Conexões

Sistema de scraping simplificado e robusto que funciona sem
dependências complexas de pools ou sistemas ML.
"""

import asyncio
import time
from typing import List, Dict
from playwright.async_api import async_playwright

from ..utils.utils import RateLimiter, PerformanceMonitor
from ..utils.menu_system import Colors


async def scrape_catho_jobs_robust(max_concurrent_jobs: int = 3, max_pages: int = 5) -> List[Dict]:
    """
    Função de scraping robusta - sem pool de conexões
    
    Esta versão evita problemas de timeout do pool usando
    uma abordagem mais simples e confiável.
    """
    base_url = "https://www.catho.com.br/vagas/home-office/"
    
    print(f"{Colors.CYAN}🔧 Scraper robusto iniciado (sem pool de conexões){Colors.RESET}")
    print(f"{Colors.GRAY}   Configuração: {max_pages} páginas, {max_concurrent_jobs} jobs simultâneos{Colors.RESET}")
    
    # Inicializar apenas sistemas essenciais
    rate_limiter = RateLimiter(requests_per_second=1.5, burst_limit=3, adaptive=True)
    performance_monitor = PerformanceMonitor()
    performance_monitor.start_monitoring()
    
    all_jobs = []
    
    try:
        async with async_playwright() as p:
            print(f"{Colors.GREEN}🚀 Iniciando navegador (modo robusto)...{Colors.RESET}")
            
            # Configuração mais robusta do browser
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',  # Reduzir uso de memória
                    '--disable-gpu',  # Evitar problemas de GPU
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ],
                slow_mo=100  # Adicionar pequeno delay entre ações
            )
            
            # Criar apenas uma página principal
            page = await browser.new_page()
            
            # Configurar timeouts mais generosos
            page.set_default_timeout(30000)  # 30 segundos
            page.set_default_navigation_timeout(60000)  # 60 segundos
            
            try:
                print(f"\n{Colors.YELLOW}📄 Processando páginas 1-{max_pages}...{Colors.RESET}")
                
                for current_page in range(1, max_pages + 1):
                    print(f"\n{Colors.CYAN}📄 === PÁGINA {current_page} ==={Colors.RESET}")
                    
                    try:
                        # Construir URL da página
                        if current_page == 1:
                            page_url = base_url
                        else:
                            page_url = f"{base_url}?page={current_page}"
                        
                        print(f"🌐 Navegando para: {page_url}")
                        
                        # Navegar com retry
                        max_retries = 3
                        page_loaded = False
                        
                        for attempt in range(max_retries):
                            try:
                                await page.goto(page_url, wait_until='networkidle', timeout=45000)
                                await page.wait_for_timeout(2000)  # Aguardar carregamento
                                page_loaded = True
                                break
                            except Exception as nav_error:
                                print(f"⚠️ Tentativa {attempt + 1}/{max_retries} falhou: {nav_error}")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(3)
                                else:
                                    print(f"{Colors.RED}❌ Falha ao carregar página {current_page} após {max_retries} tentativas{Colors.RESET}")
                        
                        if not page_loaded:
                            print(f"{Colors.YELLOW}⏭️ Pulando página {current_page}{Colors.RESET}")
                            continue
                        
                        # Verificar se a página carregou corretamente
                        title = await page.title()
                        print(f"📑 Título: {title}")
                        
                        # Extrair vagas da página atual
                        page_jobs = await extract_jobs_from_page_robust(page)
                        
                        if page_jobs:
                            all_jobs.extend(page_jobs)
                            print(f"{Colors.GREEN}✅ Página {current_page}: {len(page_jobs)} vagas coletadas{Colors.RESET}")
                            performance_monitor.record_job_processed()
                        else:
                            print(f"{Colors.YELLOW}⚠️ Página {current_page}: Nenhuma vaga encontrada{Colors.RESET}")
                        
                        # Rate limiting entre páginas
                        if current_page < max_pages:
                            print(f"{Colors.GRAY}⏳ Aguardando rate limit...{Colors.RESET}")
                            await rate_limiter.acquire()
                        
                    except Exception as page_error:
                        print(f"{Colors.RED}❌ Erro na página {current_page}: {page_error}{Colors.RESET}")
                        continue
                
                # Fechar página
                await page.close()
                
                print(f"\n{Colors.GREEN}✅ Scraping concluído!{Colors.RESET}")
                print(f"📊 Total coletado: {len(all_jobs)} vagas")
                
                # Mostrar estatísticas
                performance_monitor.print_stats()
                
                return all_jobs
                
            except Exception as scraping_error:
                print(f"{Colors.RED}❌ Erro durante scraping: {scraping_error}{Colors.RESET}")
                return all_jobs
            
            finally:
                # Cleanup sempre executado
                try:
                    await browser.close()
                    print(f"{Colors.GRAY}🔄 Browser fechado{Colors.RESET}")
                except:
                    pass
    
    except Exception as e:
        if "Executable doesn't exist" in str(e):
            print(f"{Colors.RED}❌ ERRO: Navegadores do Playwright não encontrados!{Colors.RESET}")
            print(f"{Colors.YELLOW}📋 SOLUÇÃO:{Colors.RESET}")
            print("   1. Abra o prompt do Windows (cmd)")
            print("   2. Execute: python -m playwright install")
            print("   3. Aguarde a instalação dos navegadores")
            print("   4. Execute o script novamente")
            print(f"\n{Colors.CYAN}💡 Isso só precisa ser feito uma vez.{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ Erro inesperado: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
        
        return []


async def extract_jobs_from_page_robust(page) -> List[Dict]:
    """
    Extrai vagas da página atual - versão robusta
    """
    jobs = []
    
    try:
        print(f"{Colors.GRAY}🔍 Procurando elementos de vagas...{Colors.RESET}")
        
        # Aguardar elementos carregarem
        try:
            await page.wait_for_selector('h2 a[href*="/vagas/"]', timeout=10000)
        except:
            print(f"{Colors.YELLOW}⚠️ Seletores de vaga não encontrados rapidamente{Colors.RESET}")
        
        # Procurar links de vagas com diferentes seletores
        selectors_to_try = [
            'h2 a[href*="/vagas/"]',  # Seletor principal
            'a[href*="/vagas/"]',     # Seletor mais amplo
            '.job-title a',           # Seletor alternativo
            '[data-testid*="job"] a', # Seletor por test-id
        ]
        
        job_elements = []
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    job_elements = elements
                    print(f"{Colors.GREEN}✓ Encontrados {len(elements)} elementos com seletor: {selector}{Colors.RESET}")
                    break
            except Exception as selector_error:
                print(f"{Colors.GRAY}⚠️ Seletor {selector} falhou: {selector_error}{Colors.RESET}")
                continue
        
        if not job_elements:
            print(f"{Colors.YELLOW}⚠️ Nenhum elemento de vaga encontrado na página{Colors.RESET}")
            return []
        
        print(f"{Colors.CYAN}📝 Processando {len(job_elements)} elementos...{Colors.RESET}")
        
        # Processar apenas os primeiros 20 elementos para evitar timeout
        for i, element in enumerate(job_elements[:20]):
            try:
                # Extrair link
                link = await element.get_attribute('href')
                if not link:
                    continue
                
                # Garantir URL absoluta
                if link.startswith('/'):
                    link = f"https://www.catho.com.br{link}"
                
                # Extrair título
                title_text = await element.text_content()
                if not title_text:
                    title_text = await element.get_attribute('title') or 'Título não encontrado'
                
                # Criar objeto de vaga básico
                job = {
                    'titulo': title_text.strip(),
                    'link': link,
                    'empresa': 'Empresa não identificada',
                    'localizacao': 'Home Office',
                    'salario': 'Não informado',
                    'regime': 'Home Office',
                    'nivel': 'Não especificado',
                    'tecnologias_detectadas': [],
                    'data_coleta': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'fonte': 'catho_robust_scraper'
                }
                
                jobs.append(job)
                
                # Log a cada 5 vagas processadas
                if (i + 1) % 5 == 0:
                    print(f"{Colors.GRAY}   📝 Processadas {i + 1}/{len(job_elements[:20])} vagas{Colors.RESET}")
                
            except Exception as element_error:
                print(f"{Colors.GRAY}⚠️ Erro ao processar elemento {i}: {element_error}{Colors.RESET}")
                continue
        
        print(f"{Colors.GREEN}✅ Extraídas {len(jobs)} vagas da página{Colors.RESET}")
        return jobs
        
    except Exception as e:
        print(f"{Colors.RED}❌ Erro na extração: {e}{Colors.RESET}")
        return []


# Função para verificar se o site está acessível
async def check_catho_accessibility() -> bool:
    """Verifica se o site do Catho está acessível"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            response = await page.goto("https://www.catho.com.br/vagas/home-office/", timeout=15000)
            
            if response and response.status == 200:
                title = await page.title()
                await browser.close()
                
                if "catho" in title.lower() or "vagas" in title.lower():
                    return True
                    
            await browser.close()
            
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️ Verificação de acessibilidade falhou: {e}{Colors.RESET}")
    
    return False