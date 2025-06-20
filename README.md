# 🚀 Catho Job Scraper - Sistema Enterprise

Sistema avançado de web scraping para análise de vagas do Catho.com.br com arquitetura moderna, dashboard de estatísticas e API REST completa.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Playwright](https://img.shields.io/badge/Playwright-1.52+-orange.svg)](https://playwright.dev)

## 📋 Índice

- [🌟 Características Principais](#-características-principais)
- [⚡ Instalação Rápida](#-instalação-rápida)
- [🎮 Como Usar](#-como-usar)
- [📊 Dashboard de Estatísticas](#-dashboard-de-estatísticas)
- [⚙️ Sistema de Configurações](#️-sistema-de-configurações)
- [🏗️ Arquitetura](#️-arquitetura)
- [📚 Documentação](#-documentação)
- [🤝 Contribuição](#-contribuição)

## 🌟 Características Principais

### 🎯 **Interface Completa**
- **Menu interativo** com 8 opções principais
- **Dashboard de estatísticas** com 8 categorias de análise
- **Sistema de configurações** com 8 seções organizadas
- **Interface visual** profissional com cores e layouts estruturados

### 📊 **Dashboard de Analytics**
- 🎯 **Visão Geral** - Métricas gerais e resumos
- 💼 **Análise de Vagas** - Qualidade dos dados e distribuição
- 💻 **Tecnologias** - Top 20 techs mais demandadas por categoria
- 🏢 **Empresas** - Ranking de contratantes e distribuição por porte
- 📍 **Localização** - Distribuição geográfica e modalidades
- 💰 **Salários** - Análise de faixas salariais (em desenvolvimento)
- ⚡ **Performance** - Métricas de cache e eficiência do sistema
- 📈 **Histórico** - Evolução temporal e tendências

### ⚙️ **Sistema de Configurações Avançadas**
- 🚀 **Scraping** - URLs, concorrência, rate limiting, compressão
- 💾 **Cache** - Diretórios, TTL, limpeza automática, índices
- ⚡ **Performance** - Timeouts, retry, pool de conexões
- 📁 **Output** - Formatos de exportação, limites, relatórios
- 📝 **Logs** - Níveis, rotação, debug e performance
- 🚨 **Alertas** - Email, webhook, canais multi-plataforma
- 🌐 **Navegador** - Headless, user-agent, argumentos customizados
- 👤 **Perfis** - Múltiplos perfis de configuração

### 🛡️ **Sistema de Robustez Enterprise**
- ✅ **Sistema de Retry** - Exponential backoff + jitter
- ✅ **Fallback de Seletores** - 84 estratégias adaptativas
- ✅ **Validação de Dados** - Auto-correção + detecção de anomalias
- ✅ **Logs Estruturados** - JSON + trace IDs + performance
- ✅ **Circuit Breaker** - Proteção contra sobrecarga
- ✅ **Métricas e Monitoramento** - Dashboard + alertas
- ✅ **Sistema de Alertas** - Multi-canal + escalação
- ✅ **Cache Inteligente** - Compressão + índices + deduplicação

### 🚀 **Modos de Performance**
1. **BÁSICO** - Scraping tradicional sequencial
2. **OTIMIZADO** - Processamento incremental + deduplicação
3. **MÁXIMA PERFORMANCE** - Pool de conexões + compressão avançada

## ⚡ Instalação Rápida

### 📦 Pré-requisitos
- Python 3.8+
- pip
- Git

### 🔧 Instalação
```bash
# Clone o repositório
git clone <repository-url>
cd web

# Instale as dependências
pip install -r requirements.txt

# Configure o Playwright
playwright install chromium

# Execute o sistema
python main.py
```

### 🐳 Docker (Opcional)
```bash
# Build da imagem
docker build -t catho-scraper .

# Execute com Docker Compose
docker-compose up -d
```

## 🎮 Como Usar

### 🖥️ Interface Principal
```bash
python main.py
```

**Menu Principal:**
- `[1]` 🚀 **NOVO SCRAPING** - Coleta de dados com 3 modos de performance
- `[2]` 🔍 **BUSCAR CACHE** - Pesquisa em dados coletados anteriormente
- `[3]` 🗑️ **LIMPAR DADOS** - Reset completo do sistema
- `[4]` 🧹 **DEDUPLICAÇÃO** - Remoção de duplicatas
- `[5]` ⚙️ **CONFIGURAÇÕES** - Sistema completo de configurações
- `[6]` 📊 **ESTATÍSTICAS** - Dashboard de analytics completo
- `[7]` 🌐 **API SERVER** - Servidor REST API
- `[8]` ❓ **AJUDA** - Documentação e suporte

### 🌐 API REST
```bash
# Inicie o servidor da API
python main.py
# Escolha opção [7] ou execute:
uvicorn api.main:app --reload

# Acesse a documentação
http://localhost:8000/docs
```

## 📊 Dashboard de Estatísticas

O sistema oferece um dashboard completo com 8 categorias de análise:

### 🎯 Visão Geral
- Total de vagas coletadas
- Top 10 tecnologias mais demandadas
- Top 10 empresas que mais contratam
- Distribuição por modalidades e níveis

### 💻 Análise de Tecnologias
- Top 20 tecnologias categorizadas
- Análise por categoria (Linguagens, Frameworks, DBs, Cloud)
- Percentuais de demanda e tendências

### 🏢 Análise de Empresas
- Ranking de empresas contratantes
- Classificação por porte (Grande, Médio, Pequeno, Micro)
- Distribuição estatística

### 📈 Análise Histórica
- Evolução temporal das coletas
- Tendências de crescimento
- Evolução de tecnologias ao longo do tempo

## ⚙️ Sistema de Configurações

### 🔧 Configurações Disponíveis
- **Scraping**: Rate limiting, concorrência, páginas
- **Cache**: TTL, limpeza automática, compressão
- **Performance**: Timeouts, retry, pool de conexões
- **Output**: Formatos (JSON, CSV, TXT), relatórios
- **Logs**: Níveis, rotação, debug/performance
- **Alertas**: Email, webhook, canais múltiplos
- **Navegador**: Modo headless, user-agent, argumentos
- **Perfis**: Sistema de múltiplos perfis

### 👤 Gerenciamento de Perfis
- Criação e alternância entre perfis
- Duplicação e renomeação
- Import/Export de configurações
- Backup automático

## 🏗️ Arquitetura

```
web/
├── src/                      # Código fonte principal
│   ├── core/                 # Scrapers e lógica central
│   ├── systems/              # Sistemas de robustez
│   └── utils/                # Utilitários e configurações
├── api/                      # API REST FastAPI
├── data/                     # Dados coletados
│   ├── resultados/           # Resultados em múltiplos formatos
│   ├── cache/                # Cache comprimido e índices
│   └── checkpoints/          # Processamento incremental
├── config/                   # Configurações e backups
├── docs/                     # Documentação organizada
│   ├── features/             # Documentação de funcionalidades
│   ├── api/                  # Documentação da API
│   └── deployment/           # Guias de deployment
├── tests/                    # Testes organizados
│   ├── core/                 # Testes do core
│   └── systems/              # Testes dos sistemas
└── logs/                     # Logs estruturados
```

## 📚 Documentação

### 📖 Documentação Disponível
- `docs/features/` - Funcionalidades do sistema
- `docs/api/` - Documentação da API REST
- `docs/deployment/` - Guias de deployment
- `docs/` - Documentação técnica detalhada

### 🔗 Links Importantes
- **API Documentation**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Monitoring**: Prometheus + Grafana (Docker)

## 🚀 Próximos Desenvolvimentos

- [ ] **Análise de Salários** - Coleta e análise sistemática
- [ ] **Interface Web** - Dashboard web complementar
- [ ] **Integração com BI** - Export para ferramentas de Business Intelligence
- [ ] **Machine Learning** - Predição de tendências de mercado
- [ ] **Notificações Push** - Alertas em tempo real
- [ ] **Multi-sites** - Suporte a outros sites de vagas

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🏆 Status do Projeto

✅ **Sistema Completo e Funcional**
- Interface visual profissional
- Dashboard de estatísticas completo
- Sistema de configurações avançadas
- Arquitetura robusta e escalável
- API REST documentada
- Testes organizados
- Deployment pronto

---

**Sistema Enterprise de Web Scraping - Versão 4.0.0**