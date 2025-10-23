.PHONY: help install start dev docker-build docker-run docker-stop clean

# Default target
help:
	@echo "CopilotKit Multi-Service Application"
	@echo ""
	@echo "Available targets:"
	@echo "  make install       - Install all dependencies (Node.js + Python)"
	@echo "  make start         - Start all services locally (development mode)"
	@echo "  make dev           - Alias for 'make start'"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container (requires OPENAI_API_KEY)"
	@echo "  make docker-stop   - Stop running Docker container"
	@echo "  make clean         - Clean build artifacts and dependencies"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. Copy .env.example to .env and add your OPENAI_API_KEY"
	@echo "  2. Run 'make install' to install dependencies"
	@echo "  3. Run 'make start' to start all services"
	@echo ""

# Install all dependencies
install:
	@echo "Installing dependencies..."
	@echo ""
	@echo "Installing Node.js dependencies..."
	cd client && npm install
	@echo ""
	@echo "Installing Python dependencies..."
	cd server && uv sync
	@echo ""
	@echo "Installation complete!"
	@echo ""

# Start all services in development mode
start:
	@echo "Starting all services..."
	@echo ""
	@echo "This will start:"
	@echo "  - Python Backend (FastAPI) on port 8000"
	@echo "  - BFF (Express) on port 4000"
	@echo "  - Frontend (Vite) on port 5173"
	@echo ""
	@if [ ! -f .env ]; then \
		echo "WARNING: .env file not found!"; \
		echo "Copy .env.example to .env and configure your OPENAI_API_KEY"; \
		echo ""; \
		exit 1; \
	fi
	@echo "Starting services in parallel..."
	@trap 'kill 0' EXIT; \
	(cd server && make start) & \
	sleep 3 && \
	(cd client && make start) & \
	wait

# Alias for start
dev: start

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t copilotkit-demo .
	@echo ""
	@echo "Docker image built successfully!"
	@echo "Run 'make docker-run' to start the container"
	@echo ""

# Run Docker container
docker-run:
	@if [ -z "$$OPENAI_API_KEY" ] && [ ! -f .env ]; then \
		echo "ERROR: OPENAI_API_KEY not set!"; \
		echo ""; \
		echo "Either:"; \
		echo "  1. Set environment variable: export OPENAI_API_KEY=your_key"; \
		echo "  2. Create .env file with OPENAI_API_KEY=your_key"; \
		echo ""; \
		exit 1; \
	fi
	@echo "Starting Docker container..."
	@if [ -f .env ]; then \
		docker run -d \
			--name copilotkit-demo \
			--env-file .env \
			-p 5173:5173 \
			-p 4000:4000 \
			-p 8000:8000 \
			copilotkit-demo; \
	else \
		docker run -d \
			--name copilotkit-demo \
			-e OPENAI_API_KEY=$$OPENAI_API_KEY \
			-p 5173:5173 \
			-p 4000:4000 \
			-p 8000:8000 \
			copilotkit-demo; \
	fi
	@echo ""
	@echo "Container started! Access the application at:"
	@echo "  http://localhost:5173"
	@echo ""
	@echo "To view logs: docker logs -f copilotkit-demo"
	@echo "To stop: make docker-stop"
	@echo ""

# Stop Docker container
docker-stop:
	@echo "Stopping Docker container..."
	@docker stop copilotkit-demo 2>/dev/null || true
	@docker rm copilotkit-demo 2>/dev/null || true
	@echo "Container stopped and removed"
	@echo ""

# Clean build artifacts and dependencies
clean:
	@echo "Cleaning build artifacts..."
	rm -rf client/node_modules
	rm -rf client/dist
	rm -rf server/.venv
	rm -rf server/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete!"
	@echo ""
