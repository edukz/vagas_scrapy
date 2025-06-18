"""
Configurações do sistema de scraping Catho

Este arquivo contém todas as configurações padrão do sistema.
"""

# URLs
BASE_URL = "https://www.catho.com.br/vagas/home-office/"

# Cache
CACHE_MAX_AGE_HOURS = 6
CACHE_DIR = "data/cache"

# Performance
DEFAULT_MAX_CONCURRENT_JOBS = 3
DEFAULT_MAX_PAGES = 5
REQUESTS_PER_SECOND = 1.5
BURST_LIMIT = 3

# Arquivos
RESULTS_DIR = "data/resultados"
MAX_FILES_PER_TYPE = 5

# Navegador
BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor',
    '--no-sandbox'
]

# Timeouts (em milissegundos)
PAGE_LOAD_TIMEOUT = 60000
NETWORK_IDLE_TIMEOUT = 30000
ELEMENT_WAIT_TIMEOUT = 3000

# Tecnologias para detecção automática
TECNOLOGIAS_COMUNS = [
    'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node',
    'django', 'flask', 'fastapi', 'sql', 'mysql', 'postgresql', 'mongodb',
    'aws', 'azure', 'docker', 'kubernetes', 'git', 'html', 'css',
    'typescript', 'php', 'c#', 'c++', 'golang', 'rust', 'scala',
    'spring', 'hibernate', 'redis', 'elasticsearch', 'jenkins', 'ci/cd'
]

# Níveis de experiência
NIVEIS_EXPERIENCIA = [
    'júnior', 'junior', 'pleno', 'sênior', 'senior', 'especialista',
    'trainee', 'estagiário', 'coordenador', 'líder', 'gerente'
]

# Tipos de empresa
TIPOS_EMPRESA = [
    'startup', 'multinacional', 'consultoria', 'banco', 'fintech',
    'e-commerce', 'saúde', 'educação', 'governo', 'ong', 'agência'
]