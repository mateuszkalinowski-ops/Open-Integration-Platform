#!/usr/bin/env bash
set -euo pipefail

# Deploy an integrator to Kubernetes using Kustomize.
#
# Usage: ./deploy.sh <kustomize_path> [namespace]
#
# Examples:
#   ./deploy.sh ecommerce/allegro-v1
#   ./deploy.sh courier/dhl-v1
#   ./deploy.sh ../overlays/uat                    # Full platform
#
# Env vars:
#   KUBECONFIG   - path to kubeconfig
#   NAMESPACE    - target namespace (default: oip)

KUSTOMIZE_PATH="${1:?Usage: deploy.sh <kustomize_path> [namespace]}"
NAMESPACE="${2:-${NAMESPACE:-oip}}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

FULL_PATH="${PROJECT_ROOT}/k8s/integrators/${KUSTOMIZE_PATH}"
if [ ! -d "$FULL_PATH" ]; then
  FULL_PATH="${PROJECT_ROOT}/k8s/${KUSTOMIZE_PATH}"
fi

if [ ! -f "${FULL_PATH}/kustomization.yaml" ]; then
  echo "ERROR: kustomization.yaml not found at ${FULL_PATH}"
  exit 1
fi

echo "============================================"
echo "Deploying: ${KUSTOMIZE_PATH}"
echo "Namespace: ${NAMESPACE}"
echo "Path:      ${FULL_PATH}"
echo "============================================"

echo "==> Validating manifests..."
kubectl kustomize "${FULL_PATH}" > /dev/null

echo "==> Applying manifests..."
kubectl kustomize "${FULL_PATH}" | kubectl apply -f -

echo "==> Checking deployment status..."
DEPLOYMENTS=$(kubectl get deployments -n "${NAMESPACE}" -l "app.kubernetes.io/part-of=pinquark" -o name 2>/dev/null || true)

if [ -z "$DEPLOYMENTS" ]; then
  echo "No deployments found in namespace ${NAMESPACE}"
  exit 0
fi

FAILED=0
for dep in $DEPLOYMENTS; do
  echo "Waiting for ${dep}..."
  if ! kubectl rollout status "${dep}" -n "${NAMESPACE}" --timeout=120s; then
    echo "WARNING: ${dep} did not become ready within timeout"
    kubectl describe "${dep}" -n "${NAMESPACE}" | tail -20
    FAILED=$((FAILED + 1))
  fi
done

if [ "$FAILED" -gt 0 ]; then
  echo "WARNING: ${FAILED} deployment(s) did not become ready"
  exit 1
fi

echo "==> Deployment successful!"
echo ""
echo "Deployed resources:"
kubectl get pods -n "${NAMESPACE}" -l "app.kubernetes.io/part-of=pinquark" --no-headers
