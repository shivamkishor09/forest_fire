FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY services/data-pipeline/requirements.txt /app/services/data-pipeline/requirements.txt
RUN pip install --no-cache-dir -r /app/services/data-pipeline/requirements.txt

COPY packages /app/packages
COPY services/data-pipeline /app/services/data-pipeline

CMD ["python", "-m", "pytest", "services/data-pipeline/tests"]
