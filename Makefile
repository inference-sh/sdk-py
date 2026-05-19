# SDK-PY Makefile
#
# Usage:
#   make install                          # Set up venv and install deps
#   make test                             # Run unit tests
#   make test-int API_KEY=your-api-key    # Run integration tests
#   make help                             # Show all targets
#
# Or export INFERENCE_API_KEY and just run: make test-int

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

API_KEY ?= $(INFERENCE_API_KEY)
BASE_URL ?= $(INFERENCE_BASE_URL)

# =============================================================================
# Setup & Build
# =============================================================================

.PHONY: install install-dev build clean clean-all venv

# Create virtual environment if it doesn't exist
$(VENV)/bin/activate:
	@echo "Creating virtual environment..."
	python3 -m venv --without-pip $(VENV)
	@echo "Bootstrapping pip..."
	curl -sS https://bootstrap.pypa.io/get-pip.py | $(PYTHON)

venv: $(VENV)/bin/activate

# Install the package (creates venv if needed)
install: venv
	@echo "Installing package..."
	$(PIP) install -e .

# Install with dev/test dependencies
install-dev: venv
	@echo "Installing package with dev dependencies..."
	$(PIP) install -e ".[test,async]"
	$(PIP) install pytest-asyncio

# Build package
build: clean venv
	$(PIP) install build
	$(PYTHON) -m build

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Clean everything including venv
clean-all: clean
	rm -rf $(VENV)

# =============================================================================
# Tests
# =============================================================================

.PHONY: test test-cov test-int test-int-dev test-file check-venv

# Check that venv exists
check-venv:
	@if [ ! -f "$(PYTEST)" ]; then \
		echo "ERROR: Virtual environment not set up. Run: make install-dev"; \
		exit 1; \
	fi

# Unit tests (mocked, no API key needed)
test: check-venv
	$(PYTEST) tests/ -v

# Unit tests with coverage
test-cov: check-venv
	$(PYTEST) tests/ -v --cov=inferencesh --cov-report=term-missing

# Integration tests (requires API key)
test-int: check-venv check-key
	INFERENCE_API_KEY=$(API_KEY) INFERENCE_BASE_URL=$(BASE_URL) $(PYTEST) tests/test_integration.py -v

# Integration tests against dev API (uses dev seed key by default)
DEV_API_KEY ?= 1nfsh-dev-0000000000000000000
test-int-dev: check-venv
	INFERENCE_API_KEY=$(DEV_API_KEY) INFERENCE_BASE_URL=https://api-dev.inference.sh $(PYTEST) tests/test_integration.py -v

# Integration tests against local dev API
test-int-local: check-venv
	INFERENCE_API_KEY=$(DEV_API_KEY) INFERENCE_BASE_URL=http://localhost:3021 $(PYTEST) tests/test_integration.py -v

# Run a specific test file
test-file: check-venv
	@test -n "$(FILE)" || (echo "Usage: make test-file FILE=tests/test_client.py" && exit 1)
	$(PYTEST) $(FILE) -v

# =============================================================================
# Examples (for manual testing/demos)
# =============================================================================

.PHONY: example

# Run a specific example: make example NAME=agent_chat
example: check-venv check-key
ifndef NAME
	@echo "Usage: make example NAME=<example-name>"
	@echo ""
	@echo "Available examples:"
	@ls -1 examples/*.py | xargs -I {} basename {} .py | sed 's/^/  /'
else
	INFERENCE_API_KEY=$(API_KEY) INFERENCE_BASE_URL=$(BASE_URL) $(PYTHON) examples/$(NAME).py
endif

# =============================================================================
# Version & Release
# =============================================================================

.PHONY: patch minor major release publish

patch:
	@./scripts/bump.sh patch

minor:
	@./scripts/bump.sh minor

major:
	@./scripts/bump.sh major

# Push and create GitHub release (triggers PyPI publish via CI)
release:
	@VERSION=$$(git describe --tags --abbrev=0) && \
	git push origin HEAD "$$VERSION" && \
	gh release create "$$VERSION" --title "$$VERSION" --generate-notes && \
	echo "Released $$VERSION"

# Manual publish to PyPI
publish: build
	$(PIP) install twine
	$(PYTHON) -m twine upload dist/*

# =============================================================================
# Code Quality
# =============================================================================

.PHONY: lint typecheck format check

lint: check-venv
	$(PYTHON) -m flake8 src/inferencesh tests --max-line-length=100

typecheck: check-venv
	$(PYTHON) -m mypy src/inferencesh --ignore-missing-imports

format: check-venv
	$(PYTHON) -m black src/inferencesh tests examples

check: check-venv
	$(PYTHON) -c "from inferencesh import inference, AgentRuntimeConfig, is_terminal_status; print('All imports OK')"

# =============================================================================
# Helpers
# =============================================================================

.PHONY: check-key help

check-key:
ifndef API_KEY
	$(error API_KEY is not set. Use: make <target> API_KEY=your-key or export INFERENCE_API_KEY)
endif
ifeq ($(strip $(API_KEY)),)
	$(error API_KEY is empty. Use: make <target> API_KEY=your-key or export INFERENCE_API_KEY)
endif

.PHONY: help
help:
	@echo "SDK-PY Makefile"
	@echo ""
	@echo "Usage: make <target> [API_KEY=your-key]"
	@echo ""
	@echo "Setup:"
	@echo "  install        Create venv and install package"
	@echo "  install-dev    Install with test dependencies"
	@echo "  clean          Clean build artifacts"
	@echo "  clean-all      Clean everything including venv"
	@echo ""
	@echo "Tests:"
	@echo "  test           Run unit tests"
	@echo "  test-cov       Run unit tests with coverage"
	@echo "  test-int       Run integration tests (requires API_KEY)"
	@echo "  test-int-dev   Run integration tests against dev API"
	@echo ""
	@echo "Examples:"
	@echo "  example NAME=agent_chat    Run a specific example"
	@echo ""
	@echo "Release:"
	@echo "  patch          Bump patch version"
	@echo "  minor          Bump minor version"
	@echo "  major          Bump major version"
	@echo "  release        Create GitHub release (triggers PyPI publish)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint / typecheck / format / check"

.DEFAULT_GOAL := help

main:
	git push origin dev:main
