#!/bin/bash

# 🚀 Script de Setup da API REST - Catho Job Scraper
# Este script automatiza a configuração inicial da API

set -e  # Para em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir com cores
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Banner
print_header "🚀 SETUP DA API REST - CATHO JOB SCRAPER"
print_header "=================================================="

# Verificar se estamos no diretório correto
# Se executado da pasta scripts, mudar para diretório pai
if [[ "$(basename $PWD)" == "scripts" ]]; then
    cd ..
fi

if [[ ! -f "api/main.py" ]]; then
    print_error "Este script deve ser executado no diretório raiz do projeto!"
    print_error "Uso: cd /caminho/para/projeto && ./scripts/setup_api.sh"
    exit 1
fi

# 1. Verificar dependências do sistema
print_header "\n1. 🔍 Verificando dependências do sistema..."

# Verificar Docker
if command -v docker &> /dev/null; then
    print_status "✅ Docker encontrado: $(docker --version)"
else
    print_warning "❌ Docker não encontrado"
    echo "Instale o Docker: https://docs.docker.com/get-docker/"
fi

# Verificar Docker Compose
if command -v docker-compose &> /dev/null; then
    print_status "✅ Docker Compose encontrado: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    print_status "✅ Docker Compose (plugin) encontrado"
    alias docker-compose="docker compose"
else
    print_warning "❌ Docker Compose não encontrado"
    echo "Instale o Docker Compose: https://docs.docker.com/compose/install/"
fi

# Verificar Python
if command -v python3 &> /dev/null; then
    print_status "✅ Python3 encontrado: $(python3 --version)"
else
    print_warning "❌ Python3 não encontrado"
fi

# 2. Configurar ambiente
print_header "\n2. ⚙️  Configurando ambiente..."

# Criar .env se não existir
if [[ ! -f ".env" ]]; then
    print_status "Criando arquivo .env a partir do template..."
    cp .env.example .env
    
    # Gerar SECRET_KEY aleatória
    if command -v openssl &> /dev/null; then
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i "s/your-super-secret-key-change-this-in-production-256-bits-minimum/$SECRET_KEY/" .env
        print_status "✅ SECRET_KEY gerada automaticamente"
    else
        print_warning "⚠️  OpenSSL não encontrado. Configure SECRET_KEY manualmente no .env"
    fi
    
    print_warning "📝 Revise e ajuste as configurações no arquivo .env"
else
    print_status "✅ Arquivo .env já existe"
fi

# Criar diretórios necessários
print_status "Criando diretórios necessários..."
mkdir -p data/cache
mkdir -p logs
mkdir -p exports
mkdir -p ssl
mkdir -p deployments/monitoring/grafana/dashboards
mkdir -p deployments/monitoring/grafana/provisioning

print_status "✅ Diretórios criados"

# 3. Escolher método de instalação
print_header "\n3. 📦 Escolha o método de instalação:"
echo "1) Docker Compose (Recomendado - Produção)"
echo "2) Instalação Manual (Desenvolvimento)"
echo "3) Apenas verificar estrutura"

read -p "Digite sua escolha (1-3): " choice

case $choice in
    1)
        print_header "\n🐳 Instalação com Docker Compose"
        
        # Verificar se Docker está rodando
        if ! docker info &> /dev/null; then
            print_error "Docker não está rodando. Inicie o serviço Docker primeiro."
            exit 1
        fi
        
        print_status "Fazendo build das imagens..."
        cd deployments && docker-compose build
        
        print_status "Iniciando serviços..."
        docker-compose up -d && cd ..
        
        print_status "Aguardando serviços ficarem prontos..."
        sleep 10
        
        # Verificar se API está funcionando
        if curl -f http://localhost/api/v1/health &> /dev/null; then
            print_status "✅ API está funcionando!"
        else
            print_warning "⚠️  API pode estar ainda inicializando..."
        fi
        
        print_header "\n🎉 INSTALAÇÃO CONCLUÍDA!"
        echo ""
        echo "📋 URLs importantes:"
        echo "   • API: http://localhost:8000"
        echo "   • Documentação: http://localhost:8000/docs"
        echo "   • Grafana: http://localhost:3000 (admin/admin123)"
        echo "   • Prometheus: http://localhost:9090"
        echo ""
        echo "🔧 Comandos úteis:"
        echo "   • Ver logs: docker-compose logs -f api"
        echo "   • Parar: docker-compose down"
        echo "   • Reiniciar: docker-compose restart api"
        ;;
        
    2)
        print_header "\n🐍 Instalação Manual"
        
        # Verificar Python
        if ! command -v python3 &> /dev/null; then
            print_error "Python3 é necessário para instalação manual"
            exit 1
        fi
        
        # Criar ambiente virtual
        if [[ ! -d "venv" ]]; then
            print_status "Criando ambiente virtual..."
            python3 -m venv venv
        fi
        
        print_status "Ativando ambiente virtual..."
        source venv/bin/activate
        
        # Instalar dependências
        if [[ -f "requirements.txt" ]]; then
            print_status "Instalando dependências Python..."
            pip install --upgrade pip
            pip install -r requirements.txt
        else
            print_error "requirements.txt não encontrado!"
            exit 1
        fi
        
        print_header "\n🎉 INSTALAÇÃO MANUAL CONCLUÍDA!"
        echo ""
        echo "🚀 Para executar a API:"
        echo "   source venv/bin/activate"
        echo "   python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
        echo ""
        echo "📋 URLs:"
        echo "   • API: http://localhost:8000"
        echo "   • Documentação: http://localhost:8000/docs"
        ;;
        
    3)
        print_header "\n🔍 Verificando estrutura..."
        python3 test_structure.py
        ;;
        
    *)
        print_error "Opção inválida!"
        exit 1
        ;;
esac

# 4. Testes finais
if [[ $choice == "1" ]] || [[ $choice == "2" ]]; then
    print_header "\n4. 🧪 Executando testes básicos..."
    
    # Testar estrutura
    python3 test_structure.py
    
    # Testar API se estiver rodando
    if curl -f http://localhost:8000/api/v1/health &> /dev/null; then
        print_status "✅ API Health Check passou"
        
        # Testar documentação
        if curl -f http://localhost:8000/docs &> /dev/null; then
            print_status "✅ Documentação acessível"
        fi
    else
        print_warning "⚠️  API não está acessível em http://localhost:8000"
    fi
fi

# 5. Instruções finais
print_header "\n📚 PRÓXIMOS PASSOS:"
echo ""
echo "1. 🔐 Configurar usuários:"
echo "   • Admin padrão: admin / admin123"
echo "   • User padrão: user / user123"
echo ""
echo "2. 🧪 Testar API:"
echo "   curl http://localhost:8000/api/v1/health"
echo ""
echo "3. 📖 Consultar documentação:"
echo "   • README.md - Documentação geral"
echo "   • API_README.md - Documentação específica da API"
echo "   • DEPLOYMENT.md - Guia de deploy"
echo ""
echo "4. 🚀 Fazer primeiro scraping:"
echo "   • Acesse http://localhost:8000/docs"
echo "   • Use /auth/token para obter token"
echo "   • Use /api/v1/scraping/start para iniciar"
echo ""

print_header "🎉 SETUP CONCLUÍDO COM SUCESSO!"

exit 0