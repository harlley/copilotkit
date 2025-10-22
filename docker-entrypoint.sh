#!/bin/bash
set -e

echo "=================================================="
echo "Starting CopilotKit Multi-Service Application"
echo "=================================================="
echo ""

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable is required!"
    echo "Please set it using: docker run -e OPENAI_API_KEY=your_key_here ..."
    exit 1
fi

# Display configuration
echo "Configuration:"
echo "  Frontend (Vite): http://localhost:5173"
echo "  BFF (Express):   http://localhost:${BFF_PORT:-4000}/api/copilotkit"
echo "  Backend (FastAPI): http://localhost:${PORT:-8000}/api/copilotkit"
echo ""

# Function to handle shutdown
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill -TERM "$BACKEND_PID" "$BFF_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" "$BFF_PID" "$FRONTEND_PID" 2>/dev/null || true
    echo "All services stopped."
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start Python Backend (LangGraph + FastAPI)
echo "Starting Python Backend on port ${PORT:-8000}..."
cd /app/server
uv run python server.py &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:${PORT:-8000}/health > /dev/null 2>&1; then
        echo "  Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: Backend failed to start after 30 seconds"
        kill -TERM "$BACKEND_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Start BFF (Express)
echo ""
echo "Starting BFF (Express) on port ${BFF_PORT:-4000}..."
cd /app/client
npm run bff &
BFF_PID=$!
echo "  BFF PID: $BFF_PID"

# Wait a moment for BFF to start
sleep 2

# Start Frontend (Vite preview for production build)
echo ""
echo "Starting Frontend (Vite) on port 5173..."
cd /app/client
npm run preview -- --port 5173 --host 0.0.0.0 &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

# Display startup complete message
echo ""
echo "=================================================="
echo "All services started successfully!"
echo "=================================================="
echo ""
echo "Access the application at:"
echo "  http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
