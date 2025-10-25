# Repository Guidelines

> Concise contributor guide for the CopilotKit stack (client + server).

## Project Structure & Modules
- Root: orchestration files (Makefile, Dockerfile, scripts/).
- Client (Vite + React + TS): client/src, static assets in client/public, dev server helpers in client/server.
- Server (Python): entrypoints server/server.py and server/agent.py; config in server/.env[.example].
- Docs: README.md (root and within subprojects when present).

## Build, Test, and Development
- Root services: make start (runs client + BFF + Python server via script).
- Docker: make docker-build then make docker-run (requires OPENAI_API_KEY).
- Client dev: cd client && npm run dev (Vite), BFF: npm run bff, build: npm run build, preview: npm run preview.
- Server dev: cd server && make start (uv + Python). Quality checks: make lint, make typecheck, make format, make check.

## Coding Style & Naming
- TypeScript: follow ESLint config in client/eslint.config.js. Prefer PascalCase for components, camelCase for variables/functions, kebab-case for file names (except React components).
- Python: Ruff for lint/format; type checking with Pyright. Use snake_case for modules/functions, PascalCase for classes.
- Indentation: 2 spaces (TS), 4 spaces (Python). Keep functions small and typed (TS: explicit props types; Py: type hints).

## Testing Guidelines
- Client: Playwright is available; add tests under client/tests or client/e2e with *.spec.ts. Run via project script if added.
- Server: Prefer pytest (if/when introduced). Place tests in server/tests mirroring module paths. Aim for meaningful coverage on core logic.

## Commit & Pull Requests
- Commits: present-tense imperative ("Add server healthcheck"), scoped changes per commit. Reference issues with #123.
- Branches: feat/*, fix/*, chore/*, docs/*.
- PRs: include clear description, reproduction steps, screenshots for UI, and note config/env changes (server/.env.example). Ensure client build passes and server make check is clean.

## Security & Configuration
- Never commit secrets. Copy server/.env.example to server/.env. Required: OPENAI_API_KEY. For Docker, export envs before make docker-run.
- Validate inputs at API boundaries (BFF/server). Log minimally; avoid sensitive data in logs.
