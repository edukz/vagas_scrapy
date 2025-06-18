# 🔍 Catho Job Scraper - Versão Modular

Sistema avançado de scraping para vagas de emprego home office do site Catho.com.br, desenvolvido com arquitetura modular e otimizações de performance.

## 📁 Estrutura do Projeto

```
catho-scraper/
├── src/                    # Código fonte principal
│   ├── __init__.py        # Inicialização do pacote
│   ├── cache.py           # Sistema de cache inteligente
│   ├── scraper.py         # Lógica principal de scraping
│   ├── filters.py         # Sistema de filtros avançados
│   ├── navigation.py      # Navegação multi-página
│   └── utils.py           # Utilitários e performance
├── config/                # Configurações do sistema
│   └── settings.py        # Configurações padrão
├── data/                  # Dados e resultados
│   ├── cache/            # Cache de requisições
│   └── resultados/       # Arquivos gerados
│       ├── json/         # Dados em formato JSON
│       ├── csv/          # Planilhas para análise
│       ├── txt/          # Relatórios legíveis
│       └── relatorios/   # Análises estatísticas
├── docs/                  # Documentação
├── main.py               # Arquivo principal de execução
└── README.md             # Este arquivo
```

## 🚀 Funcionalidades

### 🔍 **Coleta Inteligente**
- ✅ Navegação automática por múltiplas páginas
- ✅ Detecção automática do tipo de paginação
- ✅ Extração completa de informações das vagas
- ✅ Tratamento robusto de erros

### ⚡ **Performance Otimizada**
- ✅ Processamento paralelo (até 5 vagas simultâneas)
- ✅ Cache inteligente (6h de validade)
- ✅ Rate limiting adaptativo
- ✅ Monitoramento de performance em tempo real

### 🎯 **Filtros Avançados**
- ✅ Filtro por tecnologias específicas
- ✅ Filtro por faixa salarial
- ✅ Filtro por nível de experiência
- ✅ Filtro por tipo de empresa
- ✅ Filtro por palavras-chave

### 📊 **Análise Automática**
- ✅ Detecção automática de tecnologias
- ✅ Categorização de empresas
- ✅ Análise salarial
- ✅ Relatórios estatísticos completos

### 💾 **Múltiplos Formatos**
- ✅ JSON (dados estruturados)
- ✅ CSV (planilhas Excel)
- ✅ TXT (relatórios legíveis)
- ✅ Relatórios de análise

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)

### 1. Clone ou baixe o projeto
```bash
# Se usando git
git clone [URL_DO_REPOSITORIO]
cd catho-scraper

# Ou extraia o ZIP baixado
```

### 2. Instale as dependências
```bash
pip install playwright asyncio
```

### 3. Instale os navegadores do Playwright
```bash
python -m playwright install
```

## 🎮 Como Usar

### Execução Básica
```bash
python main.py
```

### Interface Interativa
O sistema oferece uma interface amigável que permite:

1. **Configurar Filtros** (opcional)
   - Tecnologias desejadas
   - Salário mínimo
   - Nível de experiência
   - Tipo de empresa
   - Palavras-chave

2. **Configurar Performance**
   - Número de vagas simultâneas (1-5)
   - Número de páginas a analisar (1-10)

3. **Acompanhar Progresso**
   - Monitoramento em tempo real
   - Estatísticas de performance
   - Indicadores visuais

## 📊 Exemplo de Uso

```bash
=== WEB SCRAPER CATHO (VERSÃO MODULARIZADA) ===

Deseja aplicar filtros às vagas? (s/n)
s

=== CONFIGURAÇÃO DE FILTROS AVANÇADOS ===

1. FILTRO POR TECNOLOGIAS
Digite as tecnologias desejadas: python, react, node

2. FILTRO POR SALÁRIO MÍNIMO
Digite o salário mínimo desejado: 8000

⚡ CONFIGURAÇÃO DE PERFORMANCE:
Quantas vagas processar simultaneamente? (1-5): 3

📄 CONFIGURAÇÃO DE PÁGINAS:
Quantas páginas analisar? (1-10): 5

============================================================
INICIANDO COLETA COM ARQUITETURA MODULAR...
============================================================
```

## 📁 Arquivos Gerados

Após a execução, os resultados são organizados em:

```
data/resultados/
├── json/
│   └── vagas_catho_20241218_1430.json    # Dados estruturados
├── csv/
│   └── vagas_catho_20241218_1430.csv     # Para Excel/Sheets
├── txt/
│   └── vagas_catho_20241218_1430.txt     # Relatório legível
└── relatorios/
    └── analise_completa_20241218_1430.txt # Estatísticas
```

## ⚙️ Configurações

### Arquivo de Configuração
Edite `config/settings.py` para personalizar:

- URLs de scraping
- Configurações de cache
- Timeouts e performance
- Listas de tecnologias
- Tipos de empresa

### Exemplo de Personalização
```python
# config/settings.py
DEFAULT_MAX_PAGES = 10        # Aumentar páginas padrão
CACHE_MAX_AGE_HOURS = 12     # Cache mais duradouro
REQUESTS_PER_SECOND = 1.0    # Mais conservador
```

## 🔧 Arquitetura Modular

### Módulos Principais

| Módulo | Responsabilidade |
|--------|-----------------|
| `cache.py` | Sistema de cache inteligente com persistência |
| `scraper.py` | Lógica principal de extração de dados |
| `filters.py` | Sistema de filtros e categorização |
| `navigation.py` | Navegação por múltiplas páginas |
| `utils.py` | Utilitários, performance e salvamento |

### Benefícios da Modularização
- 🧩 **Manutenibilidade**: Cada responsabilidade em seu módulo
- 🔧 **Extensibilidade**: Fácil adicionar novas funcionalidades
- 🧪 **Testabilidade**: Módulos podem ser testados isoladamente
- 🔄 **Reutilização**: Componentes podem ser usados independentemente

## 📈 Performance

### Métricas Típicas
- **Velocidade**: 2-5 vagas/segundo
- **Eficiência do Cache**: 70-90%
- **Taxa de Sucesso**: 95%+
- **Páginas Simultâneas**: Até 10

### Otimizações Implementadas
- Cache inteligente com TTL
- Rate limiting adaptativo
- Processamento assíncrono
- Pool de páginas reutilizáveis
- Detecção automática de erros

## ❗ Resolução de Problemas

### Erro: "Navegadores não encontrados"
```bash
python -m playwright install
```

### Performance Lenta
- Reduza o número de páginas simultâneas
- Verifique a conexão com internet
- Limpe o cache (`data/cache/`)

### Erro de Imports
Certifique-se de que está executando do diretório raiz:
```bash
cd catho-scraper
python main.py
```

## 📝 Licença

Este projeto é para fins educacionais e de pesquisa. Respeite os termos de uso do site Catho.com.br.

## 🤝 Contribuições

Sugestões e melhorias são bem-vindas! Este projeto foi desenvolvido com foco em:
- Código limpo e bem documentado
- Arquitetura modular e extensível
- Performance otimizada
- Facilidade de uso

---

**Versão**: 2.0.0 (Arquitetura Modular)  
**Última Atualização**: Dezembro 2024