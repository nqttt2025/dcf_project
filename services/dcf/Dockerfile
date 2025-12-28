FROM python:3.11-slim

# Build argument for version
ARG VERSION=latest
ENV APP_VERSION=${VERSION}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy common requirements first
COPY services/common/requirements.txt /app/common_requirements.txt

# Install common dependencies
RUN pip install --no-cache-dir -r /app/common_requirements.txt

# Copy project source code
COPY src /app/src
COPY config /app/config
COPY data /app/data

# Copy service code
COPY services/dcf/main.py /app/main.py

# Create necessary directories
RUN mkdir -p /app/data/results /app/data/cache /app/logs/app /app/logs/docker

# Set PYTHONPATH
ENV PYTHONPATH=/app

LABEL version="${VERSION}"
LABEL maintainer="DCF Project"

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

