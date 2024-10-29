# Dockerfile for deploying to PaaS platforms

FROM python:3.12

WORKDIR /usr/src/app

COPY . .

# setup uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo '. $HOME/.cargo/env' >> $HOME/.bashrc
# install dependencies
RUN . $HOME/.bashrc && uv sync

CMD [ "uv", "run", "run.py", "--botconfig", "./config/bot_config.json", "--bot_verbose"]