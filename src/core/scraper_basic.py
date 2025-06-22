"""
Scraper Básico - Versão sem dependências ML

Scraper simplificado que funciona sem scikit-learn, numpy avançado
ou outras dependências de machine learning.
"""

import asyncio
import time
from typing import List, Dict
from playwright.async_api import async_playwright
from ..utils.menu_system import Colors


async def scrape_catho_jobs_basic(
    max_concurrent_jobs: int = 3, 
    max_pages: int = 5,
    multi_mode: bool = False
) -> List[Dict]:
    """
    Scraping básico sem dependências ML
    
    Args:
        multi_mode: Se True, busca em home office + presencial + híbrido
                   Se False, apenas home office
    """
    
    # URLs para diferentes modalidades
    if multi_mode:
        urls_to_search = [
            ("Home Office", "https://www.catho.com.br/vagas/home-office/"),
            ("Presencial", "https://www.catho.com.br/vagas/presencial/"),
            ("Híbrido", "https://www.catho.com.br/vagas/hibrido/"),
        ]
        print(f"{Colors.CYAN}🌍 Modo múltiplas modalidades ativado{Colors.RESET}")
    else:
        urls_to_search = [
            ("Home Office", "https://www.catho.com.br/vagas/home-office/")
        ]
        print(f"{Colors.CYAN}🏠 Modo home office exclusivo{Colors.RESET}")
    
    all_jobs = []
    
    try:
        async with async_playwright() as p:
            print(f"{Colors.GREEN}🚀 Iniciando navegador (modo básico)...{Colors.RESET}")
            
            # Configuração básica do browser
            browser = await p.chromium.launch(
                headless=True,  # Modo headless para performance
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            # Criar página principal
            page = await browser.new_page()
            page.set_default_timeout(20000)
            
            try:
                # Processar cada modalidade
                for mode_name, base_url in urls_to_search:
                    print(f"\n{Colors.YELLOW}🎯 === MODALIDADE: {mode_name.upper()} ==={Colors.RESET}")
                    
                    mode_jobs = await scrape_basic_mode(
                        page, base_url, mode_name, max_pages
                    )
                    
                    if mode_jobs:
                        all_jobs.extend(mode_jobs)
                        print(f"{Colors.GREEN}✅ {mode_name}: {len(mode_jobs)} vagas coletadas{Colors.RESET}")
                    else:
                        print(f"{Colors.YELLOW}⚠️ {mode_name}: Nenhuma vaga encontrada{Colors.RESET}")
                
                # Fechar página
                await page.close()
                
                print(f"\n{Colors.GREEN}🎉 BUSCA BÁSICA CONCLUÍDA!{Colors.RESET}")
                print(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}")
                print(f"📊 Total coletado: {len(all_jobs)} vagas")
                
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
        
        return []


async def scrape_basic_mode(
    page, 
    base_url: str, 
    mode_name: str, 
    max_pages: int
) -> List[Dict]:
    """Scraping básico de uma modalidade específica"""
    
    mode_jobs = []
    
    for current_page in range(1, min(max_pages + 1, 4)):  # Limitado a 3 páginas para modo básico
        print(f"\n{Colors.CYAN}📄 {mode_name} - Página {current_page}{Colors.RESET}")
        
        try:
            # Construir URL da página
            if current_page == 1:
                page_url = base_url
            else:
                page_url = f"{base_url}?page={current_page}"
            
            print(f"🌐 Navegando para: {page_url}")
            
            # Navegar com timeout mais baixo
            try:
                await page.goto(page_url, wait_until='domcontentloaded', timeout=20000)
                await page.wait_for_timeout(2000)
            except Exception as nav_error:
                print(f"⚠️ Erro na navegação: {nav_error}")
                continue
            
            # Extrair vagas da página
            page_jobs = await extract_basic_jobs(page, mode_name)
            
            if page_jobs:
                mode_jobs.extend(page_jobs)
                print(f"{Colors.GREEN}✅ {mode_name} P{current_page}: {len(page_jobs)} vagas{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}⚠️ {mode_name} P{current_page}: Nenhuma vaga{Colors.RESET}")
                break
            
            # Delay entre páginas
            await asyncio.sleep(1)
        
        except Exception as page_error:
            print(f"{Colors.RED}❌ Erro na página {current_page} de {mode_name}: {page_error}{Colors.RESET}")
            continue
    
    return mode_jobs


async def extract_basic_jobs(page, mode_name: str) -> List[Dict]:
    """Extrai vagas básicas da página"""
    
    jobs = []
    
    try:
        print(f"{Colors.GRAY}🔍 Procurando vagas em {mode_name}...{Colors.RESET}")
        
        # Aguardar elementos carregarem com timeout baixo
        try:
            await page.wait_for_selector('a[href*="/vagas/"]', timeout=5000)
        except:
            print(f"{Colors.YELLOW}⚠️ Elementos não encontrados rapidamente{Colors.RESET}")
        
        # Seletores básicos para encontrar vagas
        selectors_to_try = [
            'a[href*="/vagas/"]',
            'h2 a',
            '.job-title a',
            '[data-testid*="job"] a'
        ]
        
        job_elements = []
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 2:  # Pelo menos algumas vagas
                    job_elements = elements
                    break
            except:
                continue
        
        if not job_elements:
            return []
        
        print(f"{Colors.GRAY}📝 Processando {len(job_elements)} elementos de {mode_name}...{Colors.RESET}")
        
        # Processar elementos (máximo 15 por página no modo básico)
        processed = 0
        for element in job_elements[:15]:
            try:
                # Extrair link
                link = await element.get_attribute('href')
                if not link or 'vagas' not in link:
                    continue
                
                # Garantir URL absoluta
                if link.startswith('/'):
                    link = f"https://www.catho.com.br{link}"
                
                # Extrair título
                title_text = await element.text_content()
                if not title_text or len(title_text.strip()) < 3:
                    title_text = 'Vaga não identificada'
                
                # Limpar título
                title_text = title_text.strip()[:100]
                
                # Criar objeto de vaga básico
                job = {
                    'titulo': title_text,
                    'link': link,
                    'empresa': 'Empresa não identificada',
                    'localizacao': mode_name,
                    'salario': 'Não informado',
                    'regime': mode_name,
                    'modalidade_trabalho': mode_name,
                    'nivel': 'Não especificado',
                    'tecnologias_detectadas': [],
                    'data_coleta': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'fonte': f'catho_basic_{mode_name.lower().replace(" ", "_")}',
                    'fonte_categoria': mode_name,
                    'tipo_coleta': 'básica_sem_ml'
                }
                
                jobs.append(job)
                processed += 1
                
                # Limite para modo básico
                if processed >= 10:
                    break
                
            except Exception as element_error:
                continue
        
        print(f"{Colors.GREEN}✅ {mode_name}: {len(jobs)} vagas extraídas (modo básico){Colors.RESET}")
        return jobs
        
    except Exception as e:
        print(f"{Colors.RED}❌ Erro na extração básica de {mode_name}: {e}{Colors.RESET}")
        return []


async def check_basic_catho_accessibility() -> bool:
    """
    Verificação básica de acessibilidade do Catho
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            page.set_default_timeout(10000)
            
            try:
                await page.goto("https://www.catho.com.br/", wait_until='domcontentloaded')
                title = await page.title()
                is_accessible = "catho" in title.lower()
                await browser.close()
                return is_accessible
            except:
                await browser.close()
                return False
    except:
        return False