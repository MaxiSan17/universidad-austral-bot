FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements_simple.txt .
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements_simple.txt

# Copiar c�digo de la aplicaci�n
COPY . .

# Crear directorio para logs
RUN mkdir -p /app/logs

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la aplicaci�n
CMD ["python", "main_simple.py"]