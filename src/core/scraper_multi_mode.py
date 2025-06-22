"""
Scraper Multi-Modalidade - Busca em Home Office + Presencial + Híbrido

Expande a busca para além de home office, cobrindo todas as modalidades
de trabalho disponíveis no Catho.
"""

import asyncio
import time
from typing import List, Dict
from playwright.async_api import async_playwright

from ..utils.utils import RateLimiter, PerformanceMonitor
from ..utils.menu_system import Colors


async def check_catho_accessibility() -> bool:
    """
    Verifica se o site Catho está acessível
    
    Returns:
        bool: True se acessível, False caso contrário
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            page = await browser.new_page()
            page.set_default_timeout(15000)
            
            try:
                # Tentar acessar página principal do Catho
                await page.goto("https://www.catho.com.br/vagas/home-office/", wait_until='networkidle')
                
                # Verificar se a página carregou corretamente
                title = await page.title()
                is_accessible = "catho" in title.lower() and "erro" not in title.lower()
                
                await browser.close()
                return is_accessible
                
            except Exception:
                await browser.close()
                return False
                
    except Exception:
        return False


async def scrape_catho_jobs_multi_mode(
    max_concurrent_jobs: int = 3, 
    max_pages: int = 5,
    multi_mode: bool = False
) -> List[Dict]:
    """
    Scraping com múltiplas modalidades de trabalho
    
    Args:
        multi_mode: Se True, busca em home office + presencial + híbrido
                   Se False, apenas home office (comportamento original)
    """
    
    # URLs para diferentes modalidades
    if multi_mode:
        urls_to_search = [
            ("Home Office", "https://www.catho.com.br/vagas/home-office/"),
            ("Presencial", "https://www.catho.com.br/vagas/presencial/"),
            ("Híbrido", "https://www.catho.com.br/vagas/hibrido/"),
        ]
        print(f"{Colors.CYAN}🌍 Modo múltiplas modalidades ativado{Colors.RESET}")
        print(f"{Colors.GRAY}   Buscando em: Home Office, Presencial e Híbrido{Colors.RESET}")
    else:
        urls_to_search = [
            ("Home Office", "https://www.catho.com.br/vagas/home-office/")
        ]
        print(f"{Colors.CYAN}🏠 Modo home office exclusivo{Colors.RESET}")
    
    # Inicializar apenas sistemas essenciais
    rate_limiter = RateLimiter(requests_per_second=1.0, burst_limit=3, adaptive=True)
    performance_monitor = PerformanceMonitor()
    performance_monitor.start_monitoring()
    
    all_jobs = []
    
    try:
        async with async_playwright() as p:
            print(f"{Colors.GREEN}🚀 Iniciando navegador (modo multi-modalidade)...{Colors.RESET}")
            
            # Configuração robusta do browser
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ],
                slow_mo=150  # Delay entre ações para estabilidade
            )
            
            # Criar página principal
            page = await browser.new_page()
            page.set_default_timeout(30000)
            page.set_default_navigation_timeout(60000)
            
            try:
                # Processar cada modalidade
                for mode_name, base_url in urls_to_search:
                    print(f"\n{Colors.YELLOW}🎯 === MODALIDADE: {mode_name.upper()} ==={Colors.RESET}")
                    print(f"{Colors.GRAY}Base URL: {base_url}{Colors.RESET}")
                    
                    mode_jobs = await scrape_single_mode(
                        page, base_url, mode_name, max_pages, rate_limiter
                    )
                    
                    if mode_jobs:
                        all_jobs.extend(mode_jobs)
                        print(f"{Colors.GREEN}✅ {mode_name}: {len(mode_jobs)} vagas coletadas{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}⚠️ {mode_name}: Nenhuma vaga encontrada{Colors.RESET}")
                
                # Fechar página
                await page.close()
                
                print(f"\n{Colors.GREEN}🎉 BUSCA MULTI-MODALIDADE CONCLUÍDA!{Colors.RESET}")
                print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
                print(f"📊 Total coletado: {len(all_jobs)} vagas")
                
                # Mostrar distribuição por modalidade
                mode_distribution = {}
                for job in all_jobs:
                    mode = job.get('modalidade_trabalho', 'Não especificada')
                    mode_distribution[mode] = mode_distribution.get(mode, 0) + 1
                
                if mode_distribution:
                    print(f"\n📊 DISTRIBUIÇÃO POR MODALIDADE:")
                    for mode, count in mode_distribution.items():
                        print(f"   🔹 {mode}: {count} vagas")
                
                # Mostrar estatísticas
                performance_monitor.print_stats()
                
                return all_jobs
                
            except Exception as scraping_error:
                print(f"{Colors.RED}❌ Erro durante scraping: {scraping_error}{Colors.RESET}")
                return all_jobs
            
            finally:
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
        else:
            print(f"{Colors.RED}❌ Erro inesperado: {e}{Colors.RESET}")
            import traceback
            traceback.print_exc()
        
        return []


async def scrape_single_mode(
    page, 
    base_url: str, 
    mode_name: str, 
    max_pages: int, 
    rate_limiter: RateLimiter
) -> List[Dict]:
    """Scraping de uma modalidade específica"""
    
    mode_jobs = []
    
    for current_page in range(1, max_pages + 1):
        print(f"\n{Colors.CYAN}📄 {mode_name} - Página {current_page}{Colors.RESET}")
        
        try:
            # Construir URL da página
            if current_page == 1:
                page_url = base_url
            else:
                page_url = f"{base_url}?page={current_page}"
            
            print(f"🌐 Navegando para: {page_url}")
            
            # Navegar com retry
            page_loaded = False
            for attempt in range(3):
                try:
                    await page.goto(page_url, wait_until='networkidle', timeout=45000)
                    await page.wait_for_timeout(2000)
                    page_loaded = True
                    break
                except Exception as nav_error:
                    print(f"⚠️ Tentativa {attempt + 1}/3 falhou: {nav_error}")
                    if attempt < 2:
                        await asyncio.sleep(3)
            
            if not page_loaded:
                print(f"{Colors.YELLOW}⏭️ Pulando página {current_page} de {mode_name}{Colors.RESET}")
                continue
            
            # Verificar se chegou ao fim das páginas
            title = await page.title()
            if "não encontrada" in title.lower() or "404" in title:
                print(f"{Colors.YELLOW}📄 Fim das páginas para {mode_name}{Colors.RESET}")
                break
            
            # Extrair vagas da página
            page_jobs = await extract_jobs_with_mode(page, mode_name)
            
            if page_jobs:
                mode_jobs.extend(page_jobs)
                print(f"{Colors.GREEN}✅ {mode_name} P{current_page}: {len(page_jobs)} vagas{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠️ {mode_name} P{current_page}: Nenhuma vaga{Colors.RESET}")
                # Se 2 páginas consecutivas vazias, parar
                if current_page > 1:
                    break
            
            # Rate limiting entre páginas
            if current_page < max_pages:
                await rate_limiter.acquire()
        
        except Exception as page_error:
            print(f"{Colors.RED}❌ Erro na página {current_page} de {mode_name}: {page_error}{Colors.RESET}")
            continue
    
    return mode_jobs


async def extract_jobs_with_mode(page, mode_name: str) -> List[Dict]:
    """Extrai vagas da página incluindo informação de modalidade"""
    
    jobs = []
    
    try:
        print(f"{Colors.GRAY}🔍 Procurando vagas em {mode_name}...{Colors.RESET}")
        
        # Aguardar elementos carregarem
        try:
            await page.wait_for_selector('h2 a[href*="/vagas/"]', timeout=10000)
        except:
            print(f"{Colors.YELLOW}⚠️ Elementos de vaga não encontrados rapidamente{Colors.RESET}")
        
        # Seletores para encontrar vagas
        selectors_to_try = [
            'h2 a[href*="/vagas/"]',
            'a[href*="/vagas/"]',
            '.job-title a',
            '[data-testid*="job"] a',
        ]
        
        job_elements = []
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    job_elements = elements
                    break
            except:
                continue
        
        if not job_elements:
            return []
        
        print(f"{Colors.GRAY}📝 Processando {len(job_elements)} elementos de {mode_name}...{Colors.RESET}")
        
        # Processar elementos (máximo 25 por página)
        for i, element in enumerate(job_elements[:25]):
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
                
                # Criar objeto de vaga com modalidade
                job = {
                    'titulo': title_text.strip(),
                    'link': link,
                    'empresa': 'Empresa não identificada',
                    'localizacao': 'Não especificada',
                    'salario': 'Não informado',
                    'regime': mode_name,
                    'modalidade_trabalho': mode_name,  # Campo específico para modalidade
                    'nivel': 'Não especificado',
                    'tecnologias_detectadas': [],
                    'data_coleta': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'fonte': f'catho_multi_mode_{mode_name.lower().replace(" ", "_")}',
                    'fonte_categoria': mode_name
                }
                
                jobs.append(job)
                
            except Exception as element_error:
                continue
        
        print(f"{Colors.GREEN}✅ {mode_name}: {len(jobs)} vagas extraídas{Colors.RESET}")
        return jobs
        
    except Exception as e:
        print(f"{Colors.RED}❌ Erro na extração de {mode_name}: {e}{Colors.RESET}")
        return []