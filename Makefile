.PHONY: install test test-cov lint format all clean

install:
	pip install -e ".[dev]"

test:
	python3 -m pytest --ignore=tests/integration -q

test-cov:
	python3 -m pytest --ignore=tests/integration \
	  --cov=src/agentic_erp \
	  --cov-report=term-missing \
	  --cov-report=html:htmlcov \
	  -q

lint:
	python3 -m ruff check src/ tests/
	python3 -m mypy src/ --ignore-missing-imports

format:
	python3 -m ruff format src/ tests/
	python3 -m ruff check src/ tests/ --fix

hooks:
	pre-commit install

all: lint test-cov

clean:
	rm -rf htmlcov .coverage dist build *.egg-info __pycache__ .pytest_cache .mypy_cache .ruff_cache
