#!/usr/bin/env bash
set -euo pipefail

# Run tests for an integrator.
#
# Usage: ./test.sh <category> <system> <version>
#
# Example:
#   ./test.sh ecommerce allegro 1.0.0
#   ./test.sh courier dhl 1.0.0

CATEGORY="${1:?Usage: test.sh <category> <system> <version>}"
SYSTEM="${2:?Usage: test.sh <category> <system> <version>}"
VERSION="${3:?Usage: test.sh <category> <system> <version>}"

INTEGRATOR_DIR="integrators/${CATEGORY}/${SYSTEM}/v${VERSION}"

if [ ! -d "$INTEGRATOR_DIR" ]; then
  echo "ERROR: Directory not found: $INTEGRATOR_DIR"
  exit 1
fi

echo "============================================"
echo "Testing: ${CATEGORY}/${SYSTEM} v${VERSION}"
echo "Dir:     ${INTEGRATOR_DIR}"
echo "============================================"

cd "$INTEGRATOR_DIR"

if [ -f "requirements.txt" ]; then
  echo "==> Installing dependencies..."
  pip install --no-cache-dir -r requirements.txt
  pip install pytest pytest-asyncio pytest-cov httpx 2>/dev/null || true
fi

SHARED_LIB="../../../../shared/python"
if [ -d "$SHARED_LIB" ]; then
  echo "==> Installing shared library..."
  pip install --no-cache-dir "$SHARED_LIB" 2>/dev/null || true
fi

if [ -d "tests" ] && [ "$(find tests -name 'test_*.py' | head -1)" ]; then
  echo "==> Running tests..."
  python -m pytest tests/ \
    -v \
    --tb=short \
    --cov=src \
    --cov-report=term \
    --cov-report=xml:coverage.xml

  COVERAGE=$(python -m pytest tests/ --cov=src --cov-report=term 2>/dev/null | grep "^TOTAL" | awk '{print $NF}' || echo "unknown")
  echo "==> Coverage: ${COVERAGE}"
else
  echo "WARNING: No tests found in ${INTEGRATOR_DIR}/tests/"
  echo "AGENTS.md requires >80% test coverage (section 12.1)"
  exit 0
fi

echo "==> Tests passed!"
