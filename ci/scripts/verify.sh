#!/usr/bin/env bash
set -euo pipefail

# Verification Agent script (AGENTS.md section 6.2)
# Runs automated checks against a deployed integrator on UAT.
#
# Usage: ./verify.sh <system> [namespace] [max_iterations]
#
# Example:
#   ./verify.sh allegro
#   ./verify.sh dhl oip 5

SYSTEM="${1:?Usage: verify.sh <system> [namespace] [max_iterations]}"
NAMESPACE="${2:-oip}"
MAX_ITERATIONS="${3:-5}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ITERATION=0
ALL_PASSED=false

echo "============================================"
echo "Verification Agent: ${SYSTEM}"
echo "Namespace:          ${NAMESPACE}"
echo "Max iterations:     ${MAX_ITERATIONS}"
echo "============================================"

run_checks() {
  ITERATION=$((ITERATION + 1))
  echo ""
  echo "==> Iteration ${ITERATION}/${MAX_ITERATIONS}"

  RESULTS="[]"
  OVERALL_STATUS="PASS"

  echo "--- Check: health_endpoint ---"
  HEALTH_START=$(date +%s%N)
  HEALTH_STATUS=$(kubectl exec -n "$NAMESPACE" deploy/"${SYSTEM}-integrator" -- \
    python -c "import httpx; r=httpx.get('http://localhost:8000/health'); print(r.status_code)" 2>/dev/null || echo "0")
  HEALTH_END=$(date +%s%N)
  HEALTH_MS=$(( (HEALTH_END - HEALTH_START) / 1000000 ))

  if [ "$HEALTH_STATUS" = "200" ]; then
    echo "  PASS (${HEALTH_MS}ms)"
  else
    echo "  FAIL (status=$HEALTH_STATUS)"
    OVERALL_STATUS="FAIL"
  fi

  echo "--- Check: docs_endpoint ---"
  DOCS_STATUS=$(kubectl exec -n "$NAMESPACE" deploy/"${SYSTEM}-integrator" -- \
    python -c "import httpx; r=httpx.get('http://localhost:8000/docs'); print(r.status_code)" 2>/dev/null || echo "0")
  if [ "$DOCS_STATUS" = "200" ]; then
    echo "  PASS"
  else
    echo "  FAIL (status=$DOCS_STATUS)"
    OVERALL_STATUS="FAIL"
  fi

  echo "--- Check: metrics_endpoint ---"
  METRICS_STATUS=$(kubectl exec -n "$NAMESPACE" deploy/"${SYSTEM}-integrator" -- \
    python -c "import httpx; r=httpx.get('http://localhost:8000/metrics'); print(r.status_code)" 2>/dev/null || echo "0")
  if [ "$METRICS_STATUS" = "200" ]; then
    echo "  PASS"
  else
    echo "  FAIL (status=$METRICS_STATUS)"
    OVERALL_STATUS="FAIL"
  fi

  echo "--- Check: pod_resources ---"
  POD_READY=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=${SYSTEM}-integrator" -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "Unknown")
  if [ "$POD_READY" = "True" ]; then
    echo "  PASS (pod ready)"
  else
    echo "  FAIL (pod not ready: $POD_READY)"
    OVERALL_STATUS="FAIL"
  fi

  echo ""
  echo "--- Verification Report ---"
  cat <<REPORT
{
  "integrator": "${SYSTEM}",
  "timestamp": "${TIMESTAMP}",
  "status": "${OVERALL_STATUS}",
  "iteration": ${ITERATION},
  "max_iterations": ${MAX_ITERATIONS},
  "checks": [
    {"name": "health_endpoint", "status": "$([ "$HEALTH_STATUS" = "200" ] && echo "PASS" || echo "FAIL")", "response_time_ms": ${HEALTH_MS}},
    {"name": "docs_endpoint", "status": "$([ "$DOCS_STATUS" = "200" ] && echo "PASS" || echo "FAIL")"},
    {"name": "metrics_endpoint", "status": "$([ "$METRICS_STATUS" = "200" ] && echo "PASS" || echo "FAIL")"},
    {"name": "pod_resources", "status": "$([ "$POD_READY" = "True" ] && echo "PASS" || echo "FAIL")"}
  ]
}
REPORT

  if [ "$OVERALL_STATUS" = "PASS" ]; then
    ALL_PASSED=true
    return 0
  fi
  return 1
}

while [ "$ITERATION" -lt "$MAX_ITERATIONS" ]; do
  if run_checks; then
    echo ""
    echo "==> All verification checks PASSED for ${SYSTEM}!"
    exit 0
  fi

  if [ "$ITERATION" -lt "$MAX_ITERATIONS" ]; then
    echo ""
    echo "==> Checks failed. Waiting 30s before retry..."
    sleep 30
  fi
done

echo ""
echo "==> FAILED: Verification did not pass after ${MAX_ITERATIONS} iterations."
echo "==> Manual investigation required. Check logs:"
echo "    kubectl logs -n ${NAMESPACE} deploy/${SYSTEM}-integrator --tail=100"
exit 1
