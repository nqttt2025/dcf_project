FROM python:3.11-slim

# Build argument for version
ARG VERSION=latest
ENV APP_VERSION=${VERSION}

WORKDIR /app

# Copy common requirements first
COPY services/common/requirements.txt /app/common_requirements.txt

# Install common dependencies
RUN pip install --no-cache-dir -r /app/common_requirements.txt

# Copy service code
COPY services/gateway/main.py /app/main.py

LABEL version="${VERSION}"
LABEL maintainer="DCF Project"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

