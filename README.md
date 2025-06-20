# 🚀 Catho Job Scraper - Sistema Enterprise

Sistema avançado de web scraping para análise de vagas do Catho.com.br com arquitetura moderna, dashboard de estatísticas, API REST completa e sistema de análise de currículos com OCR.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Playwright](https://img.shields.io/badge/Playwright-1.52+-orange.svg)](https://playwright.dev)
[![EasyOCR](https://img.shields.io/badge/EasyOCR-1.7+-red.svg)](https://github.com/JaidedAI/EasyOCR)
[![Machine Learning](https://img.shields.io/badge/ML-Ready-purple.svg)](https://scikit-learn.org)

## 📋 Índice

- [🌟 Características Principais](#-características-principais)
- [⚡ Instalação Rápida](#-instalação-rápida)
- [🎮 Como Usar](#-como-usar)
- [🤖 Sistema de Análise de CV](#-sistema-de-análise-de-cv)
- [📊 Dashboard de Estatísticas](#-dashboard-de-estatísticas)
- [⚙️ Sistema de Configurações](#️-sistema-de-configurações)
- [🏗️ Arquitetura](#️-arquitetura)
- [📚 Documentação](#-documentação)
- [🤝 Contribuição](#-contribuição)

## 🌟 Características Principais

### 🎯 **Interface Completa**
- **Menu interativo** com 9 opções principais
- **Dashboard de estatísticas** com 8 categorias de análise
- **Sistema de configurações** com 8 seções organizadas
- **Sistema de análise de CV** com OCR integrado
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

### 🤖 **Sistema de Análise de CV com OCR**
- 📄 **Múltiplos Formatos** - TXT, PDF (texto e escaneado), DOCX
- 🔍 **OCR Avançado** - EasyOCR para PDFs escaneados (imagens)
- 🧠 **Machine Learning** - Extração inteligente de informações
- 💼 **Análise Profissional** - Nome, contato, experiência, tecnologias
- 💰 **Estimativa Salarial** - Baseada em senioridade e habilidades
- 📊 **Confiança da Análise** - Score de qualidade da extração
- 💾 **Histórico de Análises** - Armazenamento e consulta de resultados
- 🎯 **Recomendações** - Sistema de matching com vagas

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

### 🔧 Instalação Básica
```bash
# Clone o repositório
git clone <repository-url>
cd web

# Instale as dependências básicas
pip install -r requirements.txt

# Configure o Playwright
playwright install chromium

# Execute o sistema
python main.py
```

### 🤖 Instalação Completa (com OCR)
```bash
# Após a instalação básica, instale dependências OCR
pip install easyocr PyMuPDF Pillow

# Para análise ML avançada (opcional)
pip install pandas scikit-learn

# Para Tesseract (alternativa ao EasyOCR)
# Ubuntu/Debian:
sudo apt install tesseract-ocr tesseract-ocr-por
pip install pytesseract

# Windows: baixe de https://github.com/UB-Mannheim/tesseract/wiki
# macOS:
brew install tesseract
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
- `[3]` 🤖 **ANÁLISE DE CV** - Sistema completo de análise de currículos com OCR
- `[4]` 🗑️ **LIMPAR DADOS** - Reset completo do sistema
- `[5]` 🧹 **DEDUPLICAÇÃO** - Remoção de duplicatas
- `[6]` ⚙️ **CONFIGURAÇÕES** - Sistema completo de configurações
- `[7]` 📊 **ESTATÍSTICAS** - Dashboard de analytics completo
- `[8]` 🌐 **API SERVER** - Servidor REST API
- `[9]` ❓ **AJUDA** - Documentação e suporte

### 🌐 API REST
```bash
# Inicie o servidor da API
python main.py
# Escolha opção [7] ou execute:
uvicorn api.main:app --reload

# Acesse a documentação
http://localhost:8000/docs
```

## 🤖 Sistema de Análise de CV

O sistema oferece análise completa de currículos com tecnologia OCR avançada para processar PDFs escaneados.

### 📄 Formatos Suportados
- **TXT** - Arquivos de texto simples
- **PDF** - PDFs com texto pesquisável
- **PDF Escaneado** - PDFs de imagem com OCR automático
- **DOCX/DOC** - Documentos Microsoft Word

### 🔍 Tecnologias OCR
- **EasyOCR** - OCR moderno com IA (recomendado)
- **Tesseract** - OCR tradicional de alta qualidade
- **PyMuPDF** - Conversão PDF para imagem otimizada
- **Detecção Automática** - Sistema detecta se PDF precisa de OCR

### 🧠 Análise Inteligente
O sistema extrai automaticamente:

#### 👤 **Informações Pessoais**
- Nome completo
- Email e telefone
- Localização geográfica
- LinkedIn e GitHub

#### 💼 **Experiência Profissional**
- Anos de experiência total
- Posição atual
- Empresas anteriores
- Nível de senioridade (júnior, pleno, sênior, líder)

#### 🛠️ **Habilidades Técnicas**
- **Linguagens**: Python, Java, JavaScript, etc.
- **Frameworks**: React, Django, Spring, etc.
- **Databases**: PostgreSQL, MongoDB, Redis, etc.
- **Cloud/DevOps**: AWS, Docker, Kubernetes, etc.
- **Data Science**: Pandas, TensorFlow, scikit-learn, etc.
- **Categorização Automática**: 10+ categorias técnicas

#### 🧭 **Análise Avançada**
- **Estimativa Salarial**: Baseada em senioridade e tecnologias
- **Confiança da Análise**: Score de qualidade (0-100%)
- **Soft Skills**: Liderança, comunicação, trabalho em equipe
- **Preferências**: Modalidade de trabalho (remoto, híbrido, presencial)

### 🎯 Sistema de Recomendações
- **Matching com Vagas**: Compatibilidade automática
- **Score de Adequação**: Percentual de compatibilidade
- **Skills em Comum**: Tecnologias que coincidem
- **Top 5 Recomendações**: Melhores oportunidades

### 💾 Histórico e Armazenamento
- **Análises Salvas**: JSON estruturado com todos os dados
- **Consulta de Histórico**: Visualização de análises anteriores
- **Estatísticas de Perfis**: Distribuição de senioridade e tecnologias
- **Exportação**: Dados em formato JSON para integração

### 🚀 Como Usar

1. **Coloque seu CV** na pasta `data/cv_input/`
2. **Execute o sistema**: `python main.py`
3. **Escolha opção [3]**: Análise de CV
4. **Selecione "Analisar Novo Currículo"**
5. **Escolha seu arquivo** da lista ou digite o caminho
6. **Aguarde a análise**: OCR + ML + Extração
7. **Visualize os resultados**: Informações detalhadas extraídas

### ⚡ Otimizações de Performance
- **Lazy Loading**: Dependências OCR carregam apenas quando necessário
- **Cache Inteligente**: Resultados salvos para consulta rápida
- **Processamento Otimizado**: OCR apenas para PDFs de imagem
- **Interface Responsiva**: Feedback visual do progresso

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
│   ├── handlers/             # Handlers para cada funcionalidade
│   ├── ml/                   # Machine Learning e análise de CV
│   │   └── models/           # Modelos de ML e analisadores
│   ├── systems/              # Sistemas de robustez
│   └── utils/                # Utilitários e configurações
├── api/                      # API REST FastAPI
├── data/                     # Dados coletados
│   ├── resultados/           # Resultados de scraping
│   ├── cache/                # Cache comprimido e índices
│   ├── cv_input/             # CVs para análise (TXT, PDF, DOCX)
│   ├── cv_analysis/          # Resultados de análise de CV
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

### ✅ **Recentemente Implementado**
- ✅ **Sistema de Análise de CV** - Completo com OCR e ML
- ✅ **OCR Avançado** - EasyOCR + Tesseract para PDFs escaneados
- ✅ **Machine Learning** - Extração inteligente de informações
- ✅ **Estimativa Salarial** - Baseada em senioridade e habilidades
- ✅ **Sistema de Recomendações** - Matching automático com vagas
- ✅ **Otimização de Performance** - Lazy loading e cache inteligente

### 🔮 **Próximas Funcionalidades**
- [ ] **API de CV** - Endpoints REST para análise de currículos
- [ ] **Análise de Salários** - Coleta e análise sistemática de faixas
- [ ] **Interface Web** - Dashboard web complementar
- [ ] **Integração com BI** - Export para ferramentas de Business Intelligence
- [ ] **ML Avançado** - Predição de tendências de mercado
- [ ] **Notificações Push** - Alertas em tempo real
- [ ] **Multi-sites** - Suporte a outros sites de vagas
- [ ] **Análise de Vídeo CV** - OCR em vídeos e apresentações
- [ ] **Matching Inteligente** - IA para recomendações personalizadas

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

✅ **Sistema Enterprise Completo e Funcional**
- ✅ Interface visual profissional com 9 opções principais
- ✅ Dashboard de estatísticas completo (8 categorias)
- ✅ Sistema de configurações avançadas (8 seções)
- ✅ **Sistema de Análise de CV com OCR** - **NOVO!**
- ✅ **Machine Learning integrado** - **NOVO!**
- ✅ **Suporte a PDFs escaneados** - **NOVO!**
- ✅ Arquitetura robusta e escalável
- ✅ API REST documentada
- ✅ Testes organizados
- ✅ Deployment pronto
- ✅ **Performance otimizada** com lazy loading

### 🎯 **Funcionalidades Principais**
- 🚀 **Web Scraping Inteligente** com 3 modos de performance
- 🤖 **Análise de CV Completa** com OCR e ML
- 📊 **Dashboard Analytics** com 8 categorias de dados
- ⚙️ **Sistema de Configurações** com 8 seções organizadas
- 🛡️ **Robustez Enterprise** com sistemas de retry e fallback
- 🌐 **API REST** com documentação completa

---

**Sistema Enterprise de Web Scraping + CV Analysis - Versão 5.0.0**
*Novo: Sistema completo de análise de currículos com OCR e Machine Learning*