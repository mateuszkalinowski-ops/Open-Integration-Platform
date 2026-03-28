# Contributing to Open Integration Platform by Pinquark.com

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- Docker and Docker Compose
- Git

### Clone and install

```bash
git clone https://github.com/mateuszkalinowski-ops/Open-Integration-Platform.git
cd open-integration-platform

# Install shared library
cd shared/python
pip install -e ".[dev]"
cd ../..

# Install a specific connector's dependencies
cd integrators/courier/inpost/v3.0.0
pip install -r requirements.txt
cd ../../../..
```

### Run locally

```bash
# Start platform + database + Redis + dashboard (development mode)
docker compose up -d

# Or start full production-like stack with all connectors
docker compose -f docker-compose.prod.yml up -d

# Or run a single connector in development mode
cd integrators/courier/inpost/v3.0.0
cp .env.example .env
uvicorn src.app:app --reload --port 8000
```

## Creating a New Connector

1. Copy the template:

```bash
cp -r integrators/courier/_template integrators/{category}/{system-name}/v1.0.0
```

2. Create `connector.yaml` manifest:

```yaml
name: my-system
category: courier  # courier | ecommerce | erp | wms | automation | other
version: 1.0.0
display_name: "My System"
description: "Integration with My System API"
interface: courier  # courier | ecommerce | erp | generic
capabilities:
  - create_shipment
  - get_label
events:
  - shipment.status_changed
actions:
  - shipment.create
  - label.get
config_schema:
  required:
    - api_key
  optional:
    - sandbox_mode
health_endpoint: /health
docs_url: /docs
```

3. Implement the integration class in `src/integration.py` inheriting from the appropriate base interface.

4. Write tests in `tests/` with >80% coverage.

5. Add documentation in `docs/{category}/{system-name}/v1.0.0/`.

## Coding Standards

### Python

- **Formatter**: `ruff format`
- **Linter**: `ruff check`
- **Type checker**: `mypy --strict`
- **Tests**: `pytest` with `pytest-asyncio`
- **Line length**: 120 characters
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes

```bash
# Run all checks
ruff check .
ruff format --check .
mypy src/ --strict
pytest tests/ -v --cov --cov-report=term-missing
```

### Angular (Dashboard)

- **Angular CLI** for generating components/services
- **Strict TypeScript** (`strict: true` in tsconfig)
- **Angular Material** for UI components
- **Reactive Forms** for all form handling
- **OnPush change detection** for all components
- **Naming**: `kebab-case` for files, `PascalCase` for classes, `camelCase` for methods

```bash
cd platform/dashboard
ng lint
ng test
ng build integrations-lib
```

### General Rules

- No hardcoded URLs or credentials — use environment variables
- All external API calls must have explicit timeouts (30s connect, 60s read)
- Retry with exponential backoff (max 3 retries) for external calls
- Structured JSON logging — never log PII
- Every connector must expose `/health` and `/readiness` endpoints

## Commit Convention

```
[CATEGORY-SYSTEM] action: description

Examples:
  [COURIER-DHL] feat: add multi-parcel shipment support
  [ECOMMERCE-ALLEGRO] fix: handle expired OAuth token gracefully
  [PLATFORM] feat: add flow engine with any-to-any routing
  [DASHBOARD] feat: add connector marketplace page
  [SDK-PYTHON] feat: add FlowAPI client
```

## Pull Request Process

1. Fork the repository and create a branch from `main`:
   - `feature/courier-new-system` for new connectors
   - `fix/inpost-label-format` for bug fixes
   - `docs/allegro-api-mapping` for documentation

2. Ensure all checks pass:
   - Linting (`ruff check`, `ng lint`)
   - Tests with >80% coverage
   - Type checking (`mypy`)
   - Docker build succeeds

3. Update documentation if you changed APIs or added features.

4. Submit PR against `main` branch with a clear description of changes.

5. A maintainer will review your PR. Address any feedback promptly.

## Reporting Issues

Use GitHub Issues with the appropriate template:
- **Bug Report**: for bugs in connectors or platform
- **Feature Request**: for new connectors or platform features
- **Connector Request**: to request integration with a new system

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
