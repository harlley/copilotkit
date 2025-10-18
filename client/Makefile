SHELL := /bin/sh

# Configurable entry for the BFF
BFF_ENTRY ?= server/index.ts
BFF_PORT ?= 4000

.PHONY: start start-bff start-web stop

start:
	# Run BFF and frontend together with prefixed logs; Ctrl+C stops both
	set -m; \
	( npm run bff --silent 2>&1 | sed -e 's/^/[bff] /' ) & BFF_PID=$$!; \
	( npm run dev --silent 2>&1 | sed -e 's/^/[web] /' ); \
	kill $$BFF_PID >/dev/null 2>&1 || true

start-bff:
	npm run bff

start-web:
	npm run dev
