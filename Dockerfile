# Use an official Python runtime as a base image
FROM python:3.11.7-slim-bullseye 

# Install system dependencies required for building certain Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl wget ffmpeg \
    redis-server \
    supervisor \
    libffi-dev \
    libssl-dev \
    zlib1g-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container to /app
WORKDIR /app

RUN pip install poetry --no-cache-dir 
RUN poetry self add poetry-plugin-dotenv
RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock* /app/

# Install main dependencies and add celery and redis
RUN poetry add celery redis
RUN poetry install --only main --no-interaction --no-ansi

# Copy the entire application
COPY . /app
WORKDIR /app

# Install any additional dependencies that might be required for Celery
RUN poetry install --no-interaction --no-ansi

# Create necessary directories
RUN mkdir -p /data /app/logs

# Set up environment variables
ENV PYTHONPATH=/app
ENV CELERY_BROKER_URL=redis://localhost:6379/0
ENV CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Copy supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Use supervisord as the entry point
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
