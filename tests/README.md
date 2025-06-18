# 🧪 Testes do Sistema

## Teste do Sistema de Retry

### Como executar:

```bash
# Na pasta raiz do projeto:
python tests/test_retry_simple.py

# Ou dentro da pasta tests:
cd tests
python test_retry_simple.py
```

### O que o teste valida:

1. ✅ **Operação bem-sucedida** - Funciona na primeira tentativa
2. 🔄 **Falha intermitente** - Retry automático com sucesso após 3 tentativas
3. ❌ **Timeout constante** - Falha corretamente após esgotar tentativas

### Resultado esperado:

```
📊 Taxa de sucesso: 66.7%
📊 Média de retries: 1.00
```

### Para testar o scraper completo:

```bash
python main.py
```

O sistema de retry está integrado e funcionará automaticamente durante o scraping.