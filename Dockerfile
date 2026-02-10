FROM python:3.12-slim

ENV POETRY_VERSION=1.7.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"


COPY pyproject.toml poetry.lock* ./


RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi
RUN pip install celery[redis] redis stripe

COPY . .


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]