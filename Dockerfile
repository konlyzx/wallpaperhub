# Usar una imagen ligera de Python
FROM python:3.10-slim

# Evitar que Python genere archivos .pyc y forzar salida a terminal
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema para psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos primero para aprovechar la caché de Docker
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del backend
COPY backend/ ./backend/

# Crear directorios para archivos estáticos
RUN mkdir -p backend/static/wallpapers

# Exponer el puerto que usará el servicio
EXPOSE 8000

# Comando para arrancar la app
# Usamos $PORT porque Render/Koyeb lo asignan dinámicamente
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
