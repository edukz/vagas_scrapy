# 🚀 Guia de Deploy - Catho Job Scraper API

Este guia descreve como fazer o deploy da API REST do Catho Job Scraper em diferentes ambientes.

## 📋 Índice

- [Pré-requisitos](#pré-requisitos)
- [Deploy com Docker Compose](#deploy-com-docker-compose)
- [Deploy Manual](#deploy-manual)
- [Deploy em Cloud](#deploy-em-cloud)
- [Configurações](#configurações)
- [Monitoramento](#monitoramento)
- [Troubleshooting](#troubleshooting)

## 🔧 Pré-requisitos

### Requisitos Mínimos do Sistema
- **CPU**: 2 cores (4 cores recomendado)
- **RAM**: 4GB (8GB recomendado)
- **Armazenamento**: 20GB livres
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+, etc.)

### Software Necessário
```bash
# Docker e Docker Compose
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
# Fazer logout/login para aplicar
```

## 🐳 Deploy com Docker Compose

### 1. Preparação

```bash
# Clonar repositório
git clone <repository-url>
cd catho-job-scraper

# Criar arquivo de variáveis de ambiente
cp .env.example .env
nano .env  # Editar configurações
```

### 2. Configurar Variáveis de Ambiente

Edite o arquivo `.env`:

```bash
# Segurança
SECRET_KEY=your-super-secret-key-change-this-in-production-256-bits
TOKEN_EXPIRE_MINUTES=30

# Banco de dados
DATABASE_URL=postgresql://catho_user:strong_password@db:5432/catho_scraper

# Redis
REDIS_URL=redis://redis:6379/0

# Email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoramento
GRAFANA_PASSWORD=secure_admin_password
```

### 3. Deploy Completo

```bash
# Executar stack completa
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f api
```

### 4. Verificar Deploy

```bash
# Health check
curl http://localhost/api/v1/health

# Documentação
open http://localhost/docs

# Grafana (monitoramento)
open http://localhost:3000
# Login: admin / password_do_env
```

## 🛠 Deploy Manual

### 1. Preparar Ambiente

```bash
# Instalar Python 3.11+
sudo apt install python3.11 python3.11-venv python3.11-dev

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Banco de Dados

```bash
# PostgreSQL
sudo apt install postgresql postgresql-contrib
sudo -u postgres createuser catho_user
sudo -u postgres createdb catho_scraper -O catho_user
sudo -u postgres psql -c "ALTER USER catho_user PASSWORD 'strong_password';"

# Redis
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3. Configurar Aplicação

```bash
# Variáveis de ambiente
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql://catho_user:strong_password@localhost:5432/catho_scraper"
export REDIS_URL="redis://localhost:6379/0"

# Executar migrações (se houver)
python -m alembic upgrade head

# Executar aplicação
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 4. Configurar Serviço Systemd

```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/catho-api.service
```

Conteúdo do arquivo:

```ini
[Unit]
Description=Catho Job Scraper API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/catho-scraper
Environment=PATH=/opt/catho-scraper/venv/bin
Environment=SECRET_KEY=your-secret-key
Environment=DATABASE_URL=postgresql://catho_user:password@localhost:5432/catho_scraper
Environment=REDIS_URL=redis://localhost:6379/0
ExecStart=/opt/catho-scraper/venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar e iniciar serviço
sudo systemctl daemon-reload
sudo systemctl enable catho-api
sudo systemctl start catho-api
sudo systemctl status catho-api
```

## ☁️ Deploy em Cloud

### AWS ECS com Fargate

1. **Preparar Imagem Docker**
```bash
# Build da imagem
docker build -t catho-scraper-api .

# Tag para ECR
docker tag catho-scraper-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/catho-scraper-api:latest

# Push para ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/catho-scraper-api:latest
```

2. **Configurar Task Definition**
```json
{
  "family": "catho-scraper-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/catho-scraper-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "SECRET_KEY",
          "value": "your-secret-key"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/catho_scraper"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/catho-scraper-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run

```bash
# Build e deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/catho-scraper-api

gcloud run deploy catho-scraper-api \
  --image gcr.io/PROJECT_ID/catho-scraper-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SECRET_KEY=your-secret-key \
  --set-env-vars DATABASE_URL=postgresql://user:pass@db-ip:5432/catho_scraper
```

### DigitalOcean App Platform

```yaml
# .do/app.yaml
name: catho-scraper-api
services:
- name: api
  source_dir: /
  github:
    repo: your-username/catho-scraper
    branch: main
  run_command: python -m uvicorn api.main:app --host 0.0.0.0 --port 8080
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SECRET_KEY
    value: your-secret-key
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
  http_port: 8080
databases:
- engine: PG
  name: db
  num_nodes: 1
  size: db-s-dev-database
  version: "13"
```

## ⚙️ Configurações

### Variáveis de Ambiente Essenciais

| Variável | Descrição | Padrão | Obrigatória |
|----------|-----------|--------|-------------|
| `SECRET_KEY` | Chave secreta para JWT | - | ✅ |
| `DATABASE_URL` | URL do PostgreSQL | - | ❌ |
| `REDIS_URL` | URL do Redis | - | ❌ |
| `API_HOST` | Host da API | 0.0.0.0 | ❌ |
| `API_PORT` | Porta da API | 8000 | ❌ |
| `DEBUG` | Modo debug | false | ❌ |
| `RATE_LIMIT_PER_MINUTE` | Rate limit | 60 | ❌ |
| `MAX_CONCURRENT_SCRAPERS` | Scrapers simultâneos | 3 | ❌ |

### Configurações de Performance

```bash
# Para alta carga
export RATE_LIMIT_PER_MINUTE=120
export MAX_CONCURRENT_SCRAPERS=5
export DEFAULT_MAX_PAGES=10

# Para servidor pequeno
export RATE_LIMIT_PER_MINUTE=30
export MAX_CONCURRENT_SCRAPERS=1
export DEFAULT_MAX_PAGES=3
```

## 📊 Monitoramento

### Métricas Importantes

1. **Health Checks**
   - `GET /api/v1/health` - Status geral
   - Response time < 200ms
   - Uptime > 99.5%

2. **Performance**
   - `GET /api/v1/metrics` - Métricas detalhadas
   - CPU usage < 80%
   - Memory usage < 85%
   - Disk usage < 90%

3. **Scraping**
   - Active tasks
   - Success rate > 95%
   - Average completion time

### Alertas Recomendados

```yaml
# Prometheus alert rules
groups:
- name: catho-api
  rules:
  - alert: APIDown
    expr: up{job="catho-api"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "API está fora do ar"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Taxa de erro alta na API"

  - alert: HighResponseTime
    expr: http_request_duration_seconds{quantile="0.95"} > 1
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Tempo de resposta alto"
```

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. API não inicia
```bash
# Verificar logs
docker-compose logs api

# Problemas comuns:
# - SECRET_KEY não definida
# - Porta já em uso
# - Permissões incorretas
```

#### 2. Banco de dados não conecta
```bash
# Testar conexão
docker-compose exec db psql -U catho_user -d catho_scraper

# Verificar logs
docker-compose logs db

# Soluções:
# - Verificar credenciais
# - Verificar rede Docker
# - Verificar se DB inicializou
```

#### 3. Rate limiting muito restritivo
```bash
# Ajustar no arquivo .env
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_BURST=20

# Reiniciar serviço
docker-compose restart api
```

#### 4. Scraping muito lento
```bash
# Aumentar concorrência
MAX_CONCURRENT_SCRAPERS=5
DEFAULT_CONCURRENT_JOBS=5

# Verificar recursos
docker stats
```

### Logs Importantes

```bash
# Logs da API
docker-compose logs -f api

# Logs do banco
docker-compose logs -f db

# Logs do Nginx
docker-compose logs -f nginx

# Logs do sistema
tail -f /var/log/syslog | grep catho
```

### Backup e Restore

```bash
# Backup do banco de dados
docker-compose exec db pg_dump -U catho_user catho_scraper > backup.sql

# Restore
docker-compose exec -T db psql -U catho_user catho_scraper < backup.sql

# Backup dos dados de cache
tar -czf cache_backup.tar.gz data/cache/
```

## 🔒 Segurança

### Checklist de Segurança

- [ ] SECRET_KEY forte e única
- [ ] Senhas de banco fortes
- [ ] Firewall configurado (portas 80, 443, 22)
- [ ] SSL/TLS configurado
- [ ] Rate limiting ativo
- [ ] Logs de auditoria habilitados
- [ ] Backup automatizado
- [ ] Monitoramento ativo
- [ ] Usuários não-root nos containers

### Configuração SSL

```bash
# Obter certificado Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Configurar no nginx.conf
# ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

## 📞 Suporte

Em caso de problemas:

1. Verificar logs da aplicação
2. Consultar documentação da API em `/docs`
3. Verificar status dos serviços
4. Reportar issues no GitHub

---

**⚠️ Importante**: Sempre teste o deploy em ambiente de desenvolvimento antes de aplicar em produção!