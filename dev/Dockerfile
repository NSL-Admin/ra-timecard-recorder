# Dockerfile for development in local environment

FROM python:3

# PostgreSQL is necessary to use psycopg2 package
RUN apt-get update && apt-get install -y postgresql postgresql-contrib

# Install requirements
COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt