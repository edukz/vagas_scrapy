import asyncio
import re
import time
from typing import List, Dict
from playwright.async_api import async_playwright
from .cache import IntelligentCache
from .utils import RateLimiter, PerformanceMonitor
from .navigation import PageNavigator
from .retry_system import RetrySystem, STRATEGIES


async def extract_jobs_from_current_page(page, seen_urls: set, retry_system: RetrySystem = None) -> List[Dict]:
    """
    Extrai vagas da página atual com retry automático
    """
    async def _extract_jobs():
        jobs = []
        job_elements = await page.query_selector_all('h2 a[href*="/vagas/"]')
        
        for element in job_elements:
            try:
                job_title = await element.inner_text()
                job_link = await element.get_attribute('href')
                
                if not job_link or job_link in seen_urls:
                    continue
                
                if not re.search(r'/vagas/[^/]+/\d+/$', job_link):
                    continue
                
                skip_patterns = [
                    '/vagas/por-area/',
                    '/vagas/por-local/',
                    '/empresas/',
                    'buscar-vagas'
                ]
                
                if any(pattern in job_link for pattern in skip_patterns):
                    continue
                
                # Garantir URL completa
                if job_link.startswith('/'):
                    job_link = f"https://www.catho.com.br{job_link}"
                
                job_data = {
                    'titulo': job_title.strip(),
                    'link': job_link
                }
                
                jobs.append(job_data)
                seen_urls.add(job_link)
                
            except Exception as e:
                continue
        
        return jobs
    
    if retry_system:
        result = await retry_system.execute_with_retry(
            _extract_jobs, 
            strategy=STRATEGIES['standard'],
            operation_name="extract_jobs_from_page"
        )
        return result.result if result.success else []
    else:
        try:
            return await _extract_jobs()
        except Exception as e:
            print(f"❌ Erro ao extrair vagas da página: {e}")
            return []


async def extract_basic_info_from_jobs(page, jobs: List[Dict]) -> List[Dict]:
    """
    Extrai informações básicas das vagas da página de listagem
    """
    print(f"\n📋 Extraindo informações básicas de {len(jobs)} vagas...")
    
    for i, job in enumerate(jobs):
        try:
            # Tentar encontrar o article que contém a vaga
            article_selectors = [
                f'article:has(a[href*="{job["link"].split("/")[-2]}"])',
                f'div:has(a[href="{job["link"]}"])',
                f'[class*="job"]:has(a[href="{job["link"]}"])'
            ]
            
            article = None
            for selector in article_selectors:
                try:
                    article = await page.query_selector(selector)
                    if article:
                        break
                except:
                    continue
            
            if article:
                # Empresa
                empresa_selectors = [
                    'span.sc-gEvEer', 
                    '[class*="company"]', 
                    '[class*="empresa"]',
                    'span:has-text("Ltda")',
                    'span:has-text("S.A.")',
                    'div[class*="company"]'
                ]
                
                for selector in empresa_selectors:
                    try:
                        empresa_elem = await article.query_selector(selector)
                        if empresa_elem:
                            empresa = await empresa_elem.inner_text()
                            if empresa and len(empresa.strip()) > 2:
                                job['empresa'] = empresa.strip()
                                break
                    except:
                        continue
                
                if 'empresa' not in job:
                    job['empresa'] = 'Não informada'
                
                # Localização básica
                local_selectors = [
                    'button[title*="Local"]', 
                    '[class*="location"]', 
                    '[class*="local"]',
                    'span:has-text("Home Office")',
                    'span:has-text("Remoto")',
                    '[class*="cidade"]'
                ]
                
                for selector in local_selectors:
                    try:
                        local_elem = await article.query_selector(selector)
                        if local_elem:
                            local = await local_elem.inner_text()
                            if local and len(local.strip()) > 2:
                                job['localizacao'] = local.strip()
                                break
                    except:
                        continue
                
                if 'localizacao' not in job:
                    job['localizacao'] = 'Home Office'
            else:
                job['empresa'] = 'Não informada'
                job['localizacao'] = 'Home Office'
                
        except Exception as e:
            job['empresa'] = 'Não informada'
            job['localizacao'] = 'Home Office'
            
        # Progress indicator
        if (i + 1) % 20 == 0:
            print(f"  📝 {i + 1}/{len(jobs)} vagas processadas...")
    
    print(f"✅ Informações básicas extraídas de {len(jobs)} vagas")
    return jobs


async def scrape_job_details(page, job_url, cache: IntelligentCache = None, 
                            rate_limiter: RateLimiter = None, 
                            monitor: PerformanceMonitor = None,
                            retry_system: RetrySystem = None):
    """
    Extrai informações detalhadas de uma vaga específica com cache, rate limiting e retry automático
    """
    async def _scrape_with_retry():
        # Verificar cache primeiro
        if cache:
            cached_data = await cache.get(job_url)
            if cached_data:
                if monitor:
                    monitor.record_cache_hit()
                return cached_data
            elif monitor:
                monitor.record_cache_miss()
        
        # Aplicar rate limiting
        if rate_limiter:
            await rate_limiter.acquire()
        
        # Fazer requisição com retry automático para navegação
        await page.goto(job_url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(2000)
        
        return await _extract_job_details(page)
    
    if retry_system:
        result = await retry_system.execute_with_retry(
            _scrape_with_retry,
            strategy=STRATEGIES['network_heavy'],
            operation_name=f"scrape_job_details"
        )
        
        if result.success:
            job_details = result.result
            # Salvar no cache se bem-sucedido
            if cache:
                await cache.set(job_url, job_details)
            
            # Reportar sucesso
            if rate_limiter:
                rate_limiter.report_success()
            if monitor:
                monitor.record_request_success()
            
            return job_details
        else:
            # Reportar erro
            if rate_limiter:
                rate_limiter.report_error()
            if monitor:
                monitor.record_request_failure()
            
            return {
                'descricao': 'Erro ao carregar',
                'salario': 'Erro ao carregar',
                'requisitos': 'Erro ao carregar',
                'beneficios': 'Erro ao carregar',
                'nivel_experiencia': 'Erro ao carregar',
                'modalidade': 'Erro ao carregar',
                'data_publicacao': 'Erro ao carregar'
            }
    else:
        # Método original sem retry
        try:
            return await _scrape_with_retry()
        except Exception as e:
            print(f"Erro ao extrair detalhes da vaga: {e}")
            
            # Reportar erro
            if rate_limiter:
                rate_limiter.report_error()
            if monitor:
                monitor.record_request_failure()
            
            return {
                'descricao': 'Erro ao carregar',
                'salario': 'Erro ao carregar',
                'requisitos': 'Erro ao carregar',
                'beneficios': 'Erro ao carregar',
                'nivel_experiencia': 'Erro ao carregar',
                'modalidade': 'Erro ao carregar',
                'data_publicacao': 'Erro ao carregar'
            }


async def _extract_job_details(page):
    """
    Extrai detalhes específicos da página de vaga
    """
    job_details = {}
    
    # Descrição completa
    try:
        desc_selectors = [
            '[data-testid="job-description"]',
            '.job-description',
            '[class*="description"]',
            '.sc-gEvEer',
            'section:has-text("Descrição")',
            'div:has-text("Descrição")'
        ]
        
        for selector in desc_selectors:
            desc_elem = await page.query_selector(selector)
            if desc_elem:
                job_details['descricao'] = (await desc_elem.inner_text()).strip()
                break
    except:
        job_details['descricao'] = 'Não encontrada'
    
    # Salário/faixa salarial
    try:
        salary_selectors = [
            '[data-testid="salary"]',
            '.salary',
            '[class*="salario"]',
            '[class*="remuneracao"]',
            'span:has-text("R$")',
            'div:has-text("Salário")'
        ]
        
        for selector in salary_selectors:
            salary_elem = await page.query_selector(selector)
            if salary_elem:
                salary_text = await salary_elem.inner_text()
                if 'R$' in salary_text or 'salário' in salary_text.lower():
                    job_details['salario'] = salary_text.strip()
                    break
    except:
        pass
    
    if 'salario' not in job_details:
        job_details['salario'] = 'A combinar'
        
    # Requisitos técnicos
    try:
        req_selectors = [
            'section:has-text("Requisitos")',
            'div:has-text("Requisitos")',
            '[class*="requirements"]',
            '[class*="requisitos"]',
            'section:has-text("Qualificações")',
            'div:has-text("Qualificações")'
        ]
        
        for selector in req_selectors:
            req_elem = await page.query_selector(selector)
            if req_elem:
                job_details['requisitos'] = (await req_elem.inner_text()).strip()
                break
    except:
        job_details['requisitos'] = 'Não especificados'
    
    # Benefícios
    try:
        ben_selectors = [
            'section:has-text("Benefícios")',
            'div:has-text("Benefícios")',
            '[class*="benefits"]',
            '[class*="beneficios"]',
            'section:has-text("Oferecemos")',
            'ul li'
        ]
        
        for selector in ben_selectors:
            ben_elem = await page.query_selector(selector)
            if ben_elem:
                ben_text = await ben_elem.inner_text()
                if any(word in ben_text.lower() for word in ['benefício', 'vale', 'plano', 'convênio', 'auxílio']):
                    job_details['beneficios'] = ben_text.strip()
                    break
    except:
        job_details['beneficios'] = 'Não informados'
    
    # Nível de experiência
    try:
        exp_selectors = [
            '[class*="experience"]',
            '[class*="nivel"]',
            'span:has-text("anos")',
            'div:has-text("Experiência")',
            'section:has-text("Experiência")'
        ]
        
        for selector in exp_selectors:
            exp_elem = await page.query_selector(selector)
            if exp_elem:
                exp_text = await exp_elem.inner_text()
                if any(word in exp_text.lower() for word in ['júnior', 'pleno', 'sênior', 'anos', 'experiência']):
                    job_details['nivel_experiencia'] = exp_text.strip()
                    break
    except:
        job_details['nivel_experiencia'] = 'Não especificado'
    
    # Modalidade de trabalho
    try:
        mode_selectors = [
            '[class*="work-mode"]',
            '[class*="modalidade"]',
            'span:has-text("Home")',
            'span:has-text("Remoto")',
            'span:has-text("Presencial")',
            'div:has-text("Modalidade")'
        ]
        
        for selector in mode_selectors:
            mode_elem = await page.query_selector(selector)
            if mode_elem:
                mode_text = await mode_elem.inner_text()
                if any(word in mode_text.lower() for word in ['home', 'remoto', 'presencial', 'híbrido']):
                    job_details['modalidade'] = mode_text.strip()
                    break
    except:
        job_details['modalidade'] = 'Home Office'
    
    # Data de publicação
    try:
        date_selectors = [
            '[class*="date"]',
            '[class*="publicada"]',
            'time',
            'span:has-text("dia")',
            'span:has-text("publicada")',
            'div:has-text("Publicada")'
        ]
        
        for selector in date_selectors:
            date_elem = await page.query_selector(selector)
            if date_elem:
                date_text = await date_elem.inner_text()
                if any(word in date_text.lower() for word in ['dia', 'publicada', 'há', 'ontem', 'hoje']):
                    job_details['data_publicacao'] = date_text.strip()
                    break
    except:
        job_details['data_publicacao'] = 'Não informada'
    
    return job_details


async def scrape_catho_jobs(max_concurrent_jobs: int = 3, max_pages: int = 5):
    """
    Faz o scraping das vagas home office no site da Catho com navegação por múltiplas páginas e retry automático
    """
    base_url = "https://www.catho.com.br/vagas/home-office/"
    
    # Inicializar sistemas de performance e robustez
    cache = IntelligentCache(max_age_hours=6)
    rate_limiter = RateLimiter(requests_per_second=1.5, burst_limit=3, adaptive=True)
    monitor = PerformanceMonitor()
    navigator = PageNavigator(max_pages=max_pages)
    retry_system = RetrySystem(default_strategy=STRATEGIES['standard'])
    monitor.start_monitoring()
    
    print("🛡️ Sistema de retry ativado para maior robustez")
    
    try:
        async with async_playwright() as p:
            # Iniciando o navegador
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
            
            # Criando páginas
            page = await browser.new_page()
            
            # Pool de páginas para processamento paralelo
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
                page_jobs = await extract_jobs_from_current_page(page, seen_urls, retry_system)
                all_jobs.extend(page_jobs)
                print(f"✅ Página {current_page}: {len(page_jobs)} vagas coletadas")
                
                # Navegar pelas páginas restantes
                if pagination_type != "single_page" and max_pages > 1:
                    if pagination_type == "traditional":
                        # Detectar número total de páginas
                        page_numbers = await navigator.get_page_numbers(page)
                        
                        if page_numbers:
                            max_available = min(max(page_numbers), max_pages)
                            print(f"📊 Páginas disponíveis detectadas: {page_numbers[:10]}... (processando até {max_available})")
                            pages_to_try = list(range(2, max_available + 1))
                        else:
                            print("⚠ Números de páginas não detectados, tentando navegação forçada...")
                            pages_to_try = list(range(2, max_pages + 1))
                        
                        for page_num in pages_to_try:
                            print(f"\n📄 === PÁGINA {page_num} ===")
                            success = await navigator.navigate_to_page(page, page_num, base_url)
                            
                            if success:
                                page_jobs = await extract_jobs_from_current_page(page, seen_urls, retry_system)
                                all_jobs.extend(page_jobs)
                                print(f"✅ Página {page_num}: {len(page_jobs)} vagas coletadas")
                                
                                if len(page_jobs) == 0:
                                    print("⚠ Página sem vagas, parando navegação")
                                    break
                            else:
                                print(f"❌ Falha ao carregar página {page_num}")
                                continue
                            
                            # Pequena pausa entre páginas
                            await asyncio.sleep(1)
                    
                    elif pagination_type == "next_button":
                        # Usar botão "próxima página"
                        for page_num in range(2, max_pages + 1):
                            print(f"\n📄 === PÁGINA {page_num} ===")
                            success = await navigator.try_next_page_button(page)
                            
                            if success:
                                page_jobs = await extract_jobs_from_current_page(page, seen_urls, retry_system)
                                all_jobs.extend(page_jobs)
                                print(f"✅ Página {page_num}: {len(page_jobs)} vagas coletadas")
                                
                                if len(page_jobs) == 0:
                                    print("⚠ Página sem vagas, parando navegação")
                                    break
                            else:
                                print(f"❌ Não foi possível navegar para página {page_num}")
                                break
                            
                            await asyncio.sleep(1)
                    
                    elif pagination_type == "infinite_scroll":
                        # Usar scroll infinito
                        attempts = 0
                        while attempts < max_pages - 1:
                            print(f"\n🔄 === CARREGAMENTO {attempts + 2} ===")
                            
                            success = await navigator.try_infinite_scroll(page)
                            if success:
                                page_jobs = await extract_jobs_from_current_page(page, seen_urls, retry_system)
                                new_jobs = [job for job in page_jobs if job not in all_jobs]
                                all_jobs.extend(new_jobs)
                                
                                print(f"✅ Carregamento {attempts + 2}: {len(new_jobs)} novas vagas")
                                
                                if len(new_jobs) == 0:
                                    print("⚠ Nenhuma vaga nova carregada, parando")
                                    break
                            else:
                                print("❌ Não foi possível carregar mais conteúdo")
                                break
                            
                            attempts += 1
                            await asyncio.sleep(2)
                
                print(f"\n🎯 COLETA CONCLUÍDA: {len(all_jobs)} vagas de {current_page if pagination_type == 'single_page' else max_pages} páginas")
                
                # Extrair informações básicas de todas as vagas
                jobs = await extract_basic_info_from_jobs(page, all_jobs)
                
                # Terceira passada: extrair informações detalhadas em paralelo
                print(f"\n🔄 Processamento paralelo de {len(jobs)} vagas (máx {max_concurrent_jobs} simultâneas)...")
                
                semaphore = asyncio.Semaphore(max_concurrent_jobs)
                
                async def process_job_with_semaphore(job, page_index):
                    async with semaphore:
                        page_to_use = detail_pages[page_index % len(detail_pages)]
                        
                        try:
                            # Extrair informações detalhadas
                            details = await scrape_job_details(
                                page_to_use, job['link'], 
                                cache, rate_limiter, monitor, retry_system
                            )
                            
                            # Adicionar informações detalhadas ao job
                            job.update(details)
                            monitor.record_job_processed()
                            
                            print(f"  ✅ [{job.get('titulo', 'Sem título')[:30]}...] Processado com sucesso")
                            return job
                            
                        except Exception as e:
                            print(f"  ❌ Erro ao processar vaga: {e}")
                            monitor.record_request_failure()
                            
                            # Adicionar valores padrão em caso de erro
                            job.update({
                                'descricao': 'Erro ao carregar',
                                'salario': 'A combinar',
                                'requisitos': 'Não especificados',
                                'beneficios': 'Não informados',
                                'nivel_experiencia': 'Não especificado',
                                'modalidade': 'Home Office',
                                'data_publicacao': 'Não informada'
                            })
                            return job
                
                # Processar jobs em lotes paralelos
                tasks = []
                for i, job in enumerate(jobs):
                    task = process_job_with_semaphore(job, i)
                    tasks.append(task)
                
                # Executar todas as tasks em paralelo
                print(f"⚡ Iniciando processamento paralelo...")
                start_parallel = time.time()
                
                processed_jobs = await asyncio.gather(*tasks, return_exceptions=True)
                
                end_parallel = time.time()
                parallel_time = end_parallel - start_parallel
                
                print(f"✨ Processamento paralelo concluído em {parallel_time:.2f}s")
                print(f"⚡ Velocidade: {len(jobs)/parallel_time:.2f} vagas/segundo")
                
                # Filtrar jobs válidos (não exceções)
                valid_jobs = [job for job in processed_jobs if not isinstance(job, Exception)]
                
                # Mostrar estatísticas de performance e retry
                monitor.print_stats()
                retry_system.print_metrics()
                
                jobs = valid_jobs
                
                # Fechar todas as páginas
                for detail_page in detail_pages:
                    await detail_page.close()
                
                print("\n📊 Processamento concluído!")
                print("Pressione Enter para fechar o navegador...")
                input()
                await browser.close()
                
                return jobs
                
            except Exception as e:
                print(f"Erro durante o scraping: {e}")
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