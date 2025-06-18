# 🚀 Web Scraper Catho - Versão Enhanced

Sistema profissional de coleta e análise de vagas de emprego com notificações inteligentes, agendamento automático e análise avançada.

## 📋 Índice
- [Recursos](#recursos)
- [Arquitetura](#arquitetura)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [API](#api)
- [Melhorias Implementadas](#melhorias-implementadas)
- [Roadmap](#roadmap)

## 🎯 Recursos

### Core Features
- ✅ **Web Scraping Inteligente**: Coleta automática de vagas com detecção de paginação
- ✅ **Cache Multi-Nível**: Memória + disco com expiração configurável
- ✅ **Rate Limiting Adaptativo**: Ajusta velocidade baseado em respostas
- ✅ **Processamento Paralelo**: Múltiplas páginas simultaneamente
- ✅ **Análise Avançada**: Detecção de tecnologias, categorização automática

### Sistema de Notificações
- ✅ **Email**: Templates HTML responsivos com resumo das vagas
- ✅ **Telegram**: Notificações instantâneas via bot
- ✅ **Webhook**: Integração com sistemas externos
- 🔄 **Discord/Slack**: Em desenvolvimento

### Filtragem e Análise
- ✅ **Filtros Múltiplos**: Tecnologia, salário, nível, empresa, palavras-chave
- ✅ **Detecção de Tecnologias**: Identifica automaticamente skills
- ✅ **Análise Salarial**: Extrai e normaliza faixas salariais
- ✅ **Categorização**: Classifica nível e tipo de empresa

### Performance e Escalabilidade
- ✅ **Processamento Assíncrono**: Máxima eficiência
- ✅ **Pool de Conexões**: Reutilização de recursos
- ✅ **Monitoramento**: Métricas em tempo real
- 🔄 **Proxy Rotation**: Em desenvolvimento

## 🏗️ Arquitetura

```
web-scraper-catho/
├── main.py                 # Scraper principal
├── main_enhanced.py        # Versão com notificações e agendamento
├── notification_system.py  # Sistema de notificações multi-canal
├── requirements.txt        # Dependências básicas
├── requirements_enhanced.txt # Todas as dependências
├── .env.example           # Exemplo de configuração
├── cache/                 # Cache de dados
├── resultados/            # Resultados organizados
│   ├── json/
│   ├── txt/
│   ├── csv/
│   └── relatorios/
└── logs/                  # Logs do sistema
```

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/web-scraper-catho.git
cd web-scraper-catho
```

### 2. Crie ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale dependências
```bash
# Versão básica
pip install -r requirements.txt

# Versão completa (recomendado)
pip install -r requirements_enhanced.txt
```

### 4. Instale o navegador
```bash
playwright install chromium
```

## ⚙️ Configuração

### 1. Configure variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

### 2. Configure Email (Gmail)
1. Ative "Verificação em duas etapas" na sua conta Google
2. Gere uma "Senha de app" em: https://myaccount.google.com/apppasswords
3. Use essa senha no arquivo .env

### 3. Configure Telegram Bot
1. Abra o Telegram e procure por @BotFather
2. Envie `/newbot` e siga as instruções
3. Copie o token fornecido para o .env
4. Para obter seu chat_id:
   - Envie uma mensagem para seu bot
   - Acesse: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Procure por "chat":{"id": XXXXXXX}

### 4. Configure Webhook (Opcional)
Use serviços como:
- webhook.site (para testes)
- Zapier
- Make (Integromat)
- Seu próprio endpoint

## 📖 Uso

### Modo Básico (Original)
```bash
python main.py
```

### Modo Enhanced (Com Notificações)
```bash
python main_enhanced.py
```

Opções disponíveis:
1. **Executar uma vez**: Coleta e notifica imediatamente
2. **Modo agendado**: Executa automaticamente em horários definidos
3. **Configurar usuários**: Cria perfis de exemplo
4. **Modo básico**: Executa sem notificações

### Configurar Preferências de Usuário

```python
from notification_system import UserPreferencesManager

manager = UserPreferencesManager()
manager.add_user('meu_id', {
    'email': 'meu@email.com',
    'email_notifications': True,
    'telegram_chat_id': '123456789',
    'telegram_notifications': True,
    'required_technologies': ['python', 'django'],
    'minimum_salary': 8000,
    'experience_levels': ['pleno', 'senior'],
    'keywords': ['remoto', 'CLT'],
    'notifications_enabled': True
})
```

## 🔌 API (Em Desenvolvimento)

### Endpoints Planejados
```
GET  /api/jobs              # Lista vagas
GET  /api/jobs/{id}         # Detalhes da vaga
POST /api/jobs/search       # Busca com filtros
GET  /api/stats             # Estatísticas
POST /api/alerts            # Criar alerta
GET  /api/alerts/{user_id}  # Listar alertas
```

## ✨ Melhorias Implementadas

### 1. Sistema de Notificações ✅
- Email com templates HTML bonitos
- Bot Telegram funcional
- Suporte a webhooks
- Preferências por usuário

### 2. Agendamento Automático ✅
- Execução em horários específicos
- Intervalos configuráveis
- Logs detalhados

### 3. Cache Inteligente ✅
- Dois níveis (memória + disco)
- Expiração configurável
- Limpeza automática

### 4. Análise Avançada ✅
- Detecção automática de tecnologias
- Categorização de empresas
- Análise salarial

## 🗺️ Roadmap

### Fase 1: Foundation (Concluído ✅)
- [x] Scraper básico funcional
- [x] Sistema de cache
- [x] Rate limiting
- [x] Processamento paralelo

### Fase 2: Intelligence (Em Progresso 🔄)
- [x] Sistema de notificações
- [x] Agendamento automático
- [ ] Machine Learning para categorização
- [ ] Análise de sentimento

### Fase 3: Scale (Planejado 📋)
- [ ] Suporte multi-site (LinkedIn, Indeed, etc)
- [ ] API REST completa
- [ ] Interface web
- [ ] Banco de dados PostgreSQL

### Fase 4: Enterprise (Futuro 🚀)
- [ ] Dashboard analytics
- [ ] Proxy rotation
- [ ] Kubernetes deployment
- [ ] SaaS model

## 🐛 Troubleshooting

### Erro: "Page closed"
- Aumente o timeout nas configurações
- Verifique sua conexão com a internet

### Erro: "Cache permission denied"
- Execute: `chmod -R 755 cache/`
- Verifique permissões da pasta

### Notificações não funcionam
- Verifique credenciais no .env
- Teste conexão SMTP/Telegram manualmente
- Verifique logs em `scraper.log`

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🙏 Agradecimentos

- Playwright team pela excelente biblioteca
- Comunidade Python pelos packages incríveis
- Você por usar e contribuir!

---

**Nota**: Este projeto é apenas para fins educacionais. Respeite os termos de serviço dos sites ao fazer scraping.