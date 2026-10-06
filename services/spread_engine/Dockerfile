FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY services/spread-engine/requirements.txt /app/services/spread-engine/requirements.txt
RUN pip install --no-cache-dir -r /app/services/spread-engine/requirements.txt

COPY packages /app/packages
COPY services/spread-engine /app/services/spread-engine

CMD ["python", "-m", "pytest", "services/spread-engine/tests"]
