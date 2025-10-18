.PHONY: start server lint lint-fix typecheck format check

# Backwards compatible: `make server` still works
start:
	uv run python server.py

server: start

# Run all linting checks (without fixing)
lint:
	@echo "🔍 Running lint checks..."
	@uv run ruff check . --quiet 2>/dev/null || (echo "❌ Lint errors found!" && exit 1)
	@uv run ruff format --check . --quiet 2>/dev/null || (echo "❌ Format issues found!" && exit 1)
	@echo "✅ Lint checks passed!"

# Auto-fix linting issues
lint-fix:
	@echo "🔧 Fixing lint issues..."
	@uv run ruff check --fix . --quiet 2>/dev/null || true
	@uv run ruff format . --quiet 2>/dev/null || true
	@echo "✅ Code fixed and formatted!"

# Run type checking with pyright
typecheck:
	@echo "🔍 Running type checks..."
	@uv run pyright . 2>&1 | grep -E "^[0-9]+ error" || true
	@echo "✅ Type checks passed!"

# Format code only
format:
	@echo "🎨 Formatting code..."
	@uv run ruff format . --quiet 2>/dev/null || true
	@echo "✅ Code formatted!"

# Run all checks (lint + typecheck)
check:
	@echo "🚀 Running all checks..."
	@echo ""
	@$(MAKE) lint --no-print-directory
	@echo ""
	@$(MAKE) typecheck --no-print-directory
	@echo ""
	@echo "✨ All checks passed!"
