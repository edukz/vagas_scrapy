"""
Sistema de navegação corrigido para múltiplas páginas do Catho
"""

import asyncio
import re
from typing import List, Optional
from playwright.async_api import Page


class PageNavigatorFixed:
    """
    Sistema de navegação otimizado para o site do Catho
    """
    def __init__(self, max_pages: int = 5):
        self.max_pages = max_pages
        self.current_page = 1
        self.total_pages_found = 0
        
    async def detect_pagination_type(self, page: Page) -> str:
        """
        Detecta o tipo de paginação do Catho
        """
        print("🔍 Detectando tipo de paginação do Catho...")
        
        # Seletores específicos do Catho
        catho_pagination_selectors = [
            # Paginação numérica
            'nav[aria-label*="pagination" i]',
            'nav[aria-label*="paginação" i]',
            '.pagination',
            '[class*="pagination" i]',
            'ul[class*="pagination" i]',
            # Links de página
            'a[href*="?page="]',
            'a[href*="&page="]',
            'a[href*="/p/"]',
            # Botões numerados
            'button:has-text("2")',
            'a:has-text("2")',
            # Próxima página
            'a:has-text("Próxima")',
            'button:has-text("Próxima")',
            'a[aria-label*="próxima" i]',
            '[class*="next" i]'
        ]
        
        for selector in catho_pagination_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    print(f"✅ Paginação encontrada: {selector}")
                    
                    # Verificar se é numérica ou botão próxima
                    if any(x in selector for x in ['2', '3', 'pagination']):
                        return "traditional"
                    elif any(x in selector for x in ['próxima', 'next']):
                        return "next_button"
            except:
                continue
        
        # Verificar se há indicador de múltiplas páginas no texto
        try:
            page_text = await page.content()
            if re.search(r'página \d+ de \d+', page_text, re.IGNORECASE):
                print("✅ Indicador de páginas encontrado no texto")
                return "traditional"
        except:
            pass
            
        print("⚠️ Nenhuma paginação detectada")
        return "single_page"
    
    async def get_page_numbers(self, page: Page) -> List[int]:
        """
        Extrai números de páginas disponíveis (compatibilidade com versão antiga)
        """
        total = await self.get_total_pages(page)
        if total > 1:
            return list(range(1, total + 1))
        return [1]
    
    async def get_total_pages(self, page: Page) -> int:
        """
        Obtém o número total de páginas disponíveis
        """
        print("🔍 Buscando total de páginas...")
        
        # Tentar encontrar indicador de total
        total_indicators = [
            # Texto tipo "Página 1 de 10"
            r'página \d+ de (\d+)',
            r'page \d+ of (\d+)',
            # Links numerados
            'a[href*="page="]:last-child',
            '.pagination li:last-child a',
            # Último número visível
            '.pagination a:has-text(/^\\d+$/):last-child'
        ]
        
        # Buscar no texto da página
        try:
            content = await page.content()
            match = re.search(r'página \d+ de (\d+)', content, re.IGNORECASE)
            if match:
                total = int(match.group(1))
                print(f"✅ Total de páginas encontrado no texto: {total}")
                return min(total, self.max_pages)
        except:
            pass
        
        # Buscar nos links de paginação
        try:
            # Pegar todos os links com números
            page_links = await page.query_selector_all('a[href*="page="], .pagination a')
            max_page = 1
            
            for link in page_links:
                try:
                    text = await link.inner_text()
                    if text.strip().isdigit():
                        max_page = max(max_page, int(text.strip()))
                    
                    href = await link.get_attribute('href')
                    if href:
                        matches = re.findall(r'[?&]page=(\d+)', href)
                        for match in matches:
                            max_page = max(max_page, int(match))
                except:
                    continue
            
            if max_page > 1:
                print(f"✅ Máximo de páginas detectado nos links: {max_page}")
                return min(max_page, self.max_pages)
                
        except Exception as e:
            print(f"❌ Erro ao buscar links: {e}")
        
        # Se não encontrou, usar o max_pages configurado
        print(f"⚠️ Total não detectado, usando configuração: {self.max_pages} páginas")
        return self.max_pages
    
    async def navigate_to_page(self, page: Page, page_number: int, base_url: str) -> bool:
        """
        Navega para uma página específica no Catho
        """
        print(f"\n🔄 Navegando para página {page_number}...")
        
        # Limpar parâmetros da URL base
        clean_base = base_url.split('?')[0].rstrip('/')
        
        # Padrões de URL do Catho
        url_patterns = [
            # Padrão mais comum
            f"{clean_base}?page={page_number}",
            f"{clean_base}/?page={page_number}",
            # Com outros parâmetros
            f"{base_url}&page={page_number}" if '?' in base_url else f"{base_url}?page={page_number}",
            # Padrão alternativo
            f"{clean_base}/pagina/{page_number}",
            f"{clean_base}/p/{page_number}",
        ]
        
        # Tentar navegação direta via URL
        for url in url_patterns:
            try:
                print(f"   🌐 Tentando URL: {url}")
                
                # Navegar
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                if response and response.status == 200:
                    # Aguardar carregamento
                    await page.wait_for_timeout(2000)
                    
                    # Verificar se há vagas
                    await page.wait_for_selector('h2 a[href*="/vagas/"]', timeout=5000)
                    jobs = await page.query_selector_all('h2 a[href*="/vagas/"]')
                    
                    if len(jobs) > 0:
                        print(f"   ✅ Página {page_number} carregada! {len(jobs)} vagas encontradas")
                        
                        # Verificar se realmente mudou de página
                        first_job_title = await jobs[0].inner_text()
                        print(f"   📋 Primeira vaga: {first_job_title[:50]}...")
                        
                        return True
                        
            except Exception as e:
                print(f"   ❌ Falha: {str(e)[:100]}")
                continue
        
        # Se URL direta falhou, tentar clique
        print("   🖱️ Tentando navegação por clique...")
        
        try:
            # Voltar para primeira página se necessário
            if page.url != base_url:
                await page.goto(base_url, wait_until='domcontentloaded')
                await page.wait_for_timeout(2000)
            
            # Seletores para clicar
            click_selectors = [
                f'a:has-text("{page_number}"):visible',
                f'button:has-text("{page_number}"):visible',
                f'a[href*="page={page_number}"]:visible',
                f'.pagination a:has-text("{page_number}")',
                f'[data-page="{page_number}"]'
            ]
            
            for selector in click_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        print(f"   🎯 Clicando em: {selector}")
                        await element.click()
                        await page.wait_for_load_state('networkidle')
                        await page.wait_for_timeout(2000)
                        
                        # Verificar sucesso
                        jobs = await page.query_selector_all('h2 a[href*="/vagas/"]')
                        if len(jobs) > 0:
                            print(f"   ✅ Navegação por clique bem-sucedida!")
                            return True
                            
                except:
                    continue
                    
        except Exception as e:
            print(f"   ❌ Erro no clique: {e}")
        
        # Se tudo falhou, tentar botão "Próxima"
        if page_number == self.current_page + 1:
            print("   ➡️ Tentando botão 'Próxima página'...")
            success = await self.click_next_page(page)
            if success:
                self.current_page = page_number
                return True
        
        print(f"   ❌ Falha ao navegar para página {page_number}")
        return False
    
    async def click_next_page(self, page: Page) -> bool:
        """
        Clica no botão de próxima página
        """
        next_selectors = [
            'a:has-text("Próxima"):visible',
            'a:has-text("Próximo"):visible',  
            'a:has-text(">"):visible',
            'button:has-text("Próxima"):visible',
            'a[aria-label*="próxima" i]:visible',
            'a[rel="next"]:visible',
            '.pagination .next:visible',
            '[class*="next"]:not([class*="disabled"]):visible'
        ]
        
        for selector in next_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    is_disabled = await element.get_attribute('disabled')
                    classes = await element.get_attribute('class') or ''
                    
                    if not is_disabled and 'disabled' not in classes:
                        print(f"   🖱️ Clicando em próxima página: {selector}")
                        await element.click()
                        await page.wait_for_load_state('networkidle')
                        await page.wait_for_timeout(2000)
                        return True
                        
            except:
                continue
                
        return False
    
    async def wait_for_page_change(self, page: Page, old_content: str, timeout: int = 10000) -> bool:
        """
        Aguarda mudança no conteúdo da página
        """
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
            try:
                # Pegar primeira vaga atual
                first_job = await page.query_selector('h2 a[href*="/vagas/"]:first-child')
                if first_job:
                    new_content = await first_job.inner_text()
                    if new_content != old_content:
                        return True
                        
            except:
                pass
                
            await page.wait_for_timeout(500)
            
        return False