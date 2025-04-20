# Use a specific tag (not latest) for reproducibility
FROM ahmed377/apptemp:v10

# Set environment variables to avoid interactive prompts and keep image clean
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

# Set working directory early to keep layers consistent
WORKDIR /app

# Install dependencies, cleanup to reduce image size
RUN apt-get update && apt-get install -y curl && \
    pip install --no-cache-dir pylint && \
    curl -sSL https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 \
        -o /usr/local/bin/hadolint && \
    chmod +x /usr/local/bin/hadolint && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ../tests/ .
