#!/usr/bin/env bash
set -euo pipefail

# Build and push a Docker image for an integrator.
#
# Usage: ./build.sh <category> <system> <version> [build_context]
#
# Example:
#   ./build.sh courier dhl 1.0.0
#   ./build.sh ecommerce allegro 1.0.0

CATEGORY="${1:?Usage: build.sh <category> <system> <version> [build_context]}"
SYSTEM="${2:?Usage: build.sh <category> <system> <version> [build_context]}"
VERSION="${3:?Usage: build.sh <category> <system> <version> [build_context]}"
BUILD_CONTEXT="${4:-integrators/${CATEGORY}/${SYSTEM}/v${VERSION}}"

REGISTRY="${DOCKER_REGISTRY:-your-registry.example.com}"
IMAGE_BASE="${REGISTRY}/integrations/${CATEGORY}/${SYSTEM}"

TAG_VERSION="${IMAGE_BASE}:${VERSION}-uat"
TAG_SHA="${IMAGE_BASE}:$(git rev-parse --short HEAD 2>/dev/null || echo 'local')"
TAG_LATEST="${IMAGE_BASE}:latest-uat"

echo "============================================"
echo "Building: ${TAG_VERSION}"
echo "Context:  ${BUILD_CONTEXT}"
echo "============================================"

docker build \
  --label "org.opencontainers.image.version=${VERSION}" \
  --label "org.opencontainers.image.created=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -t "${TAG_VERSION}" \
  -t "${TAG_SHA}" \
  -t "${TAG_LATEST}" \
  "${BUILD_CONTEXT}"

echo "==> Scanning image for vulnerabilities..."
if command -v trivy &>/dev/null; then
  trivy image --severity HIGH,CRITICAL --exit-code 1 "${TAG_VERSION}"
else
  echo "trivy not found, skipping vulnerability scan"
fi

echo "==> Pushing images..."
docker push "${TAG_VERSION}"
docker push "${TAG_SHA}"
docker push "${TAG_LATEST}"

echo "==> Done: ${TAG_VERSION}"
