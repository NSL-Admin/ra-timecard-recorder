# Dockerfile for deploying to PaaS platforms

# use the latest python3.12-slim image with uv preinstalled
FROM ghcr.io/astral-sh/uv:python3.12-alpine

RUN apk --no-cache add tzdata && \
    cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    apk del tzdata

WORKDIR /usr/src/app

COPY . .
# install dependencies
RUN uv sync

# command for production
CMD [ "uv", "run", "run.py", "--botconfig", "./config/bot_config.json", "--bot_verbose", "--use-sentry"]