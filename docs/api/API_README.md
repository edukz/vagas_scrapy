# 🚀 Catho Job Scraper API

API REST completa para o sistema de scraping de vagas do Catho, construída com FastAPI e incluindo autenticação JWT, sistema de tarefas em background, cache inteligente e documentação automática.

## 📑 Índice

- [Características](#características)
- [Instalação Rápida](#instalação-rápida)
- [Documentação da API](#documentação-da-api)
- [Autenticação](#autenticação)
- [Endpoints Principais](#endpoints-principais)
- [Exemplos de Uso](#exemplos-de-uso)
- [Deploy](#deploy)
- [Monitoramento](#monitoramento)

## ✨ Características

### 🔐 **Autenticação Segura**
- Sistema JWT completo
- Diferentes níveis de acesso (user/admin)
- Rate limiting por IP
- Tokens com expiração configurável

### 📊 **API Completa**
- **Scraping**: Controle total dos processos
- **Busca**: Filtros avançados nas vagas
- **Cache**: Gerenciamento inteligente
- **Métricas**: Analytics em tempo real
- **Health**: Monitoramento de saúde

### ⚡ **Performance**
- Background tasks assíncronas
- Pool de conexões otimizado
- Compressão gzip automática
- Cache com Redis (opcional)
- Rate limiting inteligente

### 📚 **Documentação Automática**
- Swagger UI interativo
- ReDoc elegante
- Schemas Pydantic com exemplos
- Validação automática de dados

### 🐳 **Deploy-Ready**
- Container Docker otimizado
- Docker Compose completo
- Nginx como reverse proxy
- Monitoramento com Prometheus/Grafana

## 🚀 Instalação Rápida

### Docker Compose (Recomendado)

```bash
# 1. Clonar repositório
git clone <repository-url>
cd catho-job-scraper

# 2. Configurar ambiente
cp .env.example .env
# Editar .env com suas configurações

# 3. Executar stack completa
docker-compose up -d

# 4. Verificar se está funcionando
curl http://localhost/api/v1/health
```

### Manual

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
export SECRET_KEY="sua-chave-secreta-aqui"
export DATABASE_URL="postgresql://user:pass@localhost:5432/catho_scraper"

# 3. Executar API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 📖 Documentação da API

Após iniciar a API, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Esquema OpenAPI**: http://localhost:8000/openapi.json

## 🔐 Autenticação

### 1. Obter Token

```bash
curl -X POST "http://localhost:8000/auth/token" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "password": "admin123"
     }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Usar Token

```bash
curl -H "Authorization: Bearer seu_token_aqui" \
     "http://localhost:8000/api/v1/data/stats"
```

### Usuários Padrão

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |
| `user` | `user123` | user |

## 🛠 Endpoints Principais

### Scraping

```http
POST /api/v1/scraping/start     # Iniciar scraping
GET  /api/v1/scraping/status/{id} # Status da tarefa
POST /api/v1/scraping/stop/{id}   # Parar tarefa
GET  /api/v1/scraping/history     # Histórico
```

### Busca de Dados

```http
POST /api/v1/data/search    # Buscar vagas com filtros
GET  /api/v1/data/stats     # Estatísticas gerais
```

### Cache

```http
GET  /api/v1/cache/stats           # Estatísticas do cache
POST /api/v1/cache/clean           # Limpar cache (admin)
POST /api/v1/cache/rebuild-index   # Reconstruir índices (admin)
```

### Sistema

```http
GET /api/v1/health    # Health check
GET /api/v1/metrics   # Métricas (admin)
```

## 💡 Exemplos de Uso

### Iniciar Scraping

```bash
curl -X POST "http://localhost:8000/api/v1/scraping/start" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "max_pages": 5,
       "max_concurrent_jobs": 3,
       "incremental": true,
       "enable_deduplication": true,
       "use_pool": true,
       "filters": {
         "technologies": ["Python", "Django"],
         "min_salary": 5000,
         "locations": ["São Paulo", "Remoto"]
       }
     }'
```

### Buscar Vagas

```bash
curl -X POST "http://localhost:8000/api/v1/data/search" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "technologies": ["Python"],
       "locations": ["São Paulo"],
       "salary_min": 4000,
       "limit": 20,
       "offset": 0
     }'
```

### Verificar Status

```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/v1/scraping/status/550e8400-e29b-41d4-a716-446655440000"
```

### Filtros Avançados

```json
{
  "technologies": ["Python", "Django", "FastAPI"],
  "companies": ["Google", "Microsoft", "Amazon"],
  "locations": ["São Paulo", "Rio de Janeiro", "Remoto"],
  "levels": ["Pleno", "Senior"],
  "salary_min": 8000,
  "salary_max": 15000,
  "date_from": "2024-01-01T00:00:00",
  "date_to": "2024-01-31T23:59:59",
  "limit": 50,
  "offset": 0,
  "sort_by": "salary",
  "sort_order": "desc"
}
```

## 🔧 Configurações

### Variáveis de Ambiente

```bash
# Essenciais
SECRET_KEY=sua-chave-secreta-256-bits
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Banco de dados (opcional)
DATABASE_URL=postgresql://user:pass@host:5432/catho_scraper

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Scraping
MAX_CONCURRENT_SCRAPERS=3
DEFAULT_MAX_PAGES=5
DEFAULT_CONCURRENT_JOBS=3

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
```

### Personalização

```python
# api/config.py - Configurações customizáveis
class Settings(BaseSettings):
    # Ajustar limites
    RATE_LIMIT_PER_MINUTE: int = 120  # Aumentar para alta demanda
    MAX_CONCURRENT_SCRAPERS: int = 5   # Mais scrapers simultâneos
    
    # Timeout personalizado
    SCRAPING_TIMEOUT_MINUTES: int = 30
    
    # Cache
    CACHE_MAX_AGE_HOURS: int = 12
```

## 🐳 Deploy

### Docker Compose (Produção)

```yaml
version: '3.8'
services:
  api:
    build: .
    environment:
      - SECRET_KEY=chave-super-secreta-producao
      - DATABASE_URL=postgresql://user:pass@db:5432/catho_scraper
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=false
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=catho_scraper
      - POSTGRES_USER=catho_user
      - POSTGRES_PASSWORD=senha_forte
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catho-scraper-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: catho-scraper-api
  template:
    metadata:
      labels:
        app: catho-scraper-api
    spec:
      containers:
      - name: api
        image: catho-scraper-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: secret-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: database-url
```

## 📊 Monitoramento

### Métricas Disponíveis

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Métricas detalhadas (admin)
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/api/v1/metrics
```

**Response de Métricas:**
```json
{
  "requests_per_minute": 45.2,
  "active_scraping_tasks": 2,
  "total_jobs_scraped": 15420,
  "average_response_time_ms": 125.5,
  "cache_hit_rate": 85.3,
  "cpu_usage_percent": 35.2,
  "memory_usage_mb": 512.8
}
```

### Grafana Dashboard

```bash
# Acessar Grafana (se usando docker-compose)
open http://localhost:3000

# Login padrão: admin / admin123
# Dashboards pré-configurados incluem:
# - API Performance
# - Scraping Statistics  
# - System Resources
# - Error Tracking
```

### Alertas

```yaml
# Exemplo de alertas Prometheus
- alert: APIDown
  expr: up{job="catho-api"} == 0
  for: 5m
  labels:
    severity: critical

- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 10m
  labels:
    severity: warning

- alert: ScrapingFailed
  expr: scraping_tasks_failed_total > scraping_tasks_completed_total * 0.1
  for: 15m
  labels:
    severity: warning
```

## 🧪 Testes

### Executar Testes

```bash
# Testes unitários
pytest tests/test_api.py -v

# Testes de integração
pytest tests/test_integration.py -v

# Coverage
pytest --cov=api tests/

# Testes de performance
pytest tests/test_performance.py -v
```

### Teste Manual

```bash
# Script de teste completo
curl -X POST http://localhost:8000/auth/token \
     -d '{"username":"admin","password":"admin123"}' \
     -H "Content-Type: application/json" | \
jq -r '.access_token' > token.txt

TOKEN=$(cat token.txt)

# Testar endpoints
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/health
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/data/stats
```

## 🛡 Segurança

### Checklist de Segurança

- [x] Autenticação JWT obrigatória
- [x] Rate limiting por IP
- [x] Validação de entrada com Pydantic
- [x] Headers de segurança (CORS, CSP, etc.)
- [x] Logs de auditoria
- [x] Usuários não-root nos containers
- [x] Secrets gerenciados externamente

### Hardening

```python
# Configurações de segurança recomendadas
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'"
}

# Rate limiting mais restritivo
RATE_LIMIT_PER_MINUTE = 30
RATE_LIMIT_BURST = 5
```

## 🆘 Troubleshooting

### Problemas Comuns

1. **401 Unauthorized**
   ```bash
   # Verificar se token está válido
   python -c "import jwt; print(jwt.decode('$TOKEN', verify=False))"
   ```

2. **429 Too Many Requests**
   ```bash
   # Aumentar rate limit ou aguardar
   curl -H "Authorization: Bearer $TOKEN" \
        "http://localhost:8000/api/v1/metrics" | jq .requests_per_minute
   ```

3. **500 Internal Server Error**
   ```bash
   # Verificar logs
   docker-compose logs api
   ```

4. **Scraping não inicia**
   ```bash
   # Verificar task manager
   curl -H "Authorization: Bearer $TOKEN" \
        "http://localhost:8000/api/v1/health" | jq .components.background_tasks
   ```

### Debug Mode

```bash
# Habilitar logs detalhados
export DEBUG=true
export LOG_LEVEL=DEBUG

# Executar com reload automático
uvicorn api.main:app --reload --log-level debug
```

## 📞 Suporte

- **Documentação**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Logs**: `docker-compose logs -f api`
- **Health**: http://localhost:8000/api/v1/health

---

## 🎯 Próximos Passos

1. **Frontend React**: Interface web para gerenciar scraping
2. **Machine Learning**: Classificação automática de vagas
3. **Webhooks**: Notificações em tempo real
4. **API versioning**: Suporte a múltiplas versões
5. **GraphQL**: Alternativa ao REST para consultas complexas

**🚀 A API está pronta para produção!**