# Image for the `api` and `worker` services.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml ./
COPY pipeline ./pipeline
COPY api ./api
RUN pip install --no-cache-dir -e .

COPY alembic.ini ./
COPY scripts ./scripts

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
