# SEC Downloader Makefile

.PHONY: help install install-dev test lint format clean setup run-example

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"

setup:  ## Setup development environment
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"
	.venv/bin/python -m sec_downloader config --init

test:  ## Run tests
	pytest tests/ -v

test-cov:  ## Run tests with coverage
	pytest tests/ --cov=src/sec_downloader --cov-report=html --cov-report=term-missing

lint:  ## Run linting
	flake8 src/ tests/
	mypy src/

format:  ## Format code
	black src/ tests/

clean:  ## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-example:  ## Run basic usage example
	python examples/basic_usage.py

run-advanced:  ## Run advanced usage example
	python examples/advanced_usage.py

download-apple:  ## Download Apple's 10-K reports
	python -m sec_downloader download --convert AAPL

list-companies:  ## List available companies
	python -m sec_downloader list-tickers --limit 10

init-config:  ## Initialize configuration
	python -m sec_downloader config --init

show-config:  ## Show current configuration
	python -m sec_downloader config --show

build:  ## Build package
	python -m build

install-package:  ## Install built package
	pip install dist/*.whl

all: clean install-dev test lint format  ## Run all checks
