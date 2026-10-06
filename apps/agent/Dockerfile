FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

COPY . /app

RUN groupadd -r agentuser && useradd -r -g agentuser -d /app -s /sbin/nologin agentuser \
    && chown -R agentuser:agentuser /app

USER agentuser

CMD ["python", "main.py"]
