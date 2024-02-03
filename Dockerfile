# Dockerfile for deploying to PaaS platforms

FROM python:3

WORKDIR /usr/src/app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./run.py", "--botconfig", "./config/bot_config.json"]