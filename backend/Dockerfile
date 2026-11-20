FROM python:3.13-slim

WORKDIR /app

# Install curl for docker healthcheck probe
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged system user
RUN groupadd -g 1000 sentinel && \
    useradd -u 1000 -g sentinel -m -s /bin/bash sentinel && \
    mkdir -p /app/data && \
    chown -R sentinel:sentinel /app && \
    chmod 775 /app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Normalize line endings and executable permissions for Windows checkouts
RUN sed -i 's/\r$//' /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    chown -R sentinel:sentinel /app

USER sentinel
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
