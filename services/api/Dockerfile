FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias de la API REST
COPY services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la API, funciones serverless, módulos core, activos y demo
COPY core/ /app/core/
COPY assets/ /app/assets/
COPY functions/ /app/functions/
COPY demo/ /app/demo/
COPY services/api/ /app/services/api/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
