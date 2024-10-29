# Dockerfile for deploying to PaaS platforms

# use the latest python3.12-slim image with uv preinstalled
FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /usr/src/app

COPY . .
# install dependencies
RUN uv sync

CMD [ "uv", "run", "run.py", "--botconfig", "./config/bot_config.json", "--bot_verbose"]