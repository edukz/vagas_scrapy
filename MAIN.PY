import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime, timedelta
import re
import hashlib
import os
import time
from typing import List, Dict, Optional

class CacheEntry:
    """
    Entrada do cache com metadados
    """
    def __init__(self, data: Dict, timestamp: datetime, url: str, hash_key: str):
        self.data = data
        self.timestamp = timestamp
        self.url = url
        self.hash_key = hash_key
    
    def is_expired(self, max_age_hours: int = 6) -> bool:
        """Verifica se o cache expirou"""
        return datetime.now() - self.timestamp > timedelta(hours=max_age_hours)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário serializável"""
        return {
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'url': self.url,
            'hash_key': self.hash_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """Cria instância a partir de dicionário"""
        return cls(
            data=data['data'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            url=data['url'],
            hash_key=data['hash_key']
        )

class IntelligentCache:
    """
    Sistema de cache inteligente para URLs e dados de vagas
    """
    def __init__(self, cache_dir: str = "cache", max_age_hours: int = 6):
        self.cache_dir = cache_dir
        self.max_age_hours = max_age_hours
        self.memory_cache = {}
        
        # Criar diretório de cache
        os.makedirs(cache_dir, exist_ok=True)
        
        # Limpar cache expirado na inicialização (síncronamente)
        self._cleanup_expired_cache_sync()
    
    def _get_cache_key(self, url: str) -> str:
        """Gera chave única para URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Gera caminho do arquivo de cache"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    async def get(self, url: str) -> Optional[Dict]:
        """
        Recupera dados do cache se válidos
        """
        cache_key = self._get_cache_key(url)
        
        # Verificar cache em memória primeiro
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if not entry.is_expired(self.max_age_hours):
                print(f"✓ Cache hit (memória): {url[:50]}...")
                return entry.data
            else:
                del self.memory_cache[cache_key]
        
        # Verificar cache em disco
        cache_file = self._get_cache_file_path(cache_key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                entry = CacheEntry.from_dict(cache_data)
                
                if not entry.is_expired(self.max_age_hours):
                    # Carregar de volta para memória
                    self.memory_cache[cache_key] = entry
                    print(f"✓ Cache hit (disco): {url[:50]}...")
                    return entry.data
                else:
                    # Cache expirado, remover arquivo
                    os.remove(cache_file)
            except Exception as e:
                print(f"⚠ Erro ao ler cache: {e}")
        
        return None
    
    async def set(self, url: str, data: Dict) -> None:
        """
        Armazena dados no cache
        """
        cache_key = self._get_cache_key(url)
        entry = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            url=url,
            hash_key=cache_key
        )
        
        # Armazenar em memória
        self.memory_cache[cache_key] = entry
        
        # Armazenar em disco
        cache_file = self._get_cache_file_path(cache_key)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"✓ Cache salvo: {url[:50]}...")
        except Exception as e:
            print(f"⚠ Erro ao salvar cache: {e}")
    
    async def _cleanup_expired_cache(self) -> None:
        """
        Remove entradas de cache expiradas
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        entry = CacheEntry.from_dict(cache_data)
                        if entry.is_expired(self.max_age_hours):
                            os.remove(cache_file)
                            print(f"🗑️ Cache expirado removido: {filename}")
                    except:
                        # Se houver erro ao ler, remover arquivo corrompido
                        os.remove(cache_file)
        except Exception as e:
            print(f"⚠ Erro na limpeza do cache: {e}")
    
    def _cleanup_expired_cache_sync(self) -> None:
        """
        Remove entradas de cache expiradas (versão síncrona)
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        entry = CacheEntry.from_dict(cache_data)
                        if entry.is_expired(self.max_age_hours):
                            os.remove(cache_file)
                    except:
                        # Se houver erro ao ler, remover arquivo corrompido
                        os.remove(cache_file)
        except Exception as e:
            pass  # Silencioso na inicialização

class RateLimiter:
    """
    Sistema de rate limiting automático e adaptativo
    """
    def __init__(self, 
                 requests_per_second: float = 2.0,
                 burst_limit: int = 5,
                 adaptive: bool = True):
        self.requests_per_second = requests_per_second
        self.burst_limit = burst_limit
        self.adaptive = adaptive
        
        self.request_times = []
        self.consecutive_errors = 0
        self.base_delay = 1.0 / requests_per_second
        self.current_delay = self.base_delay
        
    async def acquire(self) -> None:
        """
        Aguarda permissão para fazer uma requisição
        """
        now = time.time()
        
        # Remove requisições antigas (últimos 60 segundos)
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Verifica se excedeu o burst limit
        recent_requests = len([t for t in self.request_times if now - t < 1.0])
        
        if recent_requests >= self.burst_limit:
            wait_time = self.current_delay * (recent_requests - self.burst_limit + 1)
            print(f"⏳ Rate limiting: aguardando {wait_time:.2f}s...")
            await asyncio.sleep(wait_time)
        
        # Aplica delay adaptativo
        if self.adaptive and self.current_delay > self.base_delay:
            await asyncio.sleep(self.current_delay - self.base_delay)
        
        self.request_times.append(time.time())
    
    def report_success(self) -> None:
        """
        Reporta sucesso - reduz delay adaptativo
        """
        if self.adaptive and self.consecutive_errors > 0:
            self.consecutive_errors = max(0, self.consecutive_errors - 1)
            self.current_delay = max(
                self.base_delay,
                self.current_delay * 0.9  # Reduz delay gradualmente
            )
    
    def report_error(self) -> None:
        """
        Reporta erro - aumenta delay adaptativo
        """
        if self.adaptive:
            self.consecutive_errors += 1
            self.current_delay = min(
                10.0,  # Máximo de 10 segundos
                self.current_delay * (1.5 + self.consecutive_errors * 0.1)
            )
            print(f"⚠ Erro detectado. Ajustando delay para {self.current_delay:.2f}s")

class PerformanceMonitor:
    """
    Monitor de performance para otimização automática
    """
    def __init__(self):
        self.start_time = None
        self.processed_jobs = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def start_monitoring(self):
        """Inicia monitoramento"""
        self.start_time = time.time()
        print("📊 Monitoramento de performance iniciado")
    
    def record_job_processed(self):
        """Registra vaga processada"""
        self.processed_jobs += 1
    
    def record_request_success(self):
        """Registra requisição bem-sucedida"""
        self.successful_requests += 1
    
    def record_request_failure(self):
        """Registra falha de requisição"""
        self.failed_requests += 1
    
    def record_cache_hit(self):
        """Registra acerto de cache"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Registra perda de cache"""
        self.cache_misses += 1
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de performance"""
        if not self.start_time:
            return {}
        
        elapsed_time = time.time() - self.start_time
        total_requests = self.successful_requests + self.failed_requests
        
        return {
            'tempo_execucao': f"{elapsed_time:.2f}s",
            'vagas_processadas': self.processed_jobs,
            'vagas_por_segundo': f"{self.processed_jobs / elapsed_time:.2f}" if elapsed_time > 0 else "0",
            'requisicoes_totais': total_requests,
            'taxa_sucesso': f"{(self.successful_requests / total_requests * 100):.1f}%" if total_requests > 0 else "0%",
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'taxa_cache': f"{(self.cache_hits / (self.cache_hits + self.cache_misses) * 100):.1f}%" if (self.cache_hits + self.cache_misses) > 0 else "0%"
        }
    
    def print_stats(self):
        """Imprime estatísticas formatadas"""
        stats = self.get_stats()
        if stats:
            print(f"\n📊 ESTATÍSTICAS DE PERFORMANCE:")
            print(f"   ⏱️  Tempo de execução: {stats['tempo_execucao']}")
            print(f"   📋 Vagas processadas: {stats['vagas_processadas']}")
            print(f"   ⚡ Vagas/segundo: {stats['vagas_por_segundo']}")
            print(f"   🌐 Requisições totais: {stats['requisicoes_totais']}")
            print(f"   ✅ Taxa de sucesso: {stats['taxa_sucesso']}")
            print(f"   💾 Cache hits: {stats['cache_hits']}")
            print(f"   ❌ Cache misses: {stats['cache_misses']}")
            print(f"   📈 Eficiência do cache: {stats['taxa_cache']}")

class JobFilter:
    """
    Sistema de filtragem avançada para vagas
    """
    def __init__(self):
        # Tecnologias comuns
        self.tecnologias_comuns = [
            'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node',
            'django', 'flask', 'fastapi', 'sql', 'mysql', 'postgresql', 'mongodb',
            'aws', 'azure', 'docker', 'kubernetes', 'git', 'html', 'css',
            'typescript', 'php', 'c#', 'c++', 'golang', 'rust', 'scala',
            'spring', 'hibernate', 'redis', 'elasticsearch', 'jenkins', 'ci/cd'
        ]
        
        # Níveis de experiência
        self.niveis_experiencia = [
            'júnior', 'junior', 'pleno', 'sênior', 'senior', 'especialista',
            'trainee', 'estagiário', 'coordenador', 'líder', 'gerente'
        ]
        
        # Tipos de empresa
        self.tipos_empresa = [
            'startup', 'multinacional', 'consultoria', 'banco', 'fintech',
            'e-commerce', 'saúde', 'educação', 'governo', 'ong', 'agência'
        ]

    def extract_technologies(self, job):
        """
        Extrai tecnologias mencionadas na vaga
        """
        technologies = set()
        
        # Textos para analisar
        texts_to_analyze = [
            job.get('titulo', '').lower(),
            job.get('descricao', '').lower(),
            job.get('requisitos', '').lower()
        ]
        
        full_text = ' '.join(texts_to_analyze)
        
        for tech in self.tecnologias_comuns:
            if tech.lower() in full_text:
                technologies.add(tech.lower())
        
        return list(technologies)

    def extract_salary_range(self, job):
        """
        Extrai e padroniza informações de salário
        """
        salary_text = job.get('salario', '').lower()
        
        if not salary_text or salary_text in ['a combinar', 'não informado']:
            return None
        
        # Procurar por valores numéricos
        import re
        numbers = re.findall(r'(\d+\.?\d*)', salary_text.replace('.', '').replace(',', '.'))
        
        if numbers:
            try:
                # Assumir que valores acima de 1000 são salários mensais
                values = [float(n) for n in numbers if float(n) > 1000]
                if values:
                    return {
                        'min': min(values),
                        'max': max(values) if len(values) > 1 else min(values),
                        'original': job.get('salario', '')
                    }
            except:
                pass
        
        return {'original': job.get('salario', '')}

    def categorize_experience_level(self, job):
        """
        Categoriza o nível de experiência
        """
        texts_to_analyze = [
            job.get('titulo', '').lower(),
            job.get('nivel_experiencia', '').lower(),
            job.get('requisitos', '').lower()
        ]
        
        full_text = ' '.join(texts_to_analyze)
        
        if any(nivel in full_text for nivel in ['trainee', 'estagiário', 'estágio']):
            return 'trainee'
        elif any(nivel in full_text for nivel in ['júnior', 'junior']):
            return 'junior'
        elif any(nivel in full_text for nivel in ['pleno']):
            return 'pleno'
        elif any(nivel in full_text for nivel in ['sênior', 'senior', 'sr']):
            return 'senior'
        elif any(nivel in full_text for nivel in ['especialista', 'expert']):
            return 'especialista'
        elif any(nivel in full_text for nivel in ['coordenador', 'líder', 'lead']):
            return 'lideranca'
        elif any(nivel in full_text for nivel in ['gerente', 'diretor']):
            return 'gestao'
        else:
            return 'nao_especificado'

    def categorize_company_type(self, job):
        """
        Categoriza o tipo de empresa
        """
        empresa = job.get('empresa', '').lower()
        descricao = job.get('descricao', '').lower()
        
        full_text = f"{empresa} {descricao}"
        
        if any(tipo in full_text for tipo in ['startup', 'scale-up']):
            return 'startup'
        elif any(tipo in full_text for tipo in ['banco', 'financeira', 'fintech']):
            return 'financeiro'
        elif any(tipo in full_text for tipo in ['consultoria', 'consulting']):
            return 'consultoria'
        elif any(tipo in full_text for tipo in ['saúde', 'hospital', 'medicina']):
            return 'saude'
        elif any(tipo in full_text for tipo in ['educação', 'universidade', 'ensino']):
            return 'educacao'
        elif any(tipo in full_text for tipo in ['e-commerce', 'marketplace', 'varejo']):
            return 'ecommerce'
        elif any(tipo in full_text for tipo in ['governo', 'público', 'municipal']):
            return 'governo'
        else:
            return 'nao_categorizado'

    def apply_filters(self, jobs, filters_config):
        """
        Aplica filtros às vagas baseado na configuração
        """
        filtered_jobs = []
        
        for job in jobs:
            # Enriquecer job com dados de análise
            job['tecnologias_detectadas'] = self.extract_technologies(job)
            job['faixa_salarial'] = self.extract_salary_range(job)
            job['nivel_categorizado'] = self.categorize_experience_level(job)
            job['tipo_empresa'] = self.categorize_company_type(job)
            
            # Aplicar filtros
            if self._job_matches_filters(job, filters_config):
                filtered_jobs.append(job)
        
        return filtered_jobs

    def _job_matches_filters(self, job, filters_config):
        """
        Verifica se uma vaga atende aos filtros
        """
        # Filtro por tecnologias
        if filters_config.get('tecnologias'):
            required_techs = [tech.lower() for tech in filters_config['tecnologias']]
            job_techs = job.get('tecnologias_detectadas', [])
            if not any(tech in job_techs for tech in required_techs):
                return False
        
        # Filtro por salário mínimo
        if filters_config.get('salario_minimo'):
            job_salary = job.get('faixa_salarial')
            if not job_salary or not job_salary.get('min'):
                return False
            if job_salary['min'] < filters_config['salario_minimo']:
                return False
        
        # Filtro por nível de experiência
        if filters_config.get('niveis_experiencia'):
            if job.get('nivel_categorizado') not in filters_config['niveis_experiencia']:
                return False
        
        # Filtro por tipo de empresa
        if filters_config.get('tipos_empresa'):
            if job.get('tipo_empresa') not in filters_config['tipos_empresa']:
                return False
        
        # Filtro por palavras-chave no título/descrição
        if filters_config.get('palavras_chave'):
            full_text = f"{job.get('titulo', '')} {job.get('descricao', '')}".lower()
            keywords = [kw.lower() for kw in filters_config['palavras_chave']]
            if not any(kw in full_text for kw in keywords):
                return False
        
        return True

def get_filter_configuration():
    """
    Interface para configurar filtros
    """
    print("\n=== CONFIGURAÇÃO DE FILTROS AVANÇADOS ===\n")
    
    filters = {}
    
    # Filtro por tecnologias
    print("1. FILTRO POR TECNOLOGIAS")
    print("Tecnologias disponíveis: python, javascript, react, angular, node, java, etc.")
    tech_input = input("Digite as tecnologias desejadas (separadas por vírgula, ou ENTER para pular): ").strip()
    if tech_input:
        filters['tecnologias'] = [tech.strip() for tech in tech_input.split(',')]
        print(f"✓ Filtro aplicado: {filters['tecnologias']}")
    
    # Filtro por salário
    print("\n2. FILTRO POR SALÁRIO MÍNIMO")
    salary_input = input("Digite o salário mínimo desejado (ou ENTER para pular): ").strip()
    if salary_input:
        try:
            filters['salario_minimo'] = float(salary_input)
            print(f"✓ Salário mínimo: R$ {filters['salario_minimo']}")
        except:
            print("⚠ Valor inválido, filtro ignorado")
    
    # Filtro por nível
    print("\n3. FILTRO POR NÍVEL DE EXPERIÊNCIA")
    print("Opções: trainee, junior, pleno, senior, especialista, lideranca, gestao")
    level_input = input("Digite os níveis desejados (separados por vírgula, ou ENTER para pular): ").strip()
    if level_input:
        filters['niveis_experiencia'] = [level.strip() for level in level_input.split(',')]
        print(f"✓ Níveis: {filters['niveis_experiencia']}")
    
    # Filtro por tipo de empresa
    print("\n4. FILTRO POR TIPO DE EMPRESA")
    print("Opções: startup, financeiro, consultoria, saude, educacao, ecommerce, governo")
    company_input = input("Digite os tipos desejados (separados por vírgula, ou ENTER para pular): ").strip()
    if company_input:
        filters['tipos_empresa'] = [tipo.strip() for tipo in company_input.split(',')]
        print(f"✓ Tipos de empresa: {filters['tipos_empresa']}")
    
    # Filtro por palavras-chave
    print("\n5. FILTRO POR PALAVRAS-CHAVE")
    keyword_input = input("Digite palavras-chave para buscar no título/descrição (separadas por vírgula, ou ENTER para pular): ").strip()
    if keyword_input:
        filters['palavras_chave'] = [kw.strip() for kw in keyword_input.split(',')]
        print(f"✓ Palavras-chave: {filters['palavras_chave']}")
    
    print(f"\n✓ Configuração de filtros concluída!")
    if filters:
        print("Filtros ativos:")
        for key, value in filters.items():
            print(f"  - {key}: {value}")
    else:
        print("Nenhum filtro será aplicado (todas as vagas serão retornadas)")
    
    return filters

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
                            import re
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

async def extract_jobs_from_current_page(page, seen_urls: set) -> List[Dict]:
    """
    Extrai vagas da página atual
    """
    jobs = []
    
    try:
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
        
    except Exception as e:
        print(f"❌ Erro ao extrair vagas da página: {e}")
    
    return jobs

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
                            monitor: PerformanceMonitor = None):
    """
    Extrai informações detalhadas de uma vaga específica com cache e rate limiting
    """
    try:
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
        
        # Fazer requisição
        await page.goto(job_url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(2000)
        
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
        
        # Salvar no cache se bem-sucedido
        if cache:
            await cache.set(job_url, job_details)
        
        # Reportar sucesso
        if rate_limiter:
            rate_limiter.report_success()
        if monitor:
            monitor.record_request_success()
        
        return job_details
        
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

async def scrape_catho_jobs(max_concurrent_jobs: int = 3, max_pages: int = 5):
    """
    Faz o scraping das vagas home office no site da Catho com navegação por múltiplas páginas
    """
    base_url = "https://www.catho.com.br/vagas/home-office/"
    
    # Inicializar sistemas de performance
    cache = IntelligentCache(max_age_hours=6)
    rate_limiter = RateLimiter(requests_per_second=1.5, burst_limit=3, adaptive=True)
    monitor = PerformanceMonitor()
    navigator = PageNavigator(max_pages=max_pages)
    monitor.start_monitoring()
    
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
            page_jobs = await extract_jobs_from_current_page(page, seen_urls)
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
                            page_jobs = await extract_jobs_from_current_page(page, seen_urls)
                            all_jobs.extend(page_jobs)
                            print(f"✅ Página {page_num}: {len(page_jobs)} vagas coletadas")
                            
                            if len(page_jobs) == 0:
                                print("⚠ Página sem vagas, parando navegação")
                                break
                        else:
                            print(f"❌ Falha ao carregar página {page_num}")
                            # Não quebrar imediatamente, tentar próxima página
                            continue
                        
                        # Pequena pausa entre páginas
                        await asyncio.sleep(1)
                
                elif pagination_type == "next_button":
                    # Usar botão "próxima página"
                    for page_num in range(2, max_pages + 1):
                        print(f"\n📄 === PÁGINA {page_num} ===")
                        success = await navigator.try_next_page_button(page)
                        
                        if success:
                            page_jobs = await extract_jobs_from_current_page(page, seen_urls)
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
                        initial_count = len(all_jobs)
                        
                        success = await navigator.try_infinite_scroll(page)
                        if success:
                            page_jobs = await extract_jobs_from_current_page(page, seen_urls)
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
                            cache, rate_limiter, monitor
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
            
            # Mostrar estatísticas de performance
            monitor.print_stats()
            
            return valid_jobs
            
        except Exception as e:
            print(f"Erro durante o scraping: {e}")
            
            # Salvando HTML para debug
            try:
                html = await page.content()
                with open("catho_error.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("HTML da página salvo em 'catho_error.html' para análise")
            except:
                pass
                
            return []
        
        finally:
            # Fechar todas as páginas
            for detail_page in detail_pages:
                await detail_page.close()
            
            print("\n📊 Processamento concluído!")
            print("Pressione Enter para fechar o navegador...")
            input()
            await browser.close()

class FileManager:
    """
    Gerenciador inteligente de arquivos - evita spam e organiza resultados
    """
    def __init__(self, results_dir: str = "resultados"):
        self.results_dir = results_dir
        self.max_files_per_type = 5  # Manter apenas os 5 mais recentes de cada tipo
        
        # Criar diretório se não existir
        os.makedirs(results_dir, exist_ok=True)
        
        # Subdiretórios organizados
        self.subdirs = {
            'json': os.path.join(results_dir, 'json'),
            'txt': os.path.join(results_dir, 'txt'), 
            'csv': os.path.join(results_dir, 'csv'),
            'relatorios': os.path.join(results_dir, 'relatorios')
        }
        
        for subdir in self.subdirs.values():
            os.makedirs(subdir, exist_ok=True)
    
    def cleanup_old_files(self, file_pattern: str, max_files: int = 5):
        """Remove arquivos antigos mantendo apenas os mais recentes"""
        try:
            import glob
            files = glob.glob(file_pattern)
            if len(files) > max_files:
                # Ordenar por data de modificação (mais antigos primeiro)
                files.sort(key=os.path.getmtime)
                files_to_remove = files[:-max_files]
                
                for file_path in files_to_remove:
                    os.remove(file_path)
                    print(f"🗑️ Arquivo antigo removido: {os.path.basename(file_path)}")
        except Exception as e:
            pass  # Silencioso para não poluir logs
    
    def get_latest_filename(self, base_name: str, extension: str, subdir: str) -> str:
        """Gera nome de arquivo inteligente - sobrescreve se for do mesmo dia"""
        today = datetime.now().strftime("%Y%m%d")
        
        # Verificar se já existe arquivo de hoje
        existing_pattern = os.path.join(self.subdirs[subdir], f"{base_name}_{today}*{extension}")
        
        try:
            import glob
            existing_files = glob.glob(existing_pattern)
            if existing_files:
                # Usar o arquivo existente de hoje (sobrescrever)
                return existing_files[0]
        except:
            pass
        
        # Criar novo arquivo com timestamp completo apenas se necessário
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return os.path.join(self.subdirs[subdir], f"{base_name}_{timestamp}{extension}")

def save_results(jobs, filters_applied=None, ask_user_preference=True):
    """
    Salva os resultados de forma organizada e inteligente
    """
    if not jobs:
        print("Nenhuma vaga para salvar")
        return
    
    # Perguntar preferência do usuário
    if ask_user_preference:
        print("\n💾 OPÇÕES DE SALVAMENTO:")
        print("1. Arquivo único (sobrescreve arquivo do dia)")
        print("2. Arquivo com timestamp (mantém histórico)")
        print("3. Não salvar arquivos (apenas exibir no terminal)")
        
        choice = input("Escolha uma opção (1-3, padrão: 1): ").strip() or "1"
        
        if choice == "3":
            print("✓ Resultados não salvos em arquivo")
            return
        
        use_timestamp = choice == "2"
    else:
        use_timestamp = False
    
    file_manager = FileManager()
    
    if use_timestamp:
        # Modo com timestamp (histórico completo)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = os.path.join(file_manager.subdirs['json'], f"vagas_catho_{timestamp}.json")
        txt_filename = os.path.join(file_manager.subdirs['txt'], f"vagas_catho_{timestamp}.txt")
        csv_filename = os.path.join(file_manager.subdirs['csv'], f"vagas_catho_{timestamp}.csv")
        stats_filename = os.path.join(file_manager.subdirs['relatorios'], f"analise_{timestamp}.txt")
    else:
        # Modo arquivo único (sobrescreve arquivo do dia)
        json_filename = file_manager.get_latest_filename("vagas_catho", ".json", "json")
        txt_filename = file_manager.get_latest_filename("vagas_catho", ".txt", "txt")
        csv_filename = file_manager.get_latest_filename("vagas_catho", ".csv", "csv") 
        stats_filename = file_manager.get_latest_filename("analise_completa", ".txt", "relatorios")
    
    # Salvar JSON
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Salvo: {os.path.relpath(json_filename)}")
    
    # Salvar TXT formatado de forma limpa e organizada
    with open(txt_filename, 'w', encoding='utf-8') as f:
        # Cabeçalho limpo
        f.write("VAGAS DE EMPREGO HOME OFFICE - CATHO\n")
        f.write("=" * 50 + "\n")
        f.write(f"Data da coleta: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n")
        f.write(f"Total de vagas: {len(jobs)}\n")
        
        if filters_applied:
            f.write(f"\nFiltros aplicados: {', '.join(f'{k}: {v}' for k, v in filters_applied.items())}\n")
        
        f.write("\n" + "=" * 50 + "\n\n")
        
        # Lista das vagas de forma mais limpa
        for i, job in enumerate(jobs, 1):
            # Cabeçalho da vaga mais simples
            f.write(f"{i:2d}. {job['titulo']}\n")
            f.write("-" * (len(f"{i:2d}. {job['titulo']}")) + "\n")
            
            # Informações organizadas em tabela simples
            empresa = job.get('empresa', 'Não informada')
            localizacao = job.get('localizacao', 'Não informada')
            salario = job.get('salario', 'Não informado')
            nivel = job.get('nivel_categorizado', 'Não especificado').replace('_', ' ').title()
            
            f.write(f"Empresa:     {empresa}\n")
            f.write(f"Local:       {localizacao}\n")
            f.write(f"Salário:     {salario}\n")
            f.write(f"Nível:       {nivel}\n")
            
            # Tecnologias em uma linha
            if job.get('tecnologias_detectadas'):
                techs = ', '.join(job['tecnologias_detectadas'])
                f.write(f"Tecnologias: {techs}\n")
            
            # Link
            f.write(f"Link:        {job['link']}\n")
            
            # Separador entre vagas
            f.write("\n" + "." * 50 + "\n\n")
        
        # Resumo estatístico no final
        f.write("RESUMO ESTATÍSTICO\n")
        f.write("=" * 50 + "\n\n")
        
        # Tecnologias mais usadas
        all_techs = {}
        for job in jobs:
            for tech in job.get('tecnologias_detectadas', []):
                all_techs[tech] = all_techs.get(tech, 0) + 1
        
        if all_techs:
            f.write("Tecnologias mais demandadas:\n")
            for tech, count in sorted(all_techs.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {tech}: {count} vagas\n")
            f.write("\n")
        
        # Empresas com mais vagas
        empresas = {}
        for job in jobs:
            empresa = job.get('empresa', 'Não informada')
            if empresa != 'Não informada':
                empresas[empresa] = empresas.get(empresa, 0) + 1
        
        if empresas:
            f.write("Empresas com mais vagas:\n")
            for empresa, count in sorted(empresas.items(), key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {empresa}: {count} vagas\n")
            f.write("\n")
        
        # Distribuição por nível
        niveis = {}
        for job in jobs:
            nivel = job.get('nivel_categorizado', 'Não especificado').replace('_', ' ').title()
            niveis[nivel] = niveis.get(nivel, 0) + 1
        
        f.write("Distribuição por nível:\n")
        for nivel, count in sorted(niveis.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {nivel}: {count} vagas\n")
    
    print(f"✓ Salvo: {os.path.relpath(txt_filename)}")
    
    # Salvar CSV limpo e organizado
    try:
        import csv
        
        # Preparar dados limpos para CSV
        csv_data = []
        for job in jobs:
            # Limpar e organizar dados
            clean_row = {
                'Titulo': job.get('titulo', '').strip(),
                'Empresa': job.get('empresa', 'Não informada').strip(),
                'Localizacao': job.get('localizacao', 'Não informada').strip(),
                'Salario': job.get('salario', 'Não informado').strip(),
                'Salario_Min': job.get('faixa_salarial', {}).get('min', '') if job.get('faixa_salarial') else '',
                'Salario_Max': job.get('faixa_salarial', {}).get('max', '') if job.get('faixa_salarial') else '',
                'Nivel_Experiencia': job.get('nivel_categorizado', 'Não especificado').replace('_', ' ').title(),
                'Tipo_Empresa': job.get('tipo_empresa', 'Não categorizado').replace('_', ' ').title(),
                'Modalidade': job.get('modalidade', 'Não especificada').strip(),
                'Data_Publicacao': job.get('data_publicacao', 'Não informada').strip(),
                'Tecnologias': ', '.join(job.get('tecnologias_detectadas', [])),
                'Tem_Beneficios': 'Sim' if job.get('beneficios') and job.get('beneficios') != 'Não informados' else 'Não',
                'Link': job.get('link', '').strip()
            }
            
            # Adicionar apenas campos úteis para análise
            csv_data.append(clean_row)
        
        # Salvar CSV com cabeçalhos em português
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as f:  # BOM para Excel
            if csv_data:
                fieldnames = [
                    'Titulo', 'Empresa', 'Localizacao', 'Salario', 
                    'Salario_Min', 'Salario_Max', 'Nivel_Experiencia', 
                    'Tipo_Empresa', 'Modalidade', 'Data_Publicacao', 
                    'Tecnologias', 'Tem_Beneficios', 'Link'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
        
        print(f"✓ Salvo: {os.path.relpath(csv_filename)} (otimizado para Excel)")
    except Exception as e:
        print(f"⚠ Erro ao salvar CSV: {e}")
    
    # Salvar relatório estatístico simplificado
    with open(stats_filename, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE ANÁLISE - VAGAS HOME OFFICE\n")
        f.write("=" * 45 + "\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n")
        f.write(f"Total de vagas: {len(jobs)}\n\n")
        
        if filters_applied:
            f.write("Filtros aplicados:\n")
            for key, value in filters_applied.items():
                f.write(f"  • {key}: {', '.join(value) if isinstance(value, list) else value}\n")
            f.write("\n")
        
        # Análise de tecnologias
        all_techs = {}
        for job in jobs:
            for tech in job.get('tecnologias_detectadas', []):
                all_techs[tech] = all_techs.get(tech, 0) + 1
        
        if all_techs:
            f.write("TECNOLOGIAS MAIS DEMANDADAS\n")
            f.write("-" * 30 + "\n")
            for tech, count in sorted(all_techs.items(), key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count / len(jobs)) * 100
                f.write(f"{tech:<15} {count:>3} vagas ({percentage:>4.1f}%)\n")
            f.write("\n")
        
        # Análise salarial
        salaries = []
        for job in jobs:
            if job.get('faixa_salarial') and job['faixa_salarial'].get('min'):
                salaries.append(job['faixa_salarial']['min'])
        
        if salaries:
            f.write("ANÁLISE SALARIAL\n")
            f.write("-" * 15 + "\n")
            f.write(f"Menor salário:    R$ {min(salaries):>8,.2f}\n")
            f.write(f"Maior salário:    R$ {max(salaries):>8,.2f}\n")
            f.write(f"Salário médio:    R$ {sum(salaries)/len(salaries):>8,.2f}\n")
            f.write(f"Com salário info: {len(salaries):>3} de {len(jobs)} vagas ({(len(salaries)/len(jobs)*100):>4.1f}%)\n\n")
        
        # Top empresas
        empresas = {}
        for job in jobs:
            empresa = job.get('empresa', 'Não informada')
            if empresa != 'Não informada':
                empresas[empresa] = empresas.get(empresa, 0) + 1
        
        if empresas:
            f.write("EMPRESAS COM MAIS VAGAS\n")
            f.write("-" * 23 + "\n")
            for empresa, count in sorted(empresas.items(), key=lambda x: x[1], reverse=True)[:8]:
                f.write(f"{empresa:<25} {count:>2} vagas\n")
            f.write("\n")
        
        # Distribuições
        nivel_counts = {}
        tipo_counts = {}
        
        for job in jobs:
            nivel = job.get('nivel_categorizado', 'Não especificado').replace('_', ' ').title()
            nivel_counts[nivel] = nivel_counts.get(nivel, 0) + 1
            
            tipo = job.get('tipo_empresa', 'Não categorizado').replace('_', ' ').title()
            tipo_counts[tipo] = tipo_counts.get(tipo, 0) + 1
        
        f.write("DISTRIBUIÇÃO POR NÍVEL\n")
        f.write("-" * 21 + "\n")
        for nivel, count in sorted(nivel_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(jobs)) * 100
            f.write(f"{nivel:<20} {count:>3} vagas ({percentage:>4.1f}%)\n")
        f.write("\n")
        
        f.write("TIPOS DE EMPRESA\n")
        f.write("-" * 16 + "\n")
        for tipo, count in sorted(tipo_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(jobs)) * 100
            f.write(f"{tipo:<20} {count:>3} vagas ({percentage:>4.1f}%)\n")
    
    print(f"✓ Salvo: {os.path.relpath(stats_filename)}")
    
    # Limpeza automática de arquivos antigos (se usando timestamp)
    if use_timestamp:
        file_manager.cleanup_old_files(
            os.path.join(file_manager.subdirs['json'], "vagas_catho_*.json"), 5
        )
        file_manager.cleanup_old_files(
            os.path.join(file_manager.subdirs['txt'], "vagas_catho_*.txt"), 5
        )
        file_manager.cleanup_old_files(
            os.path.join(file_manager.subdirs['csv'], "vagas_catho_*.csv"), 5
        )
        file_manager.cleanup_old_files(
            os.path.join(file_manager.subdirs['relatorios'], "analise_*.txt"), 5
        )
    
    print(f"\n📁 Arquivos organizados no diretório: {file_manager.results_dir}/")
    print(f"   📄 {len(jobs)} vagas salvas em 3 formatos + relatório de análise")

async def main():
    """
    Função principal
    """
    print("=== WEB SCRAPER CATHO (VERSÃO COMPLETA OTIMIZADA) ===\n")
    print("Esta versão inclui:")
    print("🔍 Sistema de filtragem avançada:")
    print("   • Filtros por tecnologias específicas")
    print("   • Filtro por faixa salarial")
    print("   • Filtro por nível de experiência")
    print("   • Filtro por tipo de empresa")
    print("   • Filtro por palavras-chave")
    print("\n⚡ Otimizações de performance:")
    print("   • Processamento paralelo/assíncrono")
    print("   • Cache inteligente (6h de validade)")
    print("   • Rate limiting automático e adaptativo")
    print("   • Navegação por múltiplas páginas")
    print("   • Monitoramento de performance em tempo real")
    print("\n📊 Coleta de informações completas:")
    print("   • Descrição completa")
    print("   • Salário/faixa salarial")
    print("   • Requisitos técnicos")
    print("   • Benefícios")
    print("   • Nível de experiência")
    print("   • Modalidade de trabalho")
    print("   • Data de publicação")
    print("\n📁 Gerenciamento inteligente de arquivos:")
    print("   • Organização em subdiretórios")
    print("   • Opção de arquivo único ou histórico")
    print("   • Limpeza automática de arquivos antigos")
    print("   • Múltiplos formatos (JSON, TXT, CSV)")
    print("\n📈 Análise automática:")
    print("   • Detecção de tecnologias")
    print("   • Categorização de empresas")
    print("   • Análise salarial")
    print("   • Relatórios estatísticos\n")
    
    # Configurar filtros
    print("Deseja aplicar filtros às vagas? (s/n)")
    apply_filters = input().strip().lower() in ['s', 'sim', 'y', 'yes']
    
    filters_config = {}
    if apply_filters:
        filters_config = get_filter_configuration()
    else:
        print("✓ Nenhum filtro será aplicado - todas as vagas serão coletadas")
    
    # Configurar performance
    print("\n⚡ CONFIGURAÇÃO DE PERFORMANCE:")
    print("Quantas vagas processar simultaneamente? (1-5, padrão: 3)")
    try:
        max_concurrent = int(input("Digite o número: ").strip() or "3")
        max_concurrent = max(1, min(5, max_concurrent))
    except:
        max_concurrent = 3
    
    print(f"✓ Processamento paralelo configurado: {max_concurrent} vagas simultâneas")
    
    # Configurar páginas
    print("\n📄 CONFIGURAÇÃO DE PÁGINAS:")
    print("Quantas páginas analisar? (1-10, padrão: 5)")
    try:
        max_pages = int(input("Digite o número: ").strip() or "5")
        max_pages = max(1, min(10, max_pages))
    except:
        max_pages = 5
    
    print(f"✓ Navegação configurada: até {max_pages} páginas")
    print("📝 Nota: Cache inteligente ativo (6h), Rate limiting adaptativo ativo")
    print("🔍 Detecção automática de paginação (tradicional/botões/scroll infinito)")
    
    # Executando o scraper
    print(f"\n{'='*60}")
    print("INICIANDO COLETA OTIMIZADA MULTI-PÁGINA...")
    print(f"{'='*60}")
    
    jobs = await scrape_catho_jobs(max_concurrent_jobs=max_concurrent, max_pages=max_pages)
    
    if jobs:
        print(f"\n{'='*60}")
        print(f"DADOS COLETADOS: {len(jobs)} vagas encontradas")
        print(f"{'='*60}")
        
        # Aplicar filtros e análise
        if filters_config or True:  # Sempre aplicar análise
            print("\nAplicando filtros e análise...")
            job_filter = JobFilter()
            
            if filters_config:
                filtered_jobs = job_filter.apply_filters(jobs, filters_config)
                print(f"✓ Filtros aplicados: {len(filtered_jobs)} vagas selecionadas")
            else:
                # Aplicar apenas análise sem filtros
                filtered_jobs = job_filter.apply_filters(jobs, {})
                print(f"✓ Análise aplicada a todas as {len(filtered_jobs)} vagas")
            
            jobs = filtered_jobs
        
        if jobs:
            print(f"\n{'='*60}")
            print(f"RESULTADO FINAL: {len(jobs)} vagas processadas")
            print(f"{'='*60}")
            
            # Salvando resultados
            save_results(jobs, filters_config)
            
            print(f"\n✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
            print(f"📁 Arquivos gerados:")
            print(f"   • JSON com dados completos e análise")
            print(f"   • TXT formatado para leitura")
            print(f"   • CSV para análise em planilhas")
            print(f"   • Relatório de análise completa")
            
            # Mostrar preview dos resultados
            print(f"\n🔥 PREVIEW DOS RESULTADOS:")
            if jobs:
                # Tecnologias mais demandadas
                all_techs = {}
                for job in jobs:
                    for tech in job.get('tecnologias_detectadas', []):
                        all_techs[tech] = all_techs.get(tech, 0) + 1
                
                if all_techs:
                    print(f"   💻 Top 5 tecnologias:")
                    for tech, count in sorted(all_techs.items(), key=lambda x: x[1], reverse=True)[:5]:
                        print(f"      - {tech}: {count} vagas")
                
                # Análise de níveis
                niveis = {}
                for job in jobs:
                    nivel = job.get('nivel_categorizado', 'Não categorizado')
                    niveis[nivel] = niveis.get(nivel, 0) + 1
                
                if niveis:
                    print(f"   📊 Distribuição por nível:")
                    for nivel, count in sorted(niveis.items(), key=lambda x: x[1], reverse=True)[:3]:
                        print(f"      - {nivel.title()}: {count} vagas")
        else:
            print("\n⚠ Nenhuma vaga atendeu aos critérios de filtro especificados.")
            print("Tente ajustar os filtros ou executar sem filtros.")
    else:
        print("\n✗ Nenhuma vaga foi encontrada no site.")
        print("Verifique o arquivo 'catho_debug.png' para ver o que apareceu na página")

if __name__ == "__main__":
    asyncio.run(main())