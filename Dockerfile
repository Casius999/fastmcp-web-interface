FROM python:3.10-slim

WORKDIR /app

# Installation des dépendances du système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    API_LOG_LEVEL=info \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=50051 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Exposition du port
EXPOSE 8000

# Exécution de l'application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]