# Dockerfile para Catho Job Scraper API
# Imagem multi-stage para otimizar tamanho final

# ====================
# STAGE 1: Build dependencies
# ====================
FROM python:3.11-slim as builder

# Definir argumentos de build
ARG DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema para build
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --user -r requirements.txt

# ====================
# STAGE 2: Runtime image
# ====================
FROM python:3.11-slim

# Definir argumentos e variáveis
ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Criar usuário não-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependências runtime mínimas
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar diretórios necessários
RUN mkdir -p /app/data/cache /app/logs /app/exports && \
    chown -R appuser:appuser /app

# Copiar dependências do stage builder
COPY --from=builder /root/.local /home/appuser/.local

# Definir diretório de trabalho
WORKDIR /app

# Copiar código da aplicação
COPY . .

# Ajustar permissões
RUN chown -R appuser:appuser /app

# Mudar para usuário não-root
USER appuser

# Adicionar binários locais ao PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expor portas
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Comando padrão
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]