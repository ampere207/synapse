# Backend Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Install system dependencies (include build tools required for building numpy from source)
RUN apt-get update -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends -o Acquire::Retries=3 \
    build-essential \
    gcc \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    libffi-dev \
    libssl-dev \
    postgresql-client \
    python3-numpy \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Ensure packaging tools are available for building dependencies on slim images
RUN python -m pip install --upgrade pip setuptools wheel

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel build && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=10s \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
