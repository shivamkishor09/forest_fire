FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY services/risk-engine/requirements.txt /app/services/risk-engine/requirements.txt
RUN pip install --no-cache-dir -r /app/services/risk-engine/requirements.txt

COPY packages /app/packages
COPY services/risk-engine /app/services/risk-engine

CMD ["python", "-m", "pytest", "services/risk-engine/tests"]
