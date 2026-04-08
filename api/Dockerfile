FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY api /app/api
COPY shared /app/shared

EXPOSE 8000

CMD ["ddtrace-run", "uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "/app/shared/uvicorn_logging.json"]
