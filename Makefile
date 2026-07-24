# Local build and pre-publish checks for sdd-plus-plus.
# Mirrors .github/workflows: test.yml, pylint.yml, python-publish.yml

.PHONY: help status vars install-dev lint test build check-release test-wheel check clean clean-build clean-all upload-testpypi graphify-update

PYTHON ?= python3
VENV ?= .venv
VENV_BIN = $(VENV)/bin
WHEEL_VENV ?= .venv-wheel-test
WHEEL_BIN = $(WHEEL_VENV)/bin

# Read version from pyproject.toml (single source of truth).
VERSION := $(shell $(PYTHON) -c "import pathlib,re; m=re.search(r'^version\\s*=\\s*\"([^\"]+)\"', pathlib.Path('pyproject.toml').read_text(), re.M); print(m.group(1) if m else '')")
PROJECT := sdd-plus-plus
DIST_GLOB = dist/$(PROJECT)-$(VERSION)-py3-none-any.whl

# Default: show help
.DEFAULT_GOAL := help

##@ Environment

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
	/^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } \
	/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Examples:"
	@echo "  make install-dev    # editable install for day-to-day dev"
	@echo "  make check          # lint + test + build + twine check + wheel smoke test"
	@echo "  make build          # wheel + sdist in dist/"
	@echo "  make test-wheel     # install dist/*.whl in $(WHEEL_VENV) and run sdd --version"
	@echo ""
	@echo "Override Python: make build PYTHON=python3.12"

status: ## Show Python, version, and dist artifacts
	@echo "📦 $(PROJECT) v$(VERSION)"
	@echo "🐍 Python: $$($(PYTHON) --version 2>&1) ($$(command -v $(PYTHON) || echo 'not found'))"
	@if [ -x "$(VENV_BIN)/python" ]; then echo "📂 Dev venv: $(VENV) ($$($(VENV_BIN)/python --version))"; fi
	@if [ -d dist ]; then echo "📁 dist/:"; ls -la dist/ 2>/dev/null || true; else echo "📁 dist/: (empty — run make build)"; fi

vars: ## Print Makefile variables
	@echo "PROJECT=$(PROJECT)"
	@echo "VERSION=$(VERSION)"
	@echo "PYTHON=$(PYTHON)"
	@echo "DIST_GLOB=$(DIST_GLOB)"

##@ Development

install-dev: ## Editable install with [full] extras (pytest, fastmcp, …)
	$(PYTHON) -m pip install -e ".[full]"

lint: ## Run pylint (same scope as CI)
	$(PYTHON) -m pip install -q pylint
	$(PYTHON) -m pylint src/sdd --fail-under=8.0

test: ## Run pytest suite
	$(PYTHON) -m pip install -q -e ".[full]"
	$(PYTHON) -m pytest

graphify-update: ## Refresh Graphify code graph (AST only, no API key)
	@command -v graphify >/dev/null || (echo "❌ graphify not on PATH — pipx install graphifyy"; exit 1)
	graphify update .
	@echo "✅ graphify-out/graph.json updated"

##@ Release (local)

build: clean-build ## Build wheel + sdist into dist/
	@test -n "$(VERSION)" || (echo "❌ Could not read version from pyproject.toml"; exit 1)
	@echo "🔨 Building $(PROJECT) $(VERSION)..."
	$(PYTHON) -m pip install -q build
	$(PYTHON) -m build
	@echo "✅ Artifacts in dist/:"
	@ls -la dist/

check-release: build ## Validate dist/ with twine
	$(PYTHON) -m pip install -q twine
	@echo "🔍 twine check..."
	@ARTS=$$(find dist -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' \)); \
	if [ -z "$$ARTS" ]; then echo "❌ No files in dist/. Run 'make build' first."; exit 1; fi; \
	$(PYTHON) -m twine check $$ARTS
	@echo "✅ twine check passed"

test-wheel: check-release ## Install wheel in a fresh venv and smoke-test the CLI
	@echo "🧪 Smoke-testing wheel in $(WHEEL_VENV)..."
	@rm -rf "$(WHEEL_VENV)"
	$(PYTHON) -m venv "$(WHEEL_VENV)"
	"$(WHEEL_BIN)/pip" install -q --upgrade pip
	"$(WHEEL_BIN)/pip" install -q dist/*.whl
	@echo "   sdd --version → $$("$(WHEEL_BIN)/sdd" --version)"
	"$(WHEEL_BIN)/sdd" --version
	"$(WHEEL_BIN)/sdd" --help >/dev/null
	@echo "✅ Wheel install and CLI smoke test passed"
	@echo "   Try: $(WHEEL_BIN)/sdd init --dry-run  (in a temp repo)"

check: lint test check-release test-wheel ## Full pre-publish gate (CI + wheel test)

upload-testpypi: check-release ## Upload dist/ to TestPyPI (needs TEST_TWINE_USERNAME / TEST_TWINE_PASSWORD)
	@if [ -z "$$TEST_TWINE_USERNAME" ] || [ -z "$$TEST_TWINE_PASSWORD" ]; then \
	  echo "❌ Export TEST_TWINE_USERNAME and TEST_TWINE_PASSWORD"; exit 1; \
	fi
	@echo "🚀 Uploading $(PROJECT) $(VERSION) to TestPyPI..."
	@ARTS=$$(find dist -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' \)); \
	TWINE_USERNAME=$$TEST_TWINE_USERNAME TWINE_PASSWORD=$$TEST_TWINE_PASSWORD \
	  $(PYTHON) -m twine upload --repository testpypi $$ARTS

##@ Cleanup

clean-build: ## Remove dist/ and build/ only
	rm -rf dist build

clean: clean-build ## Remove build artifacts and caches
	rm -rf "$(WHEEL_VENV)" .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

clean-all: clean ## clean + test caches
	@echo "✅ Clean complete"
