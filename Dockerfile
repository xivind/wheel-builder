FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8004

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004", "--log-config", "uvicorn_log_config.ini"]

# Healthcheck to monitor the container for errors
HEALTHCHECK --interval=600s --retries=1 --timeout=3s CMD grep -q "error" status.txt && exit 1 || exit 0