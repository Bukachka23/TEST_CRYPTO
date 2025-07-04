# Makefile for Transcription Audio to Notes Project
# ================================================

# Variables
PYTHON := python3
PIP := pip3
VENV_DIR := .venv
SRC_DIR := src
TESTS_DIR := tests
DOCS_DIR := docs
CONFIG_DIR := config
OUTPUT_DIR := src/output

# Colors for output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)Transcription Audio to Notes - Available Commands$(NC)"
	@echo "=================================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment Setup
.PHONY: venv
venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "$(GREEN)Virtual environment created. Activate with: source $(VENV_DIR)/bin/activate$(NC)"

.PHONY: install
install: ## Install project dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -e .
	@echo "$(GREEN)Dependencies installed successfully$(NC)"

.PHONY: install-dev
install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	$(PIP) install ruff pytest pytest-cov mypy black isort
	@echo "$(GREEN)Development dependencies installed successfully$(NC)"

.PHONY: requirements
requirements: ## Generate requirements.txt from current environment
	@echo "$(BLUE)Generating requirements.txt...$(NC)"
	$(PIP) freeze > requirements.txt
	@echo "$(GREEN)requirements.txt generated$(NC)"

# Project Execution
.PHONY: run
run: ## Run the main application
	@echo "$(BLUE)Running transcription pipeline...$(NC)"
	$(PYTHON) -m src.main

.PHONY: cli
cli: ## Run CLI interface with help
	@echo "$(BLUE)Running CLI interface...$(NC)"
	$(PYTHON) -m src.main --help

.PHONY: transcribe
transcribe: ## Run transcription with default settings (requires audio file path)
	@echo "$(BLUE)Running transcription...$(NC)"
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please specify audio file with FILE=path/to/audio$(NC)"; \
		exit 1; \
	fi
	$(PYTHON) -m src.main transcribe "$(FILE)"

# Code Quality & Linting
.PHONY: lint
lint: ## Run ruff linter
	@echo "$(BLUE)Running ruff linter...$(NC)"
	ruff check $(SRC_DIR)

.PHONY: lint-fix
lint-fix: ## Run ruff linter with auto-fix
	@echo "$(BLUE)Running ruff linter with auto-fix...$(NC)"
	ruff check --fix $(SRC_DIR)

.PHONY: format
format: ## Format code with ruff
	@echo "$(BLUE)Formatting code with ruff...$(NC)"
	ruff format $(SRC_DIR)

.PHONY: format-check
format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	ruff format --check $(SRC_DIR)

.PHONY: type-check
type-check: ## Run mypy type checking
	@echo "$(BLUE)Running mypy type checking...$(NC)"
	mypy $(SRC_DIR) --ignore-missing-imports

.PHONY: check-all
check-all: lint format-check type-check ## Run all code quality checks
	@echo "$(GREEN)All code quality checks completed$(NC)"

# Testing
.PHONY: test
test: ## Run tests with pytest
	@echo "$(BLUE)Running tests...$(NC)"
	pytest $(TESTS_DIR) -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	pytest-watch $(TESTS_DIR) -- -v

# Documentation
.PHONY: docs
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@if [ -d "$(DOCS_DIR)" ]; then \
		cd $(DOCS_DIR) && make html; \
	else \
		echo "$(YELLOW)No docs directory found. Skipping documentation generation.$(NC)"; \
	fi

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@if [ -d "$(DOCS_DIR)/_build/html" ]; then \
		cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8000; \
	else \
		echo "$(RED)Documentation not built. Run 'make docs' first.$(NC)"; \
	fi

# Project Management
.PHONY: clean
clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "$(GREEN)Cleanup completed$(NC)"

.PHONY: clean-output
clean-output: ## Clean output directory
	@echo "$(BLUE)Cleaning output directory...$(NC)"
	@if [ -d "$(OUTPUT_DIR)" ]; then \
		rm -rf $(OUTPUT_DIR)/*; \
		echo "$(GREEN)Output directory cleaned$(NC)"; \
	else \
		echo "$(YELLOW)Output directory not found$(NC)"; \
	fi

.PHONY: clean-logs
clean-logs: ## Clean log files
	@echo "$(BLUE)Cleaning log files...$(NC)"
	find . -name "*.log" -type f -delete
	@echo "$(GREEN)Log files cleaned$(NC)"

.PHONY: clean-all
clean-all: clean clean-output clean-logs ## Clean everything
	@echo "$(GREEN)Complete cleanup finished$(NC)"

# Development Workflow
.PHONY: dev-setup
dev-setup: venv install-dev ## Complete development environment setup
	@echo "$(GREEN)Development environment setup completed$(NC)"
	@echo "$(YELLOW)Don't forget to activate your virtual environment:$(NC)"
	@echo "source $(VENV_DIR)/bin/activate"

.PHONY: pre-commit
pre-commit: format lint test ## Run pre-commit checks (format, lint, test)
	@echo "$(GREEN)Pre-commit checks completed successfully$(NC)"

.PHONY: ci
ci: check-all test-cov ## Run CI pipeline (all checks + tests with coverage)
	@echo "$(GREEN)CI pipeline completed successfully$(NC)"

# Project Information
.PHONY: info
info: ## Show project information
	@echo "$(BLUE)Project Information$(NC)"
	@echo "=================="
	@echo "Project: Transcription Audio to Notes"
	@echo "Python Version: $(shell $(PYTHON) --version)"
	@echo "Virtual Environment: $(VENV_DIR)"
	@echo "Source Directory: $(SRC_DIR)"
	@echo "Tests Directory: $(TESTS_DIR)"
	@echo "Config Directory: $(CONFIG_DIR)"
	@echo "Output Directory: $(OUTPUT_DIR)"

.PHONY: deps
deps: ## Show installed dependencies
	@echo "$(BLUE)Installed Dependencies$(NC)"
	@echo "======================"
	$(PIP) list

# Audio Processing Shortcuts
.PHONY: process-sample
process-sample: ## Process sample audio file (if exists in test_audio/)
	@echo "$(BLUE)Processing sample audio...$(NC)"
	@if [ -d "test_audio" ] && [ -n "$$(ls -A test_audio/ 2>/dev/null)" ]; then \
		SAMPLE_FILE=$$(ls test_audio/ | head -1); \
		echo "Processing: $$SAMPLE_FILE"; \
		$(PYTHON) -m src.main transcribe "test_audio/$$SAMPLE_FILE"; \
	else \
		echo "$(YELLOW)No sample audio files found in test_audio/ directory$(NC)"; \
	fi

# Utility targets
.PHONY: check-python
check-python: ## Check Python installation and version
	@echo "$(BLUE)Checking Python installation...$(NC)"
	@$(PYTHON) --version
	@which $(PYTHON)

.PHONY: check-deps
check-deps: ## Check if required tools are installed
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@command -v ruff >/dev/null 2>&1 || echo "$(RED)ruff not found. Install with: pip install ruff$(NC)"
	@command -v pytest >/dev/null 2>&1 || echo "$(RED)pytest not found. Install with: pip install pytest$(NC)"
	@command -v mypy >/dev/null 2>&1 || echo "$(RED)mypy not found. Install with: pip install mypy$(NC)"
	@echo "$(GREEN)Dependency check completed$(NC)"

# Make sure intermediate files are not deleted
.PRECIOUS: $(VENV_DIR) 