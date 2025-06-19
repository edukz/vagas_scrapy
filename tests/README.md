# 🧪 Testes do Sistema de Robustez Enterprise

Este diretório contém todos os testes organizados por categoria para facilitar manutenção e execução.

## 📁 Estrutura Organizada

```
tests/
├── unit/                           # Testes unitários dos módulos
│   ├── test_retry_simple.py        # Teste do sistema de retry
│   ├── test_fallback_selectors.py  # Teste de fallback de seletores  
│   ├── test_data_validator.py      # Teste de validação de dados
│   ├── test_structured_logger.py   # Teste de logs estruturados
│   ├── test_circuit_breaker.py     # Teste de circuit breaker
│   └── test_metrics_tracker.py     # Teste de métricas
├── integration/                    # Testes de integração
│   ├── test_alert_system.py        # Teste completo do sistema de alertas
│   └── test_validation_integration.py # Teste de integração da validação
├── examples/                       # Exemplos e demonstrações
│   └── test_logging_demo.py        # Demo do sistema de logs
├── performance/                    # Testes de performance (vazio)
├── data/                          # Dados temporários de teste
├── logs/                          # Logs gerados pelos testes
└── config/                        # Configurações de teste
```

## 🚀 Como Executar os Testes

### Testes Unitários
```bash
# Executar testes individuais
python tests/unit/test_retry_simple.py
python tests/unit/test_fallback_selectors.py
python tests/unit/test_data_validator.py
python tests/unit/test_structured_logger.py
python tests/unit/test_circuit_breaker.py
python tests/unit/test_metrics_tracker.py
```

### Testes de Integração
```bash
# Sistema completo de alertas
python tests/integration/test_alert_system.py

# Integração da validação
python tests/integration/test_validation_integration.py
```

### Exemplos e Demonstrações
```bash
# Demo do sistema de logs
python tests/examples/test_logging_demo.py
```

## 🔄 Sistema de Retry

### Teste básico:
```bash
python tests/test_retry_simple.py
```

**Valida:**
- ✅ Operação bem-sucedida (1ª tentativa)
- 🔄 Falha intermitente (sucesso após retries)
- ❌ Timeout constante (falha após esgotar tentativas)

## 🎯 Sistema de Fallback de Seletores

### Teste de fallback:
```bash
python tests/test_fallback_selectors.py
```

**Valida:**
- ✅ 84 estratégias de seletores alternativos
- ✅ Sistema de scoring adaptativo
- ✅ Validação automática de dados
- ✅ Extração simulada com fallback

## 📋 Sistema de Validação de Dados

### Teste completo da validação:
```bash
python tests/test_data_validator.py
```

**Valida:**
- ✅ Limpeza e normalização de dados
- ✅ Validação por schemas
- ✅ Correção automática de formatos
- ✅ Detecção de anomalias

### Demo prático da validação:
```bash
python test_validation_demo.py
```

**Demonstra:**
- 📥 Como dados chegam do scraper
- 🔍 Processo de validação em ação
- 📊 Relatório de qualidade
- 📤 Filtro de dados válidos/inválidos

### Teste de integração completo:
```bash
python tests/test_validation_integration.py
```

**Inclui:**
- 🧪 6 cenários realistas de teste
- 🔧 Showcase de correções automáticas
- 🚨 Detecção de anomalias
- 🌐 Simulação de cenário real

## 🚀 Teste Completo (Scraper Real)

### Com todos os sistemas ativados:
```bash
python main.py
```

**Sistemas ativos:**
- 🔄 Retry automático
- 🎯 Fallback de seletores  
- 📋 Validação de dados
- 📊 Relatórios de qualidade

## 📊 Resultados Esperados

### Sistema de Retry:
```
📊 Taxa de sucesso: 93%+
🔄 Média de retries: 1.2
```

### Sistema de Fallback:
```
🎯 84 seletores alternativos
📈 95%+ taxa de extração
```

### Sistema de Validação:
```
📋 Qualidade geral: 80-95%
🔧 Correções automáticas aplicadas
⚠️ Anomalias detectadas e reportadas
```

## 💡 Como Interpretar os Testes

### ✅ **Sucesso**: 
- Sistemas funcionando conforme esperado
- Dados sendo corrigidos automaticamente
- Fallbacks ativando quando necessário

### ⚠️ **Avisos**:
- Dados com qualidade baixa mas corrigíveis
- Seletores secundários sendo usados
- Tentativas de retry necessárias

### ❌ **Erros**:
- Dados inválidos sendo filtrados
- Operações falhando após todas as tentativas
- Comportamento esperado para dados ruins