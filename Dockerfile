# Build stage
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy your application code
COPY . .

# Copy .env file
#COPY .env .

# Set the working directory to /app/app
WORKDIR /app/app

# Run your FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]