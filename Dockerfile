# Imagen base
FROM python:3.10-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos y el código
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --retries 10 --timeout 60 -r requirements.txt

# Copiar todo el contenido de la carpeta backend al contenedor
COPY backend/ ./backend/

# Asegurar que existan los directorios de estáticos
RUN mkdir -p backend/static/wallpapers

# Variable de entorno para el puerto (Koyeb lo requiere)
ENV PORT=8000
ENV PYTHONPATH=/app

# Comando de ejecución (forma de shell para expansión de variables)
CMD uvicorn backend.main:app --host 0.0.0.0 --port $PORT
