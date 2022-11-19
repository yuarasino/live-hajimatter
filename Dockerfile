FROM python:3

ENV \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONUTF8=1 \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on

RUN \
  pip install poetry; \
  poetry self add poethepoet[poetry_plugin]; \
  poetry config virtualenvs.in-project true


WORKDIR /live-hajimatter/backend

COPY ./backend/pyproject.toml ./backend/poetry.lock ./

RUN \
  poetry install


WORKDIR /live-hajimatter
