import asyncio
import re
from typing import List


class PageNavigator:
    """
    Sistema de navegação inteligente por múltiplas páginas
    """
    def __init__(self, max_pages: int = 5):
        self.max_pages = max_pages
        self.current_page = 1
        self.total_pages_found = 0
        
    async def detect_pagination_type(self, page) -> str:
        """
        Detecta o tipo de paginação do site
        """
        # Verificar paginação tradicional
        pagination_selectors = [
            'nav[aria-label*="paginat"], nav[aria-label*="Paginat"]',
            '.pagination',
            '[class*="pagination"]',
            '[class*="pager"]',
            'nav:has(a[href*="page"])',
            'div:has(a[href*="page"])'
        ]
        
        for selector in pagination_selectors:
            pagination_elem = await page.query_selector(selector)
            if pagination_elem:
                return "traditional"
        
        # Verificar scroll infinito
        scroll_indicators = [
            '[class*="load-more"]',
            '[class*="infinite"]',
            '[class*="scroll"]',
            'button:has-text("Ver mais")',
            'button:has-text("Carregar mais")'
        ]
        
        for selector in scroll_indicators:
            scroll_elem = await page.query_selector(selector)
            if scroll_elem:
                return "infinite_scroll"
        
        # Verificar botão "próxima página"
        next_selectors = [
            'a:has-text("Próxima")',
            'a:has-text(">")',
            'a[aria-label*="próxima"]',
            'a[aria-label*="next"]',
            'button:has-text("Próxima")',
            '[class*="next"]'
        ]
        
        for selector in next_selectors:
            next_elem = await page.query_selector(selector)
            if next_elem:
                return "next_button"
        
        return "single_page"
    
    async def get_page_numbers(self, page) -> List[int]:
        """
        Extrai números de páginas disponíveis
        """
        page_numbers = []
        
        print("🔍 Debug: Procurando números de páginas...")
        
        # Tentar encontrar links numerados com mais seletores
        number_selectors = [
            'a[href*="page="]',
            'a[href*="p="]',
            '.pagination a',
            '[class*="pagination"] a',
            '[class*="pager"] a',
            'nav a',
            'a:has-text("2")',
            'a:has-text("3")',
            'a:has-text("4")',
            'a:has-text("5")',
            'button[class*="page"]',
            '[data-page]'
        ]
        
        for i, selector in enumerate(number_selectors):
            try:
                elements = await page.query_selector_all(selector)
                print(f"   Seletor {i+1} '{selector[:30]}...': {len(elements)} elementos encontrados")
                
                for element in elements:
                    try:
                        text = await element.inner_text()
                        print(f"   - Texto: '{text.strip()}'")
                        
                        if text.strip().isdigit():
                            num = int(text.strip())
                            page_numbers.append(num)
                            print(f"   ✓ Número de página encontrado: {num}")
                        
                        # Também verificar no href
                        href = await element.get_attribute('href')
                        if href:
                            print(f"   - Href: '{href}'")
                            matches = re.findall(r'(?:page=|p=)(\d+)', href)
                            for match in matches:
                                num = int(match)
                                page_numbers.append(num)
                                print(f"   ✓ Número no href: {num}")
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"   ❌ Erro no seletor: {e}")
                continue
        
        # Se não encontrou páginas numeradas, tentar uma abordagem mais simples
        if not page_numbers:
            print("🔍 Debug: Tentando encontrar próxima página...")
            next_selectors = [
                'a:has-text("Próxima")',
                'a:has-text(">")',
                'button:has-text(">")',
                'a[rel="next"]',
                '[class*="next"]'
            ]
            
            for selector in next_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"   ✓ Encontrado botão próxima página: {len(elements)} elementos")
                        # Se há botão próxima, assumir pelo menos 2 páginas e tentar até max_pages
                        return list(range(1, min(self.max_pages + 1, 6)))  # Assumir até 5 páginas
                except:
                    continue
        
        unique_pages = sorted(list(set(page_numbers)))
        print(f"🎯 Debug: Números de páginas encontrados: {unique_pages}")
        return unique_pages
    
    async def navigate_to_page(self, page, page_number: int, base_url: str) -> bool:
        """
        Navega para uma página específica
        """
        try:
            print(f"🔄 Debug: Tentando navegar para página {page_number}")
            
            # Tentar diferentes formatos de URL de paginação (mais opções)
            url_patterns = [
                f"{base_url}?page={page_number}",
                f"{base_url}?p={page_number}",
                f"{base_url}&page={page_number}",
                f"{base_url}&p={page_number}",
                f"{base_url}/page/{page_number}/",
                f"{base_url}/p{page_number}/",
                f"{base_url}#{page_number}",
                f"{base_url}?pageIndex={page_number}",
                f"{base_url}?pageNumber={page_number}",
                f"{base_url}?offset={page_number-1}",
                f"{base_url}?start={page_number-1}"
            ]
            
            for i, url in enumerate(url_patterns):
                try:
                    print(f"   🌐 Tentativa {i+1}: {url}")
                    
                    # Navegar para a URL
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    print(f"   📊 Status HTTP: {response.status if response else 'N/A'}")
                    
                    # Aguardar carregamento
                    await page.wait_for_timeout(3000)
                    
                    # Verificar se a página carregou com conteúdo
                    jobs_found = await page.query_selector_all('h2 a[href*="/vagas/"]')
                    print(f"   📋 Vagas encontradas: {len(jobs_found)}")
                    
                    # Verificar se mudou de página (URL atual)
                    current_url = page.url
                    print(f"   🔗 URL atual: {current_url}")
                    
                    if len(jobs_found) > 0:
                        # Verificar se o conteúdo realmente mudou
                        page_title = await page.title()
                        print(f"   📄 Título: {page_title}")
                        
                        # Verificar se há indicador da página atual
                        page_indicators = await page.query_selector_all(f'[class*="active"]:has-text("{page_number}"), [class*="current"]:has-text("{page_number}"), .selected:has-text("{page_number}")')
                        print(f"   🎯 Indicadores de página atual: {len(page_indicators)}")
                        
                        print(f"   ✅ Página {page_number} carregada com sucesso!")
                        return True
                    else:
                        print(f"   ⚠ Nenhuma vaga encontrada nesta URL")
                        
                except Exception as e:
                    print(f"   ❌ Erro na tentativa {i+1}: {e}")
                    continue
            
            # Se chegou aqui, tentar clique no link da página
            print(f"🔄 Debug: Tentando clicar no link da página {page_number}")
            try:
                # Voltar para página base
                await page.goto(base_url, wait_until='domcontentloaded', timeout=20000)
                await page.wait_for_timeout(2000)
                
                # Procurar link clicável para a página
                page_link_selectors = [
                    f'a:has-text("{page_number}")',
                    f'button:has-text("{page_number}")',
                    f'[data-page="{page_number}"]',
                    f'a[href*="page={page_number}"]',
                    f'a[href*="p={page_number}"]'
                ]
                
                for selector in page_link_selectors:
                    try:
                        page_link = await page.query_selector(selector)
                        if page_link:
                            print(f"   🔗 Encontrado link clicável: {selector}")
                            await page_link.click()
                            await page.wait_for_load_state('domcontentloaded')
                            await page.wait_for_timeout(3000)
                            
                            # Verificar se funcionou
                            jobs_found = await page.query_selector_all('h2 a[href*="/vagas/"]')
                            if len(jobs_found) > 0:
                                print(f"   ✅ Clique funcionou! {len(jobs_found)} vagas encontradas")
                                return True
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"   ❌ Erro ao tentar clique: {e}")
            
            print(f"   ❌ Falha ao navegar para página {page_number}")
            return False
            
        except Exception as e:
            print(f"❌ Erro geral ao navegar para página {page_number}: {e}")
            return False
    
    async def try_next_page_button(self, page) -> bool:
        """
        Tenta clicar no botão "próxima página"
        """
        next_selectors = [
            'a:has-text("Próxima")',
            'a:has-text(">")',
            'a[aria-label*="próxima"]',
            'a[aria-label*="next"]',
            'button:has-text("Próxima")',
            '[class*="next"]:not([class*="disabled"])',
            'a[rel="next"]'
        ]
        
        for selector in next_selectors:
            try:
                next_elem = await page.query_selector(selector)
                if next_elem:
                    # Verificar se o elemento está visível e clicável
                    is_visible = await next_elem.is_visible()
                    is_disabled = await next_elem.get_attribute('disabled')
                    
                    if is_visible and not is_disabled:
                        print(f"🔄 Clicando no botão próxima página...")
                        await next_elem.click()
                        await page.wait_for_load_state('networkidle')
                        await page.wait_for_timeout(2000)
                        return True
            except:
                continue
        
        return False
    
    async def try_infinite_scroll(self, page) -> bool:
        """
        Tenta carregar mais conteúdo via scroll infinito
        """
        try:
            # Fazer scroll até o final da página
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(3000)
            
            # Procurar e clicar em botões "carregar mais"
            load_more_selectors = [
                'button:has-text("Ver mais")',
                'button:has-text("Carregar mais")',
                'button:has-text("Load more")',
                '[class*="load-more"]',
                '[class*="show-more"]'
            ]
            
            for selector in load_more_selectors:
                try:
                    load_button = await page.query_selector(selector)
                    if load_button and await load_button.is_visible():
                        print(f"🔄 Carregando mais vagas...")
                        await load_button.click()
                        await page.wait_for_timeout(3000)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"❌ Erro no scroll infinito: {e}")
            return False