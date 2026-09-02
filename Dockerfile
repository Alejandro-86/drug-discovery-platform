FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

ENV SENTENCE_TRANSFORMERS_HOME=/app/models_cache

EXPOSE 8000
CMD ["uvicorn", "drug_discovery.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
