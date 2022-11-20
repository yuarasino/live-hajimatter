FROM node:18 as node

FROM python:3 as python

# Install nodejs
ENV \
  NPM_CONFIG_UPDATE_NOTIFIER=false

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm

RUN \
  ln -s /usr/local/bin/node /usr/local/bin/nodejs; \
  ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm; \
  ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# Install poetry
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

# Install frontend deps
WORKDIR /live-hajimatter/frontend

COPY ./frontend/package.json ./frontend/package-lock.json ./

RUN \
  npm install

# Install backend deps
WORKDIR /live-hajimatter/backend

COPY ./backend/pyproject.toml ./backend/poetry.lock ./

RUN \
  poetry install

# Move to project root
WORKDIR /live-hajimatter
