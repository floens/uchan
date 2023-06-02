FROM python:3.10-slim AS poetry-builder

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        libpq-dev \
    && curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY poetry.lock pyproject.toml ./

RUN poetry install --no-root --no-ansi --without dev

FROM node:18.16 as node-builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci

COPY esbuild.mjs ./
COPY frontend ./frontend

RUN npm run build

RUN ls -la

FROM python:3.10-slim

# Needed at runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=node-builder /app/build /app/build
COPY --from=poetry-builder /app/.venv ./.venv

ADD uchan /app/uchan
ADD docker /app/docker
ADD migrations /app/migrations
ADD alembic.ini /app/

ENTRYPOINT ["/app/docker/docker-entrypoint.sh"]
