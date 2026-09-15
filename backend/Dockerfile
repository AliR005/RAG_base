FROM python:3.14-slim

WORKDIR /srv/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
  && rm -rf /var/lib/apt/lists/* \
  && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev

COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini backend/models.yaml backend/template.yaml ./

EXPOSE 8000

CMD ["sh", "-c", ".venv/bin/alembic upgrade head && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"]
