
.PHONY: start docker-build docker-run docker-run-prod

start:
	./scripts/start-services.sh

docker-build:
	docker build --no-cache -t copilotkit-stack .

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
		-e NODE_ENV=development \
		-e FRONTEND_PORT=$${FRONTEND_PORT:-5173} \
		-e BFF_PORT=$${BFF_PORT:-4000} \
		-e PORT=$${PORT:-8000} \
		copilotkit-stack

docker-run-prod:
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "ERROR: OPENAI_API_KEY must be exported before running this target."; \
		exit 1; \
	fi
	docker run --rm \
		-p $${FRONTEND_PORT:-5173}:$${FRONTEND_PORT:-5173} \
		-p $${BFF_PORT:-4000}:$${BFF_PORT:-4000} \
		-p $${PORT:-8000}:$${PORT:-8000} \
		-e OPENAI_API_KEY \
		-e NODE_ENV=production \
		-e FRONTEND_PORT=$${FRONTEND_PORT:-5173} \
		-e BFF_PORT=$${BFF_PORT:-4000} \
		-e PORT=$${PORT:-8000} \
		copilotkit-stack
