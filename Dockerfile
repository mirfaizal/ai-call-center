# ── Stage 1: Build Angular frontend ──────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app/ui

COPY ui/package.json ui/package-lock.json ./
RUN npm ci --prefer-offline

# Copy the rest of the frontend source
COPY ui/ ./
# Build the Angular application
RUN npm run build --configuration=production

# ── Stage 2: Python runtime + nginx + supervisord ─────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system packages: nginx, supervisor, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source files
COPY . .

# Setup Nginx configuration
RUN rm -f /etc/nginx/sites-enabled/default \
    /etc/nginx/conf.d/default.conf
COPY deploy/nginx_hf.conf /etc/nginx/conf.d/app.conf

# Copy compiled Angular app from Stage 1
COPY --from=frontend-builder /app/ui/dist/automated-call-dashboard/browser /usr/share/nginx/html

# Setup Supervisord configuration
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Allow nginx to write its pid and cache files
RUN mkdir -p /var/cache/nginx /var/run \
    && chown -R root:root /var/cache/nginx

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:7860/api/health || exit 1

# Start supervisord to manage both nginx and uvicorn
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
