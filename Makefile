
.PHONY: start docker-build docker-run

start:
	./scripts/start-services.sh

docker-build:
	docker build -t copilotkit-stack .

docker-run:
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "ERROR: OPENAI_API_KEY must be exported before running this target."; \
		exit 1; \
	fi
	docker run --rm \
		-p $${FRONTEND_PORT:-5173}:$${FRONTEND_PORT:-5173} \
		-p $${BFF_PORT:-4000}:$${BFF_PORT:-4000} \
		-p $${PORT:-8000}:$${PORT:-8000} \
		-e OPENAI_API_KEY \
		-e FRONTEND_PORT=$${FRONTEND_PORT:-5173} \
		-e BFF_PORT=$${BFF_PORT:-4000} \
		-e PORT=$${PORT:-8000} \
		copilotkit-stack
