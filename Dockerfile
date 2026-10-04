FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY app ./app
COPY knowledge ./knowledge
COPY scripts ./scripts

RUN addgroup --system nexo && adduser --system --ingroup nexo nexo \
    && chown -R nexo:nexo /app
USER nexo

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
