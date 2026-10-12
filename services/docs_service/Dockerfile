FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del microservicio (sin GUI ni librerías pesadas)
COPY services/docs_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el módulo central desacoplado y los activos institucionales
COPY core/ /app/core/
COPY assets/ /app/assets/
COPY services/docs_service/ /app/services/docs_service/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "services/docs_service/worker.py"]
