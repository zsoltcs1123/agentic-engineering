.PHONY: help install format lint type-check test test-cov clean sync

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies and package in editable mode
	uv sync --dev
	uv pip install -e .

sync: ## Sync dependencies (update lock file)
	uv sync --dev

format: ## Format code with Ruff
	uv run ruff format .

lint: ## Lint code with Ruff
	uv run ruff check .

lint-fix: ## Lint and auto-fix code with Ruff
	uv run ruff check --fix .

type-check: ## Run type checking with Mypy
	uv run mypy .

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=packages --cov-report=term --cov-report=html

test-unit: ## Run only unit tests
	uv run pytest -m unit

test-integration: ## Run only integration tests
	uv run pytest -m integration

check: format lint type-check test ## Run all checks (format, lint, type-check, test)

pre-commit: ## Run all pre-commit hooks
	uv run pre-commit run --all-files

clean: ## Clean cache and build artifacts
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type d -name .pytest_cache -exec rm -r {} +
	find . -type d -name .mypy_cache -exec rm -r {} +
	find . -type d -name .ruff_cache -exec rm -r {} +
	find . -type d -name .coverage -exec rm -r {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
