FROM node:22-bookworm-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set up Python virtual environment and install uv
RUN python3 -m venv /venv
ENV PATH="/venv/bin:${PATH}"
RUN pip install --upgrade pip \
    && pip install uv

# Copy Python dependency files and install dependencies
COPY server/pyproject.toml server/uv.lock ./server/
ENV UV_PROJECT_ENVIRONMENT=/venv
RUN cd server && uv sync --no-install-project

# Copy Node.js dependency files and install dependencies
COPY client/package.json client/package-lock.json ./client/
RUN npm ci --prefix client --include=dev --no-audit --no-fund

# Copy the rest of the source code
COPY . .

# Build the frontend for production
RUN npm run build --prefix client

# Create a non-root user and set permissions
RUN useradd -m appuser && chown -R appuser:appuser /app
RUN chown -R appuser:appuser /venv
USER appuser

# Make the start script executable
RUN chmod +x scripts/start-services.sh

# Expose the necessary ports
EXPOSE 5173 4000 8000

# Set environment variables
ENV NODE_ENV=production \
    PORT=8000 \
    BFF_PORT=4000 \
    FRONTEND_PORT=5173

# Healthcheck to monitor the server's status
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD wget -qO- http://localhost:${PORT}/health || exit 1

# The command to start the services
ENTRYPOINT ["./scripts/start-services.sh"]
