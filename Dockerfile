# Multi-service Dockerfile for CopilotKit Demo
# Runs Frontend (Vite/React), BFF (Express), and LangGraph Backend (FastAPI)

FROM node:20-slim AS frontend-builder

# Build the frontend
WORKDIR /app/client
COPY client/package*.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# Final stage - includes both Node.js and Python
FROM node:20-slim

# Install Python 3.11 and uv package manager
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy frontend build artifacts
COPY --from=frontend-builder /app/client/dist /app/client/dist

# Install Node.js dependencies (for BFF)
COPY client/package*.json /app/client/
WORKDIR /app/client
RUN npm ci --production
COPY client/server /app/client/server

# Install Python dependencies
WORKDIR /app/server
COPY server/pyproject.toml server/uv.lock* ./
RUN uv sync --frozen --no-dev

# Copy Python source code
COPY server/ ./

# Copy entrypoint script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Expose ports
# 5173: Frontend (Vite preview)
# 4000: BFF (Express)
# 8000: Python Backend (FastAPI)
EXPOSE 5173 4000 8000

# Environment variables defaults
ENV BFF_PORT=4000
ENV PORT=8000
ENV NODE_ENV=production

WORKDIR /app

# Start all services
ENTRYPOINT ["/app/docker-entrypoint.sh"]
