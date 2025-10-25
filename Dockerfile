FROM node:20-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --upgrade pip \
    && pip install uv

WORKDIR /app

# Install Python dependencies first to leverage caching
COPY server/pyproject.toml server/uv.lock ./server/
RUN uv pip sync --system server/uv.lock

# Install Node dependencies
COPY client/package.json client/package-lock.json ./client/
RUN npm install --prefix client --no-audit --no-fund

# Copy project files
COPY . .

RUN chmod +x scripts/start-services.sh

EXPOSE 5173 4000 8000

ENV PORT=8000 \
    BFF_PORT=4000 \
    FRONTEND_PORT=5173

ENTRYPOINT ["./scripts/start-services.sh"]
