.PHONY: help install install-dev test test-unit test-integration test-coverage lint format check clean run run-test pre-commit-install

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Forbin - Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@grep -E '^install.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@grep -E '^test.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@grep -E '^(lint|format|check):.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Running:$(NC)"
	@grep -E '^run.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@grep -E '^(clean|pre-commit-install):.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install production dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	uv sync --no-dev
	@echo "$(GREEN)+ Dependencies installed$(NC)"

install-dev: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	uv sync
	uv pip install pytest pytest-asyncio pytest-cov black ruff pre-commit
	@echo "$(GREEN)+ Development dependencies installed$(NC)"

test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	uv run pytest tests/ -v
	@echo "$(GREEN)+ All tests passed$(NC)"

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	uv run pytest tests/ -v
	@echo "$(GREEN)+ Unit tests passed$(NC)"

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	uv run pytest tests/test_integration.py -v
	@echo "$(GREEN)+ Integration tests passed$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	uv run pytest tests/ --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)+ Coverage report generated$(NC)"
	@echo "$(YELLOW)Open htmlcov/index.html to view detailed coverage$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode...$(NC)"
	uv run pytest-watch tests/ -v

lint: ## Run linter (ruff)
	@echo "$(GREEN)Running linter...$(NC)"
	uv run ruff check forbin tests/
	@echo "$(GREEN)+ Linting complete$(NC)"

format: ## Format code with black
	@echo "$(GREEN)Formatting code...$(NC)"
	uv run black forbin tests/
	@echo "$(GREEN)+ Code formatted$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(GREEN)Checking code formatting...$(NC)"
	uv run black --check forbin tests/
	@echo "$(GREEN)+ Code formatting is correct$(NC)"

check: format-check lint test ## Run all checks (format, lint, test)
	@echo "$(GREEN)+ All checks passed!$(NC)"

clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ htmlcov/ .coverage
	@echo "$(GREEN)+ Cleanup complete$(NC)"

run: ## Run the tool in interactive mode
	@echo "$(GREEN)Starting Forbin...$(NC)"
	uv run python run_forbin.py

run-test: ## Run the tool in connectivity test mode
	@echo "$(GREEN)Running connectivity test...$(NC)"
	uv run python run_forbin.py --test

run-help: ## Show tool help
	uv run python run_forbin.py --help

pre-commit-install: ## Install pre-commit hooks
	@echo "$(GREEN)Installing pre-commit hooks...$(NC)"
	uv run pre-commit install
	@echo "$(GREEN)+ Pre-commit hooks installed$(NC)"

pre-commit-run: ## Run pre-commit hooks manually
	@echo "$(GREEN)Running pre-commit hooks...$(NC)"
	uv run pre-commit run --all-files

validate: ## Validate Python syntax
	@echo "$(GREEN)Validating Python syntax...$(NC)"
	uv run python -m py_compile forbin/*.py
	uv run python -m py_compile tests/*.py
	@echo "$(GREEN)+ Syntax is valid$(NC)"

setup-env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		echo "$(GREEN)Creating .env file from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(YELLOW)! Please edit .env with your MCP server details$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

install-all: install-dev setup-env pre-commit-install ## Complete setup (install deps, create .env, setup hooks)
	@echo "$(GREEN)+ Complete setup finished!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env with your MCP server details"
	@echo "  2. Run 'make test' to verify setup"
	@echo "  3. Run 'make run-test' to test connectivity"

ci: lint format-check test ## Run CI checks (used by GitHub Actions)
	@echo "$(GREEN)+ CI checks passed!$(NC)"

# Development workflow targets
dev-setup: install-all ## Alias for install-all

quick-test: ## Quick test (no coverage)
	@uv run pytest tests/ -v --tb=short

watch: test-watch ## Alias for test-watch
