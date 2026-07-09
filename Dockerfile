# ---- Base image ----
# Slim keeps the image small; pin the version for reproducible builds.
FROM python:3.12-slim

# Don't buffer stdout/stderr (logs show up immediately in kubectl logs),
# and don't write .pyc files inside the container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY app .

# Run as a non-root user (Kubernetes/EKS best practice).
# Create the user, make the logs dir, and give the user ownership of /app so
# the app can write logs/app.log at runtime.
RUN useradd --create-home appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Note: no --reload in production. Bind to 0.0.0.0 so the container is reachable.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
