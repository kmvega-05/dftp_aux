FROM python:3.11-slim

WORKDIR /app

# Evita buffers en salida para ver logs en tiempo real
ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONPATH=/app

# Copia todo el proyecto al contenedor
COPY . /app

# Instala dependencias si existe requirements.txt (la instrucción es segura si no existe)
RUN set -e \
	&& if [ -f /app/requirements.txt ]; then pip install --no-cache-dir -r /app/requirements.txt; fi

# Puertos comunes usados por los nodos (no obligatorio)
EXPOSE 9100 9200 9201 9202

# Por defecto ejecutamos python; al hacer `docker run imagen <script>` se ejecutará ese script.
ENTRYPOINT ["python3"]

# Default command: primer script de prueba (puedes sobrescribir al hacer `docker run imagen tests/run_location.py ...`)
CMD ["tests/run_discovery.py"]
